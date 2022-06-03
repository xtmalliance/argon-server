from dataclasses import dataclass
from typing import Optional
from scd_operations.scd_data_definitions import OperationalIntentReference


@dataclass
class FlightDeclarationRequest:
    """Class for keeping track of an operational intent test injections"""
    operational_intent: OperationalIntentReference
    type_of_operation: int
    
    submitted_by: Optional[str]
    approved_by: Optional[str]
    is_approved: bool