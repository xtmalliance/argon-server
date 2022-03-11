from dataclasses import dataclass
from uuid import uuid4
import enum
import arrow
from typing import List, Literal, Optional, Union

class StringBasedDateTime(str):
  """String that only allows values which describe a datetime."""
  def __new__(cls, value):
    if isinstance(value, str):
      t = arrow.get(value).datetime
    else:
      t = value
    str_value = str.__new__(cls, arrow.get(t).to('UTC').format('YYYY-MM-DDTHH:mm:ss.SSSSSS') + 'Z')
    str_value.datetime = t
    return str_value

@dataclass
class LatLngPoint:
    '''A clas to hold information about LatLngPoint'''
    lat: float
    lng: float

@dataclass
class Radius:
    ''' A class to hold the radius object '''
    value: float
    units:str

@dataclass
class Time:
    ''' A class to hold time objects'''
    format: str
    value: StringBasedDateTime

@dataclass
class Radius:
    ''' A class to hold the radius object '''
    value: float
    units:str

@dataclass
class Polygon:
    ''' A class to hold the polygon object '''
    vertices: List[LatLngPoint] # A minimum of three LatLngPoints

@dataclass
class Circle:
    ''' Hold the details of a circle object '''
    center: LatLngPoint 
    radius: Radius

@dataclass
class Altitude:
    ''' A class to hold altitude '''
    value:int
    reference:str
    units: str

@dataclass
class OperationalIntentReference:
    """Class for keeping track of an operational intent reference"""
    id: uuid4

@dataclass
class Volume3D:
    '''A class to hold Volume3D objects'''
    outline_circle: Circle
    outline_polygon: Polygon
    altitude_lower: Altitude
    altitude_upper: Altitude

class OperationalIntentState(str, enum.Enum):
    ''' A test is either pass or fail or could not be processed, currently not  '''
    Accepted = 'Accepted'
    Activated = 'Activated'
    Nonconforming = 'Nonconforming'
    Contingent = 'Contingent'

@dataclass
class Volume4D:
    '''A class to hold Volume4D objects'''
    volume: Volume3D
    time_start: StringBasedDateTime
    time_end: StringBasedDateTime

@dataclass
class OperationalIntentTestInjection:
    """Class for keeping track of an operational intent test injections"""
    volumes: List[Volume4D]
    priority: int
    off_nominal_volumes: Optional[List[Volume4D]]
    state: Literal[OperationalIntentState.Accepted,OperationalIntentState.Activated,OperationalIntentState.Nonconforming,OperationalIntentState.Contingent]

class OperationCategory(str, enum.Enum):
    ''' A enum to hold all categories of an operation '''
    Vlos = 'vlos'
    Bvlos = 'bvlos'

class UASClass(str, enum.Enum):
    ''' A enum to hold all UAS Classes '''
    C0 = 'C0'
    C1 = 'C1'
    C2 = 'C2'
    C3 = 'C3'
    C4 = 'C4'

class TestInjectionResultState(str, enum.Enum):
    ''' A test is either pass or fail or could not be processed, currently not  '''
    Planned = 'Planned'
    Rejected = 'Rejected'
    ConflictWithFlight = 'ConflictWithFlight'
    Failed = 'Failed'
    
class IDTechnology(str, enum.Enum):
    ''' A enum to hold ID technologies for an operation '''
    Network = 'network'
    Broadcast = 'broadcast'

class StatusResponseEnum(str, enum.Enum):
    ''' A enum to hold ID technologies for an operation '''
    Starting = 'Starting'
    Ready = 'Ready'

class DeleteFlightStatusResponseEnum(str, enum.Enum):
    ''' A enum to hold ID technologies for an operation '''
    Closed = 'Closed'
    Failed = 'Failed'

@dataclass
class FlightAuthorizationDataPayload:
    '''A class to hold information about Flight Authorization Test'''
    uas_serial_number: str
    operation_mode: Literal[OperationCategory.Vlos, OperationCategory.Bvlos]
    operation_category: str
    uas_class: Literal[UASClass.C0, UASClass.C1,
                       UASClass.C2, UASClass.C3, UASClass.C4, ]
    identification_technologies: Literal[IDTechnology.Network,
                                         IDTechnology.Broadcast]
    connectivity_methods: List[str]
    endurance_minutes: int
    emergency_procedure_url: str
    operator_id: str
@dataclass
class SCDTestInjectionDataPayload:
    operational_intent: OperationalIntentTestInjection
    flight_authorisation: FlightAuthorizationDataPayload


@dataclass
class TestInjectionResult: 
    result: Literal[TestInjectionResultState.Planned, TestInjectionResultState.Rejected, TestInjectionResultState.ConflictWithFlight,TestInjectionResultState.Failed]
    notes:str
    operational_intent_id: uuid4

@dataclass
class StatusResponse:
    status: Literal[StatusResponseEnum.Starting, StatusResponseEnum.Ready]

@dataclass
class DeleteFlightResponse:
    ''' Delete flight status response'''
    result: Literal[DeleteFlightStatusResponseEnum.Failed, DeleteFlightStatusResponseEnum.Closed]
    notes: str

@dataclass 
class ClearAreaResponse:
    ''' Response after clearing flights in an area '''
    success: bool
    message: str
    timestamp: StringBasedDateTime

@dataclass 
class ClearAreaRequestData:
    ''' Request to clear flights in an area '''
    request_id: uuid4
    extent: Volume4D

@dataclass
class ImplicitSubscriptionParameters:
    uss_base_url:str
    notify_for_constraints: bool = False

@dataclass 
class OperationalIntentReference: 
    ''' A operational intent reference for the DSS '''
    extents: List[Volume4D]
    key: List[str]
    state:str
    uss_base_url:str
    new_subscription:ImplicitSubscriptionParameters

@dataclass
class OpIntSubscribers:
    subscribers: List[str]

@dataclass
class OperationalIntentReferenceDSSResponse:
    id: str
    manager: str
    uss_availability: str
    version: int
    state: Literal[OperationalIntentState.Accepted,OperationalIntentState.Activated,OperationalIntentState.Nonconforming,OperationalIntentState.Contingent]
    ovn: uuid4 
    time_start: Time
    time_end: Time
    uss_base_url: str
    subscription_id: str

@dataclass
class DSSOperationalIntentCreateResponse: 
    subscribers: List[str]
    operational_intent_reference: OperationalIntentReferenceDSSResponse
    
@dataclass
class LatLng:
    lat:float
    lng: float
    
@dataclass
class OperationalIntentStorage:
    bounds:str
    start_time:str
    end_time: str
    alt_max:float
    alt_min: float
    success_response: DSSOperationalIntentCreateResponse

@dataclass 
class OperationalIntentSubmissionError: 
    result: str
    notes: str

@dataclass 
class OperationalIntentSubmissionStatus: 
    dss_response: Union[DSSOperationalIntentCreateResponse,OperationalIntentSubmissionError]
    status: str
    status_code: int
    message: str