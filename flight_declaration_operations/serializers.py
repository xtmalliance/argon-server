from rest_framework import serializers
import json
from .models import FlightDeclaration
from .utils import OperationalIntentsConverter

class FlightDeclarationSerializer(serializers.ModelSerializer):
    operational_intent = serializers.SerializerMethodField() 
    flight_declaration_geojson = serializers.SerializerMethodField() 
    flight_declaration_raw_geojson = serializers.SerializerMethodField() 
    
    def get_flight_declaration_geojson(self, obj):
        o = json.loads(obj.operational_intent) 
        
        my_operational_intent_converter = OperationalIntentsConverter()
        my_operational_intent_converter.convert_operational_intent_to_geo_json(volumes = o['volumes'])
        
        return my_operational_intent_converter.geo_json   
   
    def get_flight_declaration_raw_geojson(self, obj):
        
        return json.loads(obj.flight_declaration_raw_geojson)

    def get_operational_intent(self, obj):
        return json.loads(obj.operational_intent) 
    class Meta:
        model = FlightDeclaration
        fields = ('operational_intent','originating_party', 'type_of_operation','id','state','is_approved','start_datetime','end_datetime','flight_declaration_geojson','flight_declaration_raw_geojson','approved_by','submitted_by','aircraft_id',)
     
class FlightDeclarationApprovalSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightDeclaration
        fields = ('is_approved','approved_by',)
     
class FlightDeclarationStateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightDeclaration
        fields = ('state','submitted_by',)
     