from dataclasses import dataclass
from typing import Optional, List
from shapely.geometry import shape

@dataclass
class FlightDeclarationRequest:
    """Class for keeping track of an operational intent test injections"""
    features: List[shape]
    type_of_operation: int
    submitted_by: Optional[str]
    approved_by: Optional[str]
    is_approved: bool
    state:int