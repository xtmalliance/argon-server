from flight_declaration_operations.models import FlightAuthorization, FlightDeclaration
from typing import Tuple, List
from uuid import uuid4
import arrow
from django.db.utils import IntegrityError

class BlenderDatabaseReader():
    """
    A file to unify read and write operations to the database. Eventually caching etc. can be added via this file
    """

    def get_all_flight_declarations(self) ->Tuple[None, List[FlightDeclaration]]:        
        
        flight_declarations = FlightDeclaration.objects.all()
        return flight_declarations
        
    def get_flight_declaration_by_id(self, flight_declaration_id:str) ->Tuple[None, FlightDeclaration]:        
        try:
            flight_declaration = FlightDeclaration.objects.get(id = flight_declaration_id)
            return flight_declaration
        except FlightDeclaration.DoesNotExist: 
            return None

    def get_flight_authorization_by_flight_declaration_obj(self, flight_declaration:FlightDeclaration) ->Tuple[None, FlightAuthorization]:        
        try:
            flight_authorization = FlightAuthorization.objects.get(declaration = flight_declaration)
            return flight_authorization
        except FlightDeclaration.DoesNotExist: 
            return None
        except FlightAuthorization.DoesNotExist: 
            return None

    def get_flight_authorization_by_flight_declaration(self, flight_declaration_id:str) ->Tuple[None, FlightAuthorization]:        
        try:
            flight_declaration = FlightDeclaration.objects.get(id = flight_declaration_id)
            flight_authorization = FlightAuthorization.objects.get(declaration = flight_declaration)
            return flight_authorization
        except FlightDeclaration.DoesNotExist: 
            return None
        except FlightAuthorization.DoesNotExist: 
            return None

    def get_current_flight_declaration_ids(self, now:str ) ->Tuple[None, uuid4]:  
        ''' This method gets flight operation ids that are active in the system'''
        n = arrow.get(now)
        
        two_minutes_before_now = n.shift(seconds = -120).isoformat()
        five_hours_from_now = n.shift(minutes = 300).isoformat()    
        relevant_ids =  FlightDeclaration.objects.filter(start_datetime__gte = two_minutes_before_now, end_datetime__lte = five_hours_from_now).values_list('id', flat=True)        
        return relevant_ids
    
    def get_current_flight_accepted_activated_declaration_ids(self, now:str ) ->Tuple[None, uuid4]:  
        ''' This method gets flight operation ids that are active in the system'''
        n = arrow.get(now)
        
        two_minutes_before_now = n.shift(seconds = -120).isoformat()
        five_hours_from_now = n.shift(minutes = 300).isoformat()    
        relevant_ids =  FlightDeclaration.objects.filter(start_datetime__gte = two_minutes_before_now, end_datetime__lte = five_hours_from_now).filter(state__in = [1,2]).values_list('id', flat=True)        
        return relevant_ids


class BlenderDatabaseWriter():    

    def create_flight_authorization(self, flight_declaration_id:str) ->bool:    
        try:
            flight_declaration = FlightDeclaration.objects.get(id = flight_declaration_id)
            flight_authorization = FlightAuthorization(declaration = flight_declaration)
            flight_authorization.save()
            return True
        except FlightDeclaration.DoesNotExist: 
            return False
        except IntegrityError as ie:
            return False
        
        

    def update_telemetry_timestamp(self, flight_declaration_id:str) ->bool:        
        now = arrow.now().isoformat()
        try:
            flight_declaration = FlightDeclaration.objects.get(id = flight_declaration_id)
            flight_declaration.latest_telemetry_datetime = now
            flight_declaration.save()
            return True
        except FlightDeclaration.DoesNotExist: 
            return False
        
    def update_flight_authorization_op_int(self, flight_authorization:FlightAuthorization,dss_operational_intent_id) -> bool:
        try: 
            flight_authorization.dss_operational_intent_id = dss_operational_intent_id
            flight_authorization.save()
            return True
        except Exception as e: 
            return False
        
    def update_flight_operation_state(self,flight_declaration_id:str, state:int) -> bool:
        try: 
            flight_declaration = FlightDeclaration.objects.get(id = flight_declaration_id)
            flight_declaration.state = state
            flight_declaration.save()
            return True
        except Exception as e: 
            return False



