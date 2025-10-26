from rest_framework import serializers
from .models import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'

        read_only_fields=['id', 'exchange_rate', 'estimated_gdp', 'last_refreshed_at']

      
    def validate(self, data):
        errors={}
        if not data.get('name'):
            errors['name']='This field is required.'
        if data.get('population') is None:
            errors['population']='This field is required.'
        if self.instance is None and not data.get("currency.code"):
            errors['currency_code']='This field is required for new entries.'
        if errors:
            raise serializers.ValidationError({"error":"Validation failed", "details":errors})
        return data