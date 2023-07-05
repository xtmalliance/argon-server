## This file checks the conformance of a operation per the AMC stated in the EU Conformance monitoring service 
import logging
import arrow
import json
from typing import List
from shapely.geometry import Point
from shapely.geometry import Polygon as Plgn
from dotenv import load_dotenv, find_dotenv
from common.database_operations import BlenderDatabaseReader
from .operator_conformance_notifications import OperationConformanceNotification
from scd_operations.scd_data_definitions import LatLngPoint, Polygon, Volume4D
from conformance_monitoring_operations.data_definitions import PolygonAltitude

from .data_helper import cast_to_volume4d
logger = logging.getLogger('django')
load_dotenv(find_dotenv())



class StatusCode:

    @classmethod
    def list(cls):
        """Return the StatusCode options as a list of mapped key / value items."""
        return list(cls.dict().values())

    @classmethod
    def text(cls, key):
        """Text for supplied status code."""
        return cls.options.get(key, None)

    @classmethod
    def items(cls):
        """All status code items."""
        return cls.options.items()

    @classmethod
    def keys(cls):
        """All status code keys."""
        return cls.options.keys()

    @classmethod
    def labels(cls):
        
        return cls.options.values()

    @classmethod
    def names(cls):
        """Return a map of all 'names' of status codes in this class

        Will return a dict object, with the attribute name indexed to the integer value.

        e.g.
        {
            'PENDING': 10,
            'IN_PROGRESS': 20,
        }
        """
        keys = cls.keys()
        status_names = {}

        for d in dir(cls):
            if d.startswith('_'):
                continue
            if d != d.upper():
                continue

            value = getattr(cls, d, None)

            if value is None:
                continue
            if callable(value):
                continue
            if type(value) != int:
                continue
            if value not in keys:
                continue

            status_names[d] = value

        return status_names

    @classmethod
    def dict(cls):
        """Return a dict representation containing all required information"""
        values = {}

        for name, value, in cls.names().items():
            entry = {
                'key': value,
                'name': name,
                'label': cls.label(value),
            }

            if hasattr(cls, 'colors'):
                if color := cls.colors.get(value, None):
                    entry['color'] = color

            values[name] = entry

        return values

    @classmethod
    def label(cls, value):
        """Return the status code label associated with the provided value."""
        return cls.options.get(value, value)

    @classmethod
    def value(cls, label):
        """Return the value associated with the provided label."""
        for k in cls.options.keys():
            if cls.options[k].lower() == label.lower():
                return k

        raise ValueError("Label not found")



class ConformanceChecksList(StatusCode):
    ''' A list of conformance checks and their status'''
    # 1 is reserved for True / check 
    C2 = 2
    C3 = 3
    C4 = 4
    C5 = 5
    C6 = 6
    C7 = 7
    C8 = 8
    C9 = 9
    C10 = 10
    C11 = 11

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    # Source: https://stackoverflow.com/questions/10048249/how-do-i-determine-if-current-time-is-within-a-specified-range-using-pythons-da
    check_time = check_time or arrow.now()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time


