from dataclasses import dataclass
from typing import Optional


@dataclass
class LatLngPoint:
  lat: float
  lng: float

@dataclass
class RIDOperatorDetails():
  id: str
  operator_location: LatLngPoint
  operator_id: Optional[str]
  operation_description: Optional[str]
  serial_number: Optional[str]
  registration_number: Optional[str]
  aircraft_type:str = 'Helicopter'
