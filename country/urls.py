from django.urls import path
from .views import (
    CountryListView, CountryDetailView, RefreshCountriesView, StatusView, CountryImageView
)

urlpatterns = [
    path("countries/refresh", RefreshCountriesView.as_view(), name="countries-refresh"),
    path("countries/image", CountryImageView.as_view(), name="countries-image"),
    path("countries", CountryListView.as_view(), name="countries-list"),
    path("countries/<str:name>", CountryDetailView.as_view(), name="countries-detail"),
    path("status", StatusView.as_view(), name="status"),
]
