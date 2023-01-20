from dataclasses import dataclass
from uuid import uuid4
import enum
import arrow
from typing import List, Literal, Optional, Union
from shapely.geometry import Polygon
from implicitdict import StringBasedDateTime

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
class Volume3D:
    '''A class to hold Volume3D objects'''
    outline_polygon: Polygon
    altitude_lower: Altitude
    altitude_upper: Altitude
    outline_circle: Circle = None

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

class DeleteFlightStatus(str, enum.Enum):
    
    Closed = 'Closed'
    Failed = 'Failed'
    
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
    ''' A enum to specify if the USS is ready (or not) '''
    Starting = 'Starting'
    Ready = 'Ready'

class DeleteFlightStatusResponseEnum(str, enum.Enum):
    ''' A enum to hold Flight Status '''
    Closed = 'Closed'
    Failed = 'Failed'

class USSCapabilitiesResponseEnum(str, enum.Enum):
    ''' A enum to hold USS capabilites operation '''
    BasicStrategicConflictDetection = 'BasicStrategicConflictDetection'
    FlightAuthorisationValidation = 'FlightAuthorisationValidation'
    HighPriorityFlights = 'HighPriorityFlights'

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
class SCDTestStatusResponse:
    status: Literal[StatusResponseEnum.Starting, StatusResponseEnum.Ready]
    version: str

@dataclass
class CapabilitiesResponse:
    capabilities: List[Literal[USSCapabilitiesResponseEnum.BasicStrategicConflictDetection, USSCapabilitiesResponseEnum.FlightAuthorisationValidation, USSCapabilitiesResponseEnum.HighPriorityFlights]]
    

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
    new_subscription:Optional[ImplicitSubscriptionParameters] = None

@dataclass 
class PartialCreateOperationalIntentReference: 
    ''' A operational intent reference for the DSS that is stored in the Database '''
    volumes: List[Volume4D]
    priority:str
    state:str
    off_nominal_volumes:List[Volume4D]

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
class OperationalIntentSubmissionSuccess: 
    subscribers: List[str]
    operational_intent_reference: OperationalIntentReferenceDSSResponse

@dataclass
class OperationalIntentUSSDetails:
    volumes: List[Volume4D]
    priority: int
    off_nominal_volumes: Optional[List[Volume4D]]

@dataclass
class OperationalIntentDetailsUSSResponse:
    reference:OperationalIntentReferenceDSSResponse
    details: OperationalIntentUSSDetails

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
    success_response: OperationalIntentSubmissionSuccess
    operational_intent_details: OperationalIntentTestInjection

@dataclass 
class OperationalIntentSubmissionError:     
    result: str
    notes: str

@dataclass 
class OperationalIntentSubmissionStatus: 
    dss_response: Union[OperationalIntentSubmissionSuccess,OperationalIntentSubmissionError]
    status: str
    status_code: int
    message: str
    operational_intent_id: uuid4

@dataclass
class DeleteOperationalIntentConstuctor:
    """This method holds information to send to the DSS to delete a Operational intent """
    entity_id:uuid4
    ovn: uuid4

@dataclass
class DeleteOperationalIntentResponseSuccess:
    """This method holds details of the data the DSS provides once a operational intent is deleted """
    subscribers: List[str]
    operational_intent_reference: OperationalIntentReferenceDSSResponse

@dataclass
class CommonDSS4xxResponse:
    message:str    

@dataclass
class CommonDSS2xxResponse:
    message:str    

@dataclass
class DeleteOperationalIntentResponse:
    dss_response: Union[DeleteOperationalIntentResponseSuccess,CommonDSS4xxResponse]
    status: int
    message:Union[CommonDSS4xxResponse, CommonDSS2xxResponse]
    
@dataclass
class DeleteFlightResponse:
    result:  Literal[DeleteFlightStatus.Closed, DeleteFlightStatus.Failed]
    notes:str

@dataclass
class QueryOperationalIntentPayload:
    area_of_interest: Volume4D

@dataclass
class OperationalIntentReferenceDSSDetails:
    operational_intent_refrence: OperationalIntentReferenceDSSResponse

@dataclass
class SuccessfulOperationalIntentFlightIDStorage:
    flight_id:str
    operational_intent_id:str

@dataclass
class OpInttoCheckDetails:
    ovn: str
    shape: Polygon
