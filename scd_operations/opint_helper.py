from flight_declaration_operations.models import FlightDeclaration
from . import dss_scd_helper
from rid_operations import rtree_helper
import uuid
import arrow
import json
from .data_definitions import FlightDeclarationOperationalIntentStorageDetails
from .scd_data_definitions import OperationalIntentSubmissionStatus
from common.database_operations import BlenderDatabaseReader, BlenderDatabaseWriter
from dacite import from_dict
import logging
logger = logging.getLogger('django')

INDEX_NAME = 'opint_idx'

class DSSOperationalIntentsCreator():
    ''' This class provides helper function to submit a operational intent in the DSS based on a operation ID'''

    def __init__(self, flight_declaration_id: str):
        self.flight_declaration_id = flight_declaration_id

    def validate_flight_declaration_start_end_time(self) -> bool: 
        my_database_reader = BlenderDatabaseReader()
        flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id= self.flight_declaration_id)        
        # check that flight declaration start and end time is in the next two hours
        now = arrow.now()
        two_hours_from_now = now.shift(hours = 2)

        op_start_time = arrow.get(flight_declaration.start_datetime)
        op_end_time = arrow.get(flight_declaration.end_datetime)

        start_time_ok =  (op_start_time <= two_hours_from_now and op_start_time >= now)
        end_time_ok = (op_end_time <= two_hours_from_now and op_end_time >= now)
        
        start_end_time_oks  = [start_time_ok, end_time_ok]
        if False in start_end_time_oks:
            return False
        else: 
            return True
        
    def submit_flight_declaration_to_dss(self) -> OperationalIntentSubmissionStatus:
        """ This method submits a flight declaration as a operational intent to the DSS """
        # Get the Flight Declaration object
        
        new_entity_id = str(uuid.uuid4())

        my_database_reader = BlenderDatabaseReader()
        my_database_writer = BlenderDatabaseWriter()
        
        flight_declaration = my_database_reader.get_flight_declaration_by_id(flight_declaration_id= self.flight_declaration_id)   

        flight_authorization = my_database_reader.get_flight_authorization_by_flight_declaration_obj(flight_declaration = flight_declaration)
        
        view_rect_bounds = flight_declaration.bounds
        operational_intent  = json.loads(flight_declaration.operational_intent)

        operational_intent_data = from_dict(data_class=FlightDeclarationOperationalIntentStorageDetails, data=operational_intent)
                
        my_rtree_helper = rtree_helper.OperationalIntentsIndexFactory(index_name=INDEX_NAME)
        my_scd_dss_helper = dss_scd_helper.SCDOperations()
        my_rtree_helper.generate_operational_intents_index(pattern='flight_opint.*')
        view_box = list(map(float, view_rect_bounds.split(',')))
        
        all_flight_declarations = my_rtree_helper.check_box_intersection(view_box= view_box)        

        # flight authorisation data is correct, can submit the operational intent to the DSS
        self_deconflicted = False if operational_intent_data.priority == 0 else True
        
        if all_flight_declarations and self_deconflicted == False:
            # there are existing op_ints in the area. 
            deconflicted_status = []
            for existing_op_int in all_flight_declarations:     
                # check if start time or end time is between the existing bounds
                is_start_within = dss_scd_helper.is_time_within_time_period(start_time=arrow.get(existing_op_int['start_time']).datetime, end_time= arrow.get(existing_op_int['end_time']).datetime, time_to_check=arrow.get(flight_declaration.start_datetime))
                is_end_within = dss_scd_helper.is_time_within_time_period(start_time=arrow.get(existing_op_int['start_time']).datetime, end_time= arrow.get(existing_op_int['end_time']).datetime, time_to_check=flight_declaration.end_datetime)

                timeline_status = [is_start_within, is_end_within]
        
                if all(timeline_status):      
                    deconflicted_status.append(True)
                else:
                    deconflicted_status.append(False)
            
            self_deconflicted = all(deconflicted_status)
        else:
            # No existing op ints we can plan it.             
            self_deconflicted = True
        
        my_rtree_helper.clear_rtree_index(pattern='flight_opint.*')   
        logger.info("Self deconfliction status %s" % self_deconflicted)        
        if self_deconflicted:                 
            auth_token = my_scd_dss_helper.get_auth_token()
            
            if 'error' in auth_token:
                logging.error("Error in retrieving auth_token, check if the auth server is running properly, error details displayed above")
                logging.error(auth_token['error'])           
                op_int_submission = OperationalIntentSubmissionStatus(status = "auth_server_error", status_code = 500, message = "Error in getting a token from the Auth server", dss_response={}, operational_intent_id = new_entity_id)
            else:
                op_int_submission = my_scd_dss_helper.create_and_submit_operational_intent_reference(state = operational_intent_data.state, volumes = operational_intent_data.volumes, off_nominal_volumes = operational_intent_data.off_nominal_volumes, priority = operational_intent_data.priority)

                # Update flight Authorization 
                if op_int_submission.status_code in [200, 201]:
                    my_database_writer.update_flight_authorization_op_int(flight_authorization=flight_authorization, dss_operational_intent_id=op_int_submission.operational_intent_id)                    

        else: 
            logger.error("Flight not deconflicted, there are other flights in the area")            
            op_int_submission = OperationalIntentSubmissionStatus(status = "conflict_with_flight", status_code = 500, message = "Flight not deconflicted, there are other flights in the area", dss_response={}, operational_intent_id = new_entity_id)
        
        return op_int_submission        