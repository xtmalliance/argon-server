from rest_framework import serializers
from .models import SignedTelmetryPublicKey
from rid_operations import data_definitions as rid_dd
class SignedTelmetryPublicKeySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SignedTelmetryPublicKey        
        fields = ('key_id','url', 'is_active',)
   
class TimestampSerializer(serializers.Serializer):
    value = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%fZ")
    format = serializers.CharField(required=False,default = 'RFC3339')

class PositionSerializer(serializers.Serializer):
    lat = serializers.FloatField(required=False,default=0.0)
    lng = serializers.FloatField(required=False,default=0.0)
    alt = serializers.FloatField(required=False,default=0.0)
    accuracy_h = serializers.ChoiceField(choices=[(choice.value, choice.name) for choice in rid_dd.HorizontalAccuracy])
    accuracy_v = serializers.ChoiceField(choices=[(choice.value, choice.name) for choice in rid_dd.VerticalAccuracy])
    extrapolated = serializers.BooleanField(required=False,default=False)
    pressure_altitude = serializers.FloatField(required=False,default=0.0)

class HeightSerializer(serializers.Serializer):
    distance = serializers.FloatField()
    reference = serializers.CharField()

class CurrentStateSerializer(serializers.Serializer):
    timestamp = TimestampSerializer()
    timestamp_accuracy = serializers.FloatField()
    operational_status = serializers.ChoiceField(choices=[(choice.value, choice.name) for choice in rid_dd.RIDOperationalStatus])
    position = PositionSerializer()
    track = serializers.FloatField()
    speed = serializers.FloatField()
    speed_accuracy = serializers.ChoiceField(choices=[(choice.value, choice.name) for choice in rid_dd.SpeedAccuracy])
    vertical_speed = serializers.FloatField()
    height = HeightSerializer()
    group_radius = serializers.FloatField(required=False)
    group_ceiling = serializers.FloatField(required=False)
    group_floor = serializers.FloatField(required=False)
    group_count = serializers.IntegerField(required=False)
    group_time_start = serializers.DateTimeField(required=False,format="%Y-%m-%dT%H:%M:%S.%fZ")
    group_time_end = serializers.DateTimeField(required=False,format="%Y-%m-%dT%H:%M:%S.%fZ")

class RidDetailsSerializer(serializers.Serializer):
    id = serializers.CharField()
    operator_id = serializers.CharField()
    operation_description = serializers.CharField()

class EuClassificationSerializer(serializers.Serializer):
    category = serializers.CharField(required=False,default='EUCategoryUndefined')
    class_ = serializers.CharField(required=False,default='EUClassUndefined')

class UasIdSerializer(serializers.Serializer):
    serial_number = serializers.CharField(required=False,default="")
    registration_id = serializers.CharField(required=False,default="")
    utm_id = serializers.CharField(required=False,default="")
    specific_session_id = serializers.CharField(required=False,default=None)

class OperatorLocationSerializer(serializers.Serializer):
    position = PositionSerializer()
    altitude = serializers.FloatField()
    altitude_type = serializers.CharField()

class AuthDataSerializer(serializers.Serializer):
    format = serializers.CharField(required=False,default="")
    data = serializers.IntegerField(required=False,default=0)

class FlightDetailsSerializer(serializers.Serializer):
    rid_details = RidDetailsSerializer()
    eu_classification = EuClassificationSerializer()
    uas_id = UasIdSerializer()
    operator_location = OperatorLocationSerializer()
    auth_data = AuthDataSerializer()
    serial_number = serializers.CharField()
    registration_number = serializers.CharField()

class ObservationSerializer(serializers.Serializer):
    current_states = CurrentStateSerializer(many=True)
    flight_details = FlightDetailsSerializer()

class TelemetryRequestSerializer(serializers.Serializer):
    observations = ObservationSerializer(many=True,        error_messages={
            "required": "A flight observation array with current states and flight details is necessary"
        })

    def create(self, validated_data):
        return TelemetryRequest(**validated_data)



class TelemetryRequest:
    """
    Class object that will be used to contain deserialized JSON payload from the POST request.
    """

    def __init__(
        self,
        observations,
    ):
        self.observations = observations
