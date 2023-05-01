from dataclasses import dataclass
from typing import Optional
from enum import Enum

SpecificSessionID = str
@dataclass
class LatLngPoint:
  lat: float
  lng: float

class Reference1(str, Enum):
    W84 = 'W84'

class Units(str, Enum):
    M = 'M'

class Category(str, Enum):
    EUCategoryUndefined = 'EUCategoryUndefined'
    Open = 'Open'
    Specific = 'Specific'
    Certified = 'Certified'

class Class(str, Enum):
    EUClassUndefined = 'EUClassUndefined'
    Class0 = 'Class0'
    Class1 = 'Class1'
    Class2 = 'Class2'
    Class3 = 'Class3'
    Class4 = 'Class4'
    Class5 = 'Class5'
    Class6 = 'Class6'

@dataclass
class Altitude:
    value: float
    reference: Reference1
    units: Units

class AltitudeType(Enum):
    Takeoff = 'Takeoff'
    Dynamic = 'Dynamic'
    Fixed = 'Fixed'

@dataclass
class RIDAuthData:
    data: Optional[str] = ''
    format: Optional[int] = 0

@dataclass
class OperatorLocation:
    position: LatLngPoint
    altitude: Optional[Altitude] = None
    altitude_type: Optional[AltitudeType] = None

@dataclass
class UASID:
    specific_session_id: Optional[SpecificSessionID] = None
    serial_number: Optional[str] = ''
    registration_id: Optional[str] = ''
    utm_id: Optional[str] = ''


@dataclass
class UAClassificationEU:
    category: Optional[Category] = 'EUCategoryUndefined'
    class_: Optional[Class] = 'EUClassUndefined'



@dataclass
class RIDOperatorDetails:
    id: str
    eu_classification: Optional[UAClassificationEU] = None
    uas_id: Optional[UASID] = None
    operator_location: Optional[OperatorLocation] = None
    auth_data: Optional[RIDAuthData] = None
    operator_id: Optional[str] = ''
    operation_description: Optional[str] = ''
