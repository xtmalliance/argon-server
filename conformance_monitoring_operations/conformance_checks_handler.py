from common.database_operations import BlenderDatabaseReader()

from common.data_definitions import OPERATION_STATES
from operation_state_helper import FlightOperationStateMachine, match_state, get_status

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


    def transition_operation_state(self, current_state:int, new_state: int, event:str) -> bool:
        original_state = match_state(current_state)

        my_operation_state_machine =FlightOperationStateMachine(state = original_state)
        my_operation_state_machine.on_event(event)
        new_state = get_status(my_operation_state_machine.state)

        if original_state == new_state: 
            ## The event cannot trigger a change of state, flight state is not updated
            return False
        else: 
            ## The event can trigger a change of state, flight state updated
            self.flight_declaration.state = new_state
            self.flight_declaration.save()
            self.flight_declaration.add_state_history_entry(notes = "Updated flight state", new_state = new_state, original_state = original_state)
            return True
          