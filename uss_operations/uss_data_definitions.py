from dataclasses import dataclass
from scd_operations.scd_data_definitions import OperationalIntentDetailsUSSResponse
@dataclass
class OperationalIntentNotFoundResponse:
    message:str

@dataclass
class OperationalIntentDetails:
    operational_intent: OperationalIntentDetailsUSSResponse
    
@dataclass
class UpdateOperationalIntent: 
    message:str