class BlenderConformanceOps():    
    
    def is_operation_conformant_via_telemetry(self, flight_declaration_id:str, aircraft_id:str, telemetry_location: LatLngPoint,altitude_m_wgs_84:float) -> bool:
        """ This method performs the conformance sequence per AMC1 Article 13(1) as specified in the EU AMC / GM on U-Space regulation. 
        This method is called every time a telemetry has been sent into Flight Blender. Specifically, it checks this once a telemetry has been sent: 
         - C2 Check if flight authorization is granted
         - C3 Match telmetry from aircraft with the flight authorization
         - C4 Determine whether the aircraft is subject to an accepted and activated flight authorization
         - C5 Check if flight operation is activated 
         - C6 Check if telemetry is within start / end time of the operation            
         - C7 (A)(B) Check if the aircraft complies with deviation thresholds / 4D volume
         - C8 Check if it is near a GeoFence and / breaches one

        """
        my_database_reader = BlenderDatabaseReader()
        now = arrow.now()        

        flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id= flight_declaration_id)        
        flight_authorization = my_database_reader.get_flight_authorization_by_flight_declaration(flight_declaration_id=flight_declaration_id)
        # C2 Check 
        try: 
            assert flight_authorization is not None
            assert flight_declaration is not None
        except AssertionError as ae:             
            logging.error("Error in getting flight authorization and declaration for {flight_declaration_id}, cannot continue with conformance checks, C2 Check failed.".format(flight_declaration_id = flight_declaration_id))
            return ConformanceChecksList.C2
        
        # Flight Operation and Flight Authorization exists, create a notifications helper
        my_operation_notification = OperationConformanceNotification(flight_declaration_id=flight_declaration_id)        
        operation_start_time = arrow.get(flight_declaration.start_datetime)
        operation_end_time = arrow.get(flight_declaration.end_datetime)

        # C3 check         
        try: 
            assert flight_declaration.aircraft_id == aircraft_id
        except AssertionError as ae: 
            invalid_aircraft_id_msg = "The aircraft ID provided in telemetry for operation {flight_declaration_id}, does not match the declared / authorized aircraft, you must stop operation. C4 Check failed.".format(flight_declaration_id = flight_declaration_id)
            logging.error(invalid_aircraft_id_msg)
            my_operation_notification.send_conformance_status_notification(message = invalid_aircraft_id_msg, level='error')
            return ConformanceChecksList.C3        
        
        # C4, C5 check 
        try: 
            assert flight_declaration.state in [1,2]
        except AssertionError as ae: 
            flight_state_not_correct_msg = "The Operation state for operation {flight_declaration_id}, is not one of 'Accepted' or 'Activated', your authorization is invalid. C4+C5 Check failed.".format(flight_declaration_id = flight_declaration_id)
            logging.error(flight_state_not_correct_msg)
            my_operation_notification.send_conformance_status_notification(message = flight_state_not_correct_msg, level='error')
            
            return ConformanceChecksList.C5

        # C6 check
        try: 
            assert is_time_between(begin_time= operation_start_time, end_time= operation_end_time, check_time= now)
        except AssertionError as ae:
            telemetry_timestamp_not_within_op_start_end_msg = "The telemetry timestamp provided for operation {flight_declaration_id}, is not within the start / end time for an operation. C6 Check failed.".format(flight_declaration_id = flight_declaration_id)
            logging.error(telemetry_timestamp_not_within_op_start_end_msg)
            my_operation_notification.send_conformance_status_notification(message = telemetry_timestamp_not_within_op_start_end_msg, level='error')
            return ConformanceChecksList.C6  
        
        # C7 check : Check if the aircraft is within the 4D volume 

        # Construct the boundary of the current operation by getting the operational intent
               
        # TODO: Cache this so that it need not be done everytime
        operational_intent = json.loads(flight_declaration.operational_intent)

        all_volumes = operational_intent['volumes']
        # The provided telemetry location cast as a Shapely Point
        lng = float(telemetry_location.lng)
        lat = float(telemetry_location.lat)
        rid_location = Point(lng,lat)                
        all_polygon_altitudes: List[PolygonAltitude] = []

        for v in all_volumes:
            v4d = cast_to_volume4d(v)
            altitude_lower = v4d.volume.altitude_lower.value
            altitude_upper = v4d.volume.altitude_upper.value
            outline_polygon = v4d.volume.outline_polygon            
            point_list = []            
            for vertex in outline_polygon.vertices:
                p = Point(vertex.lng, vertex.lat)
                point_list.append(p)
            outline_polygon = Plgn([[p.x, p.y] for p in point_list])
            
            
            pa = PolygonAltitude(polygon = outline_polygon, altitude_upper = altitude_upper, altitude_lower = altitude_lower)
            all_polygon_altitudes.append(pa)        

        rid_obs_within_all_volumes = []
        rid_obs_within_altitudes = []
        for p in all_polygon_altitudes:      
            is_within = rid_location.within(p.polygon)
            # If the aircraft RID is within the the polygon, check the altitude
            altitude_conformant = True if altitude_lower <= altitude_m_wgs_84 <= altitude_upper else False            
            
            rid_obs_within_all_volumes.append(is_within)
            rid_obs_within_altitudes.append(altitude_conformant)
                
        aircraft_bounds_conformant = any(rid_obs_within_all_volumes) 
        aircraft_altitude_conformant = any(rid_obs_within_altitudes) 
        
        try: 
            assert aircraft_altitude_conformant
        except AssertionError as ae:             
            aircraft_altitude_nonconformant_msg = "The telemetry timestamp provided for operation {flight_declaration_id}, is not within the altitude bounds C7a check failed.".format(flight_declaration_id = flight_declaration_id)            
            logging.error(aircraft_altitude_nonconformant_msg)
            my_operation_notification.send_conformance_status_notification(message = aircraft_altitude_nonconformant_msg, level='error')
            return ConformanceChecksList.C7  

        try: 
            assert aircraft_bounds_conformant
        except AssertionError as ae:             
            aircraft_bounds_nonconformant_msg = "The telemetry location provided for operation {flight_declaration_id}, is not within the declared bounds for an operation. C7b check failed.".format(flight_declaration_id = flight_declaration_id)
            
            logging.error(aircraft_bounds_nonconformant_msg)
            my_operation_notification.send_conformance_status_notification(message = aircraft_bounds_nonconformant_msg, level='error')
            return ConformanceChecksList.C7  
        
        # C8 check Check if aircraft is not breaching any active Geofences

        return True

    def check_flight_authorization_conformance(self, flight_declaration_id: str) -> bool:  
        """ This method checks the conformance of a flight authorization independent of telemetry observations being sent:            
            C9 Check if telemetry is being sent
            C10 Check operation state that it not ended and the time limit of the flight authorization has passed
            C11 Check if a Flight authorization object exists
        """
        # Flight Operation and Flight Authorization exists, create a notifications helper
        my_operation_notification = OperationConformanceNotification(flight_declaration_id=flight_declaration_id)

        my_database_reader = BlenderDatabaseReader()
        now = arrow.now()        
        flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id= flight_declaration_id)        
        flight_authorization_exists = my_database_reader.get_flight_authorization_by_flight_declaration(flight_declaration_id=flight_declaration_id)
        # C11 Check
        if not flight_authorization_exists:
            authorization_not_granted_message = "There is no flight authorization for operation with ID {flight_declaration_id}. Check C11 Failed".format(flight_declaration_id = flight_declaration_id)
            logging.error(authorization_not_granted_message)
            my_operation_notification.send_conformance_status_notification(message = authorization_not_granted_message, level='error')                   
            # if flight state is accepted, then change it to ended and delete from dss
            return ConformanceChecksList.C10

        # The time the most recent telemetry was sent
        latest_telemetry_datetime = flight_declaration.latest_telemetry_datetime

        # Check the current time is within the start / end date time +/- 15 seconds TODO: trim this window as it is to broad
        fifteen_seconds_before_now = now.shift(seconds = -15)
        fifteen_seconds_after_now = now.shift(seconds = 15)
            
        # C10 state check     
        # allowed_states = ['Activated', 'Nonconforming', 'Contingent']
        allowed_states = [2,3,4]
        if flight_declaration.state not in allowed_states:
            flight_state_not_conformant = "The state for operation {flight_declaration_id}, has not been is not one of 'Activated', 'Nonconforming' or 'Contingent. Check C10 failed' ".format(flight_declaration_id = flight_declaration_id)            
            logging.error(flight_state_not_conformant)
            my_operation_notification.send_conformance_status_notification(message = flight_state_not_conformant, level='error')
            # set state as ended
            return ConformanceChecksList.C10
                           
        # C9 state check 

        # Operation is supposed to start check if telemetry is bieng submitted (within the last minute)
        if latest_telemetry_datetime: 
                        
            if not fifteen_seconds_before_now <= latest_telemetry_datetime <= fifteen_seconds_after_now:
                telemetry_not_being_received_error_msg = "The telemetry for operation {flight_declaration_id}, has not been received in the past 15 seconds. Check C9 Failed".format(flight_declaration_id = flight_declaration_id)
                
                logging.error(telemetry_not_being_received_error_msg)
                my_operation_notification.send_conformance_status_notification(message = telemetry_not_being_received_error_msg, level='error')

                # declare state as contingent and 

                return ConformanceChecksList.C9
        else: 
            telemetry_never_received_error_msg = "The telemetry for operation {flight_declaration_id}, has never been received. Check C9 Failed".format(flight_declaration_id = flight_declaration_id)            
            logging.error(telemetry_never_received_error_msg)
            my_operation_notification.send_conformance_status_notification(message = telemetry_never_received_error_msg, level='error')
            
            # declare state as contingent 
        
            return ConformanceChecksList.C9


        return True

    