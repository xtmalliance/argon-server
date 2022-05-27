from rest_framework import serializers

from .models import FlightOperation

class FlightOperationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightOperation
        fields = ('gutma_flight_declaration', 'id','is_approved','state','type_of_operation','start_datetime','end_datetime',)
     
class FlightOperationApprovalSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightOperation
        fields = ('is_approved','approved_by',)
     
class FlightOperationStateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightOperation
        fields = ('state','submitted_by',)
     