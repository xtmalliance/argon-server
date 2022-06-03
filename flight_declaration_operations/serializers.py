from rest_framework import serializers
import json
from .models import FlightOperation
from .utils import OperationalIntentsConverter

class FlightOperationSerializer(serializers.ModelSerializer):
    operational_intent = serializers.SerializerMethodField() 
    flight_declaration_geojson = serializers.SerializerMethodField() 
    
    def get_flight_declaration_geojson(self, obj):
        o = json.loads(obj.operational_intent) 
        my_operational_intent_converter = OperationalIntentsConverter()
        my_operational_intent_converter.convert_operational_intent_to_geo_json(extents = o['extents'])
        return my_operational_intent_converter .geo_json   
   

    def get_operational_intent(self, obj):
        return json.loads(obj.operational_intent) 
    class Meta:
        model = FlightOperation
        fields = ('operational_intent','originating_party', 'type_of_operation','id','is_approved','start_datetime','end_datetime','flight_declaration_geojson',)
     
class FlightOperationApprovalSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightOperation
        fields = ('is_approved','approved_by',)
     
class FlightOperationStateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightOperation
        fields = ('state','submitted_by',)
     