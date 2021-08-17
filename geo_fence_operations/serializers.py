from rest_framework import serializers

from .models import GeoFence

class GeoFenceSerializer(serializers.ModelSerializer):
    altitude_ref = serializers.SerializerMethodField()
    
    class Meta:
        model = GeoFence
        fields = '__all__'
   
   
    def get_altitude_ref(self,obj):
        return obj.get_altitude_ref_display()
     