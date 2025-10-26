from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Country
from .serializers import CountrySerializer
from .tasks import refresh_all_countries, ExternalAPIError
from django.conf import settings
import os
from django_filters import rest_framework as filters

class CountryFilter(filters.FilterSet):
    region = filters.CharFilter(field_name="region", lookup_expr="iexact")
    currency = filters.CharFilter(field_name="currency_code", lookup_expr="iexact")

    class Meta:
        model = Country
        fields = ["region", "currency"]

class CountryListView(generics.ListAPIView):
    serializer_class = CountrySerializer
    queryset = Country.objects.all()
    filterset_class = CountryFilter

    def get_queryset(self):
        qs = super().get_queryset()
        sort = self.request.query_params.get("sort")
        if sort == "gdp_desc":
            qs = qs.order_by("-estimated_gdp")
        elif sort == "gdp_asc":
            qs = qs.order_by("estimated_gdp")
        return qs

class CountryDetailView(APIView):
    def get(self, request, name):
        country = Country.objects.filter(name__iexact=name).first()
        if not country:
            return Response({"error": "Country not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CountrySerializer(country)
        return Response(serializer.data)

    def delete(self, request, name):
        country = Country.objects.filter(name__iexact=name).first()
        if not country:
            return Response({"error": "Country not found"}, status=status.HTTP_404_NOT_FOUND)
        country.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RefreshCountriesView(APIView):
    def post(self, request):
        try:
            result = refresh_all_countries()
            # format datetime to ISO
            return Response({
                "message": "Refresh successful",
                "total_countries": result["total_countries"],
                "last_refreshed_at": result["last_refreshed_at"].isoformat()
            })
        except ExternalAPIError as e:
            return Response(
                {"error": "External data source unavailable", "details": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StatusView(APIView):
    def get(self, request):
        total = Country.objects.count()
        last = Country.objects.order_by("-last_refreshed_at").first()
        last_ts = last.last_refreshed_at.isoformat() if last else None
        return Response({"total_countries": total, "last_refreshed_at": last_ts})


class CountryImageView(APIView):
    def get(self, request):
        path = os.path.join(settings.MEDIA_ROOT, "summary.png")
        if not os.path.exists(path):
            return Response({"error": "Summary image not found"}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(path, "rb"), content_type="image/png")
