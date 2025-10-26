import requests, random, os
from datetime import datetime, timezone
from django.db import transaction
from django.conf import settings
from .models import Country
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

RESTCOUNTRIES_URL = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_URL = "https://open.er-api.com/v6/latest/USD"

class ExternalAPIError(Exception):
    pass

def fetch_countries():
    r = requests.get(RESTCOUNTRIES_URL, timeout=15)
    if r.status_code != 200:
        raise ExternalAPIError("Could not fetch data from Countries API")
    return r.json()

def fetch_exchange_rates():
    r = requests.get(EXCHANGE_URL, timeout=15)
    if r.status_code != 200:
        raise ExternalAPIError("Could not fetch data from Exchange Rates API")
    data = r.json()
    # expected structure: { "result": "success", "rates": { "NGN": 1600.23, ... } }
    rates = data.get("rates") or {}
    return rates

def generate_estimated_gdp(population, exchange_rate):
    if exchange_rate in (None, 0):
        return None
    multiplier = random.randint(1000, 2000)
    return (population * multiplier) / exchange_rate

def build_country_record(country_raw, rates):
    # country_raw expected fields: name, capital, region, population, flag, currencies
    name = country_raw.get("name")
    capital = country_raw.get("capital")
    region = country_raw.get("region")
    population = country_raw.get("population") or 0
    flag = country_raw.get("flag")
    currencies = country_raw.get("currencies") or []

    if currencies:
        # take first currency code
        currency_code = currencies[0].get("code") if currencies[0].get("code") else None
    else:
        currency_code = None

    if currency_code:
        exchange_rate = rates.get(currency_code)
        if exchange_rate is None:
            exchange_rate = None
            estimated_gdp = None
        else:
            estimated_gdp = generate_estimated_gdp(population, exchange_rate)
    else:
        exchange_rate = None
        estimated_gdp = 0  # per spec if currencies array empty -> estimated_gdp = 0

    return {
        "name": name,
        "capital": capital,
        "region": region,
        "population": population,
        "currency_code": currency_code,
        "exchange_rate": exchange_rate,
        "estimated_gdp": estimated_gdp,
        "flag_url": flag,
    }

def generate_summary_image(total_count, top5, last_refreshed_at, output_path):
    # Simple image: white background, text lines
    width, height = 1200, 800
    img = Image.new("RGB", (width, height), color=(255,255,255))
    draw = ImageDraw.Draw(img)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, 28)
        title_font = ImageFont.truetype(font_path, 40)
    except Exception:
        font = ImageFont.load_default()
        title_font = font

    y = 40
    draw.text((40, y), "Countries Summary", font=title_font, fill=(0,0,0))
    y += 80
    draw.text((40, y), f"Total countries: {total_count}", font=font, fill=(0,0,0))
    y += 40
    draw.text((40, y), f"Last refreshed at (UTC): {last_refreshed_at.isoformat()}", font=font, fill=(0,0,0))
    y += 60
    draw.text((40, y), "Top 5 countries by estimated GDP:", font=font, fill=(0,0,0))
    y += 40

    for i, c in enumerate(top5, start=1):
        name = c.name
        gdp = c.estimated_gdp or 0
        draw.text((60, y), f"{i}. {name} — estimated_gdp: {gdp:,.2f}", font=font, fill=(0,0,0))
        y += 30

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, format="PNG")

def refresh_all_countries():
    """
    Fetch from external APIs and update DB.
    Returns: dict with total_countries and last_refreshed_at
    Raises ExternalAPIError on failure
    """
    countries_raw = fetch_countries()
    rates = fetch_exchange_rates()

    
    with transaction.atomic():
        last_refreshed_at = datetime.now(timezone.utc)
        updated_count = 0
        for cr in countries_raw:
            rec = build_country_record(cr, rates)
            # Case-insensitive match by name
            existing = Country.objects.filter(name__iexact=rec["name"]).first()
            if existing:
                # update
                existing.capital = rec["capital"]
                existing.region = rec["region"]
                existing.population = rec["population"]
                existing.currency_code = rec["currency_code"]
                existing.exchange_rate = rec["exchange_rate"]
                existing.estimated_gdp = rec["estimated_gdp"]
                existing.flag_url = rec["flag_url"]
                existing.last_refreshed_at = last_refreshed_at
                existing.save()
            else:
                Country.objects.create(
                    name=rec["name"],
                    capital=rec["capital"],
                    region=rec["region"],
                    population=rec["population"],
                    currency_code=rec["currency_code"],
                    exchange_rate=rec["exchange_rate"],
                    estimated_gdp=rec["estimated_gdp"],
                    flag_url=rec["flag_url"],
                    last_refreshed_at=last_refreshed_at
                )
            updated_count += 1

        # generate summary image
        top5 = Country.objects.order_by("-estimated_gdp")[:5]
        output_path = os.path.join(settings.MEDIA_ROOT, "summary.png")
        generate_summary_image(updated_count, top5, last_refreshed_at, output_path)
        # Return global info
        return {"total_countries": updated_count, "last_refreshed_at": last_refreshed_at}
