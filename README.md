          Country Currency & Exchange API

A RESTful API built with Django + MySQL, that fetches and caches real-time country data, currency codes, and exchange rates.
It also computes estimated GDP for each country, provides CRUD operations, and generates a summary image.

    Features

Fetch and store country data with currency details

Fetch real-time exchange rates from an external API

Compute estimated GDP using:
  estimated_gdp = population × random(1000–2000) ÷ exchange_rate
Cache results in a MySQL database
CRUD operations for countries
Image generation with top 5 GDP countries summary
Custom error handling and validation
Deployed on Railway

Tech Stack 

Component	                      Technology
Backend	                          Django REST Framework
Database	                         MySQL
Deployment                        Railway
Image Generation                 	Pillow

Installation & Setup

Clone Repository
  git clone https://github.com/Zeehy123/CountryCdE_api.git
  cd CountryCdE_api
Create Virtual Environment
Install Dependencies
  pip install -r requirements.txt
Database migrations
    python manage.py makemigrations
    python manage.py migrate


API Endpoints
| Method     | Endpoint             | Description                                                  |
| ---------- | -------------------- | ------------------------------------------------------------ |
| **POST**   | `/countries/refresh` | Fetch all countries and exchange rates, cache them in the DB |
| **GET**    | `/countries`         | Get all countries (with filters and sorting)                 |
| **GET**    | `/countries/:name`   | Get a single country by name                                 |
| **DELETE** | `/countries/:name`   | Delete a country                                             |
| **GET**    | `/status`            | Show total countries and last refresh timestamp              |
| **GET**    | `/countries/image`   | Serve the summary image                                      |


Filtering and Sorting Examples

| Example                    | Description                                  |
| -------------------------- | -------------------------------------------- |
| `/countries?region=Africa` | Filter countries by region                   |
| `/countries?currency=NGN`  | Filter by currency code                      |
| `/countries?sort=gdp_desc` | Sort countries by estimated GDP (descending) |


Example Response
GET /countries?region=Africa
    [
  {
    "id": 1,
    "name": "Nigeria",
    "capital": "Abuja",
    "region": "Africa",
    "population": 206139589,
    "currency_code": "NGN",
    "exchange_rate": 1600.23,
    "estimated_gdp": 25767448125.2,
    "flag_url": "https://flagcdn.com/ng.svg",
    "last_refreshed_at": "2025-10-22T18:00:00Z"
  }
]


Error Responses
| Status  | Example                                                                                              |
| ------- | ---------------------------------------------------------------------------------------------------- |
| **400** | `{ "error": "Validation failed", "details": {"currency_code": "is required"} }`                      |
| **404** | `{ "error": "Country not found" }`                                                                   |
| **500** | `{ "error": "Internal server error" }`                                                               |
| **503** | `{ "error": "External data source unavailable", "details": "Could not fetch data from [API name]" }` |
