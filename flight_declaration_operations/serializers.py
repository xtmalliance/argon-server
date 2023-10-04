"""
This module holds the Serialization classes to be used in Flight Declaration operations.
"""
import json

from rest_framework import serializers

from .models import FlightDeclaration
from .utils import OperationalIntentsConverter


class FlightDeclarationRequest:
    """
    Class object that will be used to contain deserialized JSON payload from the POST request.
    """

    def __init__(
        self,
        originating_party,
        start_datetime,
        end_datetime,
        type_of_operation,
        vehicle_id,
        submitted_by,
        flight_declaration_geo_json,
    ):
        self.originating_party = originating_party
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.type_of_operation = type_of_operation
        self.vehicle_id = vehicle_id
        self.submitted_by = submitted_by
        self.flight_declaration_geo_json = flight_declaration_geo_json


class FlightDeclarationRequestSerializer(serializers.Serializer):
    """
    Deserialize the JSON received payload for validation purposes.
    """

    originating_party = serializers.CharField(
        required=False, default="No Flight Information"
    )
    start_datetime = serializers.DateTimeField(required=False, default=None)
    end_datetime = serializers.DateTimeField(required=False,default=None)
    type_of_operation = serializers.IntegerField(required=False, default=0)
    vehicle_id = serializers.CharField(required=False, default="000")
    submitted_by = serializers.CharField(required=False, default=None)
    flight_declaration_geo_json = serializers.DictField(
        error_messages={
            "required": "A valid flight declaration as specified by the A flight declaration protocol must be submitted."
        }
    )

    def create(self, validated_data):
        return FlightDeclarationRequest(**validated_data)


class FlightDeclarationSerializer(serializers.ModelSerializer):
    """
    Serializer class for the model: FlightDeclaration
    """

    operational_intent = serializers.SerializerMethodField()
    flight_declaration_geojson = serializers.SerializerMethodField()
    flight_declaration_raw_geojson = serializers.SerializerMethodField()

    def get_flight_declaration_geojson(self, obj):
        o = obj.operational_intent

        my_operational_intent_converter = OperationalIntentsConverter()
        my_operational_intent_converter.convert_operational_intent_to_geo_json(
            volumes=o["volumes"]
        )

        return my_operational_intent_converter.geo_json

    def get_flight_declaration_raw_geojson(self, obj):
        return json.loads(obj.flight_declaration_raw_geojson)

    def get_operational_intent(self, obj):
        return obj.operational_intent

    class Meta:
        model = FlightDeclaration
        fields = (
            "operational_intent",
            "originating_party",
            "type_of_operation",
            "aircraft_id",
            "id",
            "state",
            "is_approved",
            "start_datetime",
            "end_datetime",
            "flight_declaration_geojson",
            "flight_declaration_raw_geojson",
            "approved_by",
            "submitted_by",
        )


class FlightDeclarationApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightDeclaration
        fields = (
            "is_approved",
            "approved_by",
        )


class FlightDeclarationStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightDeclaration
        fields = (
            "state",
            "submitted_by",
        )
