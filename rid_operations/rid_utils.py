from typing import List, NamedTuple, Optional
import uuid
from dataclasses import dataclass, field
import arrow

from scd_operations.scd_data_definitions import Volume3D, Volume4D

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


class Position(NamedTuple):
    ''' A class to hold most recent position for remote id data '''
    lat:float
    lng:float
    alt:float

class RIDPositions(NamedTuple):
    ''' A list of positions for RID'''
    positions: List[Position]

class RIDFlight(NamedTuple):    
    id:str
    most_recent_position: Position
    recent_paths: List[RIDPositions]

class ClusterDetails(NamedTuple):
    corners:List[Position]
    area_sqm: float
    number_of_flights: float

class RIDDisplayDataResponse(NamedTuple):
    flights: List[RIDFlight]
    clusters: List[ClusterDetails]

@dataclass
class SubscriptionResponse:
    ''' A object to hold details of a request for creation of subscription in the DSS '''
    created: bool
    dss_subscription_id: Optional[uuid.uuid4]
    notification_index: int

@dataclass
class RIDVertex:
  lat:float
  lng: float

@dataclass
class RIDFootprint:
  vertices: List[RIDVertex]

@dataclass
class RIDVolume3D:
  footprint: RIDFootprint
  altitude_lo: int
  altitude_high: int

@dataclass
class RIDVolume4D:
  spatial_volume: RIDVolume3D
  time_start: str
  time_end: str

@dataclass
class SubscriptionState:
  subscription_id: str
  notification_index: int = 0

@dataclass
class SubscriberToNotify:
  url: str
  subscriptions: List[SubscriptionState] = field(default_factory=[])

@dataclass
class ISACreationRequest:
    ''' A object to hold details of a request that indicates the DSS '''
    extents: Volume4D
    flights_url: str

@dataclass
class IdentificationServiceArea:  
  flights_url: str
  owner: str
  time_start: StringBasedDateTime
  time_end: StringBasedDateTime
  version: str
  id: str

@dataclass
class ISACreationResponse:
    ''' A object to hold details of a request for creation of an ISA in the DSS '''
    created: bool
    subscribers: List[SubscriberToNotify]
    service_area:IdentificationServiceArea


class CreateSubscriptionResponse(NamedTuple):
    ''' Output of a request to create subscription '''
    message: str
    id: uuid.uuid4
    dss_subscription_response: Optional[SubscriptionResponse]

@dataclass
class RIDAircraftPosition:
  lat: float
  lng: float
  alt: float
  accuracy_h: str
  accuracy_v: str
  extrapolated: Optional[bool]
  pressure_altitude: Optional[float]

@dataclass
class RIDHeight:
  distance: float
  reference: str

@dataclass
class LatLngPoint:
  lat: float
  lng: float

@dataclass
class RIDAuthData:
  format: str
  data: str

@dataclass
class RIDFlightDetails:
  id: str
  operator_id: Optional[str]
  operator_location: Optional[LatLngPoint]
  operation_description: Optional[str]
  auth_data: Optional[RIDAuthData]
  serial_number: Optional[str]
  registration_number: Optional[str]


@dataclass
class FlightState:     
  timestamp: StringBasedDateTime
  timestamp_accuracy: float
  operational_status: Optional[str]
  position: RIDAircraftPosition
  track: float
  speed: float
  speed_accuracy: str
  vertical_speed: float
  height: Optional[RIDHeight]
  group_radius:int
  group_ceiling: int
  group_floor: int
  group_count: int
  group_time_start: StringBasedDateTime
  group_time_end: StringBasedDateTime

@dataclass
class RIDTestDetailsResponse: 
    effective_after: str
    details: RIDFlightDetails

@dataclass
class RIDTestInjection: 
    injection_id: uuid
    telemetry: List[FlightState]
    details_responses: List[RIDTestDetailsResponse]

@dataclass
class HTTPErrorResponse:
  message: str
  status: int

@dataclass
class CreateTestPayload:
  requested_flights: List[RIDTestInjection]
  test_id: uuid

@dataclass
class CreateTestResponse:
    injected_flights: List[RIDTestInjection]
    version: int

@dataclass
class RIDAircraftPosition:
  lat: float
  lng: float
  alt: float
  accuracy_h: str
  accuracy_v: str
  extrapolated: Optional[bool]
  pressure_altitude: Optional[float]

@dataclass
class RIDHeight:
  distance: float
  reference: str

@dataclass
class RIDAircraftState:
  timestamp: StringBasedDateTime
  timestamp_accuracy: float
  operational_status: Optional[str]
  position: RIDAircraftPosition
  track: float
  speed: float
  speed_accuracy: str
  vertical_speed: float
  height: Optional[RIDHeight]

@dataclass
class RIDRecentAircraftPosition:
  time: StringBasedDateTime
  position: RIDAircraftPosition

@dataclass
class RIDFlight:
  id: str
  aircraft_type: str
  current_state: Optional[RIDAircraftState]  
  simulated: Optional[bool]
  recent_positions: Optional[List[RIDRecentAircraftPosition]]

@dataclass
class FullRequestedFlightDetails:
  id: uuid
  telemetry_length: int
  injection_details: List[RIDTestInjection]

@dataclass
class RIDRecentAircraftPosition:
  time:str
  position:Position

@dataclass
class RIDFlightResponseDetails:
  id: str
  aircraft_type: str
  current_state: RIDAircraftState
  # volumes: Optional[List[Volume4D]]
  simulated: bool
  recent_positions: List[RIDRecentAircraftPosition]

@dataclass
class RIDFlightResponse:
  timestamp: str
  flights: List[RIDFlightResponseDetails]

@dataclass
class AuthData:
  format: str
  data: str

@dataclass
class SingleObeservationMetadata:
  details_response: RIDTestDetailsResponse
  telemetry: RIDAircraftState

