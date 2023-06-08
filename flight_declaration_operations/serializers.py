from rest_framework import serializers
import json
from .models import FlightDeclaration
from .utils import OperationalIntentsConverter
from conformance_monitoring_operations.operation_state_helper import FlightOperationStateMachine, get_status

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

    def validate_state(self, value):
        if self.instance and value not in [2, 4, 5]:
            raise serializers.ValidationError("An operator can only set the state to Activated (2), Contingent (4) or Ended (5) using this end point")
                
        original_state  = self.instance.state
        if value == 5: 
            event = 'operator_confirms_ended'
        elif value == 2:
            event = 'operator_activates'
        elif value == 4:
            event = 'operator_confirms_contingent'

        my_operation_state_machine = FlightOperationStateMachine(state = original_state)
        original_state = my_operation_state_machine.state

        if original_state == 5:
            raise serializers.ValidationError("Cannot change state of an operation that has already set as ended")    

        my_operation_state_machine.on_event(event)        
        new_state = get_status(my_operation_state_machine.state)
        
        if original_state == new_state:
            raise serializers.ValidationError("State transition to {new_state} from current state of {current_state} is not allowed per the ASTM standards".format(new_state = new_state, current_state = original_state))
        
        return value
    
    def update(self, instance, validated_data):        
        fd = FlightDeclaration.objects.get(pk=instance.id)
        original_state  = fd.state
        fd_u = FlightDeclaration.objects.filter(pk=instance.id) \
                           .update(**validated_data)
        
        new_state = validated_data['state']

        fd.add_state_history_entry(original_state= original_state, new_state=new_state, notes="State changed by operator")
        
        return fd
    class Meta:
        model = FlightDeclaration
        fields = ('state','submitted_by',)
     