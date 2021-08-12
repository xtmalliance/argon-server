from typing import List, NamedTuple,Optional
from uuid import uuid4


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


class SubscriptionResponse(NamedTuple):
    ''' A object to hold details of a request for creation of subscription in the DSS '''
    created: bool
    dss_subscription_id: Optional[uuid4]
    notification_index: int

class CreateSubscriptionResponse(NamedTuple):
    ''' Output of a request to create subscription '''
    message: str
    id: uuid4
    dss_subscription_response: Optional[SubscriptionResponse]