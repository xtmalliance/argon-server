from flight_declaration_operations.models import FlightAuthorization, FlightDeclaration
from typing import Tuple
from datetime import datetime
from uuid import uuid4
import arrow

class BlenderDatabaseReader():
    """
    A class to unify read and write operations to the database. Eventually caching etc. can be added via this file
    """

    def get_flight_declaration_by_id(self, flight_declaration_id:str) ->Tuple[None, FlightDeclaration]:        
        try:
            flight_declaration = FlightDeclaration.objects.get(id = flight_declaration_id)
            return flight_declaration
        except FlightDeclaration.DoesNotExist: 
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

    def get_relevant_flight_declaration_ids(self, now:str ) ->Tuple[None, uuid4]:  
        n = arrow.get(now)
        two_minutes_before_now = n.shift(seconds = -120).isoformat()
        two_minutes_after_now = n.shift(seconds = 120).isoformat()          
        relevant_ids =  FlightDeclaration.objects.filter(start_datetime__lte = two_minutes_before_now, end_datetime__gte = two_minutes_after_now).values_list('id', flat=True)        
        return relevant_ids

