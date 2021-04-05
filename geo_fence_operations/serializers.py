from rest_framework import serializers

from .models import GeoFence

class GeoFenceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = GeoFence
        fields = '__all__'
   
   
     