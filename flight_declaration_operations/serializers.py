"""
This module holds the Serialization classes to be used in Flight Declaration operations.
"""
import json
from rest_framework import serializers
from .models import FlightDeclaration
from .utils import OperationalIntentsConverter


class FlightDeclarationRequestSerializer(serializers.Serializer):
    """
    Deserializes the JSON received payload for validation purposes.
    """
    originating_party=serializers.CharField()
    start_datetime=serializers.DateTimeField()
    end_datetime=serializers.DateTimeField()
    type_of_operation=serializers.IntegerField()
    flight_declaration_geo_json=serializers.DictField()

class FlightDeclarationSerializer(serializers.ModelSerializer):
    """
    Serializer class for the model: FlightDeclaration
    """
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
        fields = ('operational_intent','originating_party', 'type_of_operation','id','state','is_approved','start_datetime','end_datetime','flight_declaration_geojson','flight_declaration_raw_geojson','approved_by','submitted_by',)
     
class FlightDeclarationApprovalSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightDeclaration
        fields = ('is_approved','approved_by',)
     
class FlightDeclarationStateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FlightDeclaration
        fields = ('state','submitted_by',)
     