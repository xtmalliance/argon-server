from flight_declaration_operations.models import FlightDeclaration
from . import dss_scd_helper
from rid_operations import rtree_helper
import uuid
import arrow

from .data_definitions import OperationalIntent
from .scd_data_definitions import OperationalIntentSubmissionStatus
from implicitdict import ImplicitDict

import logging
logger = logging.getLogger('django')

INDEX_NAME = 'opint_proc'

class DSSOperationalIntentsCreator():
    ''' This class provides helper function to submit a operational intent in the DSS based on a operation ID'''

    def __init__(self, flight_declaration_id: str):
        self.flight_declaration_id = flight_declaration_id

    def submit_flight_declaration_to_dss(self):
        """ This method submits a flight declaration as a operational intent to the DSS """
        # Get the Flight Declaration object
        
        new_entity_id = str(uuid.uuid4())
        flight_declaration = FlightDeclaration.objects.get(id = self. flight_declaration_id)
        view_rect_bounds = flight_declaration.bounds
        operational_intent_data = ImplicitDict.parse(flight_declaration.operational_intent, OperationalIntent)
        my_rtree_helper = rtree_helper.RTreeIndexFactory(index_name=INDEX_NAME)
        my_scd_dss_helper = dss_scd_helper.SCDOperations()
        my_rtree_helper.generate_operational_intents_index(pattern='flight_opint.*')
        all_existing_op_ints_in_area = my_rtree_helper.check_box_intersection(view_box= view_rect_bounds)        

        # flight authorisation data is correct, can submit the operational intent to the DSS
        self_deconflicted = False if operational_intent_data.priority == 0 else True
        
        if all_existing_op_ints_in_area and self_deconflicted == False:
            # there are existing op_ints in the area. 
            deconflicted_status = []
            for existing_op_int in all_existing_op_ints_in_area:     
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
        if self_deconflicted:                         
            op_int_submission = my_scd_dss_helper.create_and_submit_operational_intent_reference(state = operational_intent_data.state, volumes = operational_intent_data.volumes, off_nominal_volumes = operational_intent_data.off_nominal_volumes, priority = operational_intent_data.priority)

        else: 
            logger.info("Flight not deconflicted, there are other flights in the area")            
            op_int_submission = OperationalIntentSubmissionStatus(status = "conflict_with_flight", status_code = 500, message = "Flight not deconflicted, there are other flights in the area", dss_response={}, operational_intent_id = new_entity_id)


        return op_int_submission
        