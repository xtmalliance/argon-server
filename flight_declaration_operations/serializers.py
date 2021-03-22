from rest_framework import serializers

from .models import FlightOperation

class FlightOperationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightOperation
        fields = ('gutma_flight_declaration', 'id','is_approved','start_datetime','end_datetime')
     