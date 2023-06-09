from common.database_operations import BlenderDatabaseReader
from .operation_state_helper import FlightOperationStateMachine, match_state, get_status
from django.core import management
from dotenv import load_dotenv, find_dotenv
import logging
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')


class FlightOperationConformanceHelper():
    """
    This class handles changes / transitions to a operation when the conformance check fails, it transitions  
    """

    def __init__(self, flight_declaration_id:str):
        self.flight_declaration_id = flight_declaration_id
        self.my_database_reader = BlenderDatabaseReader()
        self.flight_declaration = self.my_database_reader.get_flight_declaration_by_id(flight_declaration_id=self.flight_declaration_id)


    def verify_operation_state_transition(self, original_state:int, new_state: int, event:str) -> bool:
        """
        This class updates the state of a flight operation.
        """        
        my_operation_state_machine = FlightOperationStateMachine(state = original_state)
        logging.info("Current Operation State %s" % my_operation_state_machine.state)
        logging.info(event)
        my_operation_state_machine.on_event(event)
        new_state = get_status(my_operation_state_machine.state)
        if original_state == new_state: 
            ## The event cannot trigger a change of state, flight state is not updated
            logging.info("State change verification failed")
            return False
        else: 
            return True
          
    def manage_operation_state_transition(self, original_state:int, new_state: int, event:str):
        '''
        This method manages the communication with DSS once a new state has been achieved
        '''
        if new_state == 5: #operation has ended
            if event =='operator_confirms_ended':
                management.call_command('operation_ended_clear_dss',flight_operation_id = self.flight_declaration_id)

        elif new_state == 4: # handle entry into contingent state
            if original_state == 2 and event == 'operator_initiates_contingent':
                # Operator activates contingent state from Activated state
                pass            
            elif original_state == 3 and event in ['timeout','operator_confirms_contingent']:
                # Operator activates contingent state / timeout from Non-conforming state 
                pass

        elif new_state == 3: # handle entry in non-conforming state
            if original_state == 1 and event == 'ua_departs_early_late_outside_op_intent': 
                # Enters non-conforming from Accepted
                # Command: Update / expand volumes
                pass
            elif original_state ==2 and event == 'ua_exits_coordinated_op_intent': 
                # Enters non-conforming from Activated
                # Command: Update / expand volumes
                pass
        
        elif new_state == 2: # handle entry into activated state
            if original_state == 1 and event == 'operator_initiates_contingent':
                # Operator activates contingent state from Activated state
                pass

            elif original_state == 3 and event in ['timeout','operator_confirms_contingent']:
                # Operator activates contingent state / timeout from Non-conforming state 
                pass