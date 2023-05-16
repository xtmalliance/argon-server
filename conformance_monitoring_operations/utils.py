## This file checks the conformance of a operation per the AMC stated in the EU Conformance monitoring service 
import logging
import arrow
from dotenv import load_dotenv, find_dotenv
from common.database_operations import BlenderDatabaseReader
from operator_conformance_notifications import OperationConformanceNotification
logger = logging.getLogger('django')
load_dotenv(find_dotenv())
 

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    # Source: https://stackoverflow.com/questions/10048249/how-do-i-determine-if-current-time-is-within-a-specified-range-using-pythons-da
    check_time = check_time or arrow.utcnow()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time


class BlenderConformanceOps():
        
    def is_operation_conformant_via_telemetry(self, flight_declaration_id:str, aircraft_id:str) -> bool:
        """ This method performs the conformance sequence per AMC1 Article 13(1) as specified in the EU AMC / GM on U-Space regulation. Specifically, it checks this once a telemetry has been sent: 
         - C1 Check if flight authorization is granted
         - C2 Match telmetry from aircraft with the flight authorization
         - C3 Determine whether the aircraft is subject to an accepted and activated flight authorization
         - C4 Check if flight operation is activated 
         - C5 Check if telemetry is within start / end time of the operation            
         - C6 Check if the aircraft complies with deviation thresholds / 4D volume
         - C7 Check if it is near a GeoFence and / breaches one

        """
        my_database_reader = BlenderDatabaseReader()
        now = arrow.now()        

        flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id= flight_declaration_id)
        
        flight_authorization = my_database_reader.get_flight_authorization_by_flight_declaration(flight_declaration_id=flight_declaration_id)
        # C1 Check 
        try: 
            assert flight_authorization is not None
            assert flight_declaration is not None
        except AssertionError as ae:             
            logging.error("Error in getting flight authorization and declaration for {flight_declaration_id}, cannot continue with conformance checks".format(flight_declaration_id = flight_declaration_id))
            return False
        
        # Flight Operation and Flight Authorization exists, create a notifications helper
        my_operation_notification = OperationConformanceNotification(flight_declaration_id=flight_declaration_id)        
        operation_start_time = flight_declaration.start_datetime
        operation_end_time = flight_declaration.end_datetime

        # C2 check 
        try: 
            assert flight_declaration.aircraft_id == aircraft_id
        except AssertionError as ae: 
            invalid_aircraft_id_msg = "The aircraft ID provided in telemetry for operation {flight_declaration_id}, does not match the declared / authorized aircraft, you must stop operation.".format(flight_declaration_id = flight_declaration_id)
            logging.error(invalid_aircraft_id_msg)
            my_operation_notification.send_conformance_status_notification(message = invalid_aircraft_id_msg, level='error')
            return False        
        
        # C3 + C4 check 
        try: 
            assert flight_declaration.state in ['Accepted','Activated']
        except AssertionError as ae: 
            flight_state_not_correct_msg = "The Operation state for operation {flight_declaration_id}, is not one of 'Accepted' or 'Activated', your authorization is invalid.".format(flight_declaration_id = flight_declaration_id)
            logging.error(flight_state_not_correct_msg)
            my_operation_notification.send_conformance_status_notification(message = flight_state_not_correct_msg, level='error')
            
            return False

        # C5 check
        try: 
            assert is_time_between(begin_time=operation_start_time, end_time=operation_end_time, check_time= now)
        except AssertionError as ae:
            telemetry_timestamp_not_within_op_start_end_msg = "The telemetry timestamp provided for operation {flight_declaration_id}, is not within the start / end time for an operation.".format(flight_declaration_id = flight_declaration_id)
            logging.error(telemetry_timestamp_not_within_op_start_end_msg)
            my_operation_notification.send_conformance_status_notification(message = telemetry_timestamp_not_within_op_start_end_msg, level='error')
            return False  
        
        # C6 check : Check if the aircraft is within the 4D volume 


        # C7 check Check if aircraft is not breaching any active Geofences


        return True

    def check_flight_authorization_conformance(self, operation_id: str) -> bool:  
        """ This method checks the conformance of a flight authorization independent of telemetry observations being sent:            
            C8 Check if telemetry is being sent
            C9 Has not ended and the time limit of the flight authorization has passed
        """



        raise NotImplementedError

    
    

    

