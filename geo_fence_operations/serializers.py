from rest_framework import serializers
import json
from .models import GeoFence

class GeoFenceSerializer(serializers.ModelSerializer):
    altitude_ref = serializers.SerializerMethodField()
    raw_geo_fence = serializers.SerializerMethodField()
    geozone = serializers.SerializerMethodField()
    
    def get_raw_geo_fence(self, obj):
        raw_geo_fence = json.loads(obj.raw_geo_fence)
        return raw_geo_fence
    def get_geozone(self, obj):
        if obj.geozone: 
            parsed_geo_zone = json.loads(obj.geozone)
        else: 
            parsed_geo_zone = {}
        return parsed_geo_zone
    
    class Meta:
        model = GeoFence
        fields = '__all__'
   
   
    def get_altitude_ref(self,obj):
        return obj.get_altitude_ref_display()
     