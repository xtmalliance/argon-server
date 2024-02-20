import enum
from dataclasses import dataclass
from typing import List, Literal, Optional, Union

from rid_operations.rid_utils import RIDOperatorDetails


# TODO: Need to consolidate all data_definitions across different apps
@dataclass
class OperationalIntentNotFoundResponse:
    message: str


@dataclass
class Time:
    """A class to hold time objects"""

    format: str
    value: str


@dataclass
class UpdateOperationalIntent:
    message: str


@dataclass
class GenericErrorResponseMessage:
    message: str


@dataclass
class SummaryFlightsOnly:
    number_of_flights: int
    timestamp: str


@dataclass
class FlightDetailsNotFoundMessage:
    message: str


@dataclass
class OperatorDetailsSuccessResponse:
    details: RIDOperatorDetails


@dataclass
class SubscriptionState:
    subscription_id: str
    notification_index: int


@dataclass
class LatLngPoint:
    """A clas to hold information about LatLngPoint"""

    lat: float
    lng: float


@dataclass
class Radius:
    """A class to hold the radius object"""

    value: float
    units: str


@dataclass
class Polygon:
    """A class to hold the polygon object"""

    vertices: List[LatLngPoint]  # A minimum of three LatLngPoints


@dataclass
class Circle:
    """Hold the details of a circle object"""

    center: LatLngPoint
    radius: Radius


@dataclass
class Altitude:
    """A class to hold altitude"""

    value: Union[int, float]
    reference: str
    units: str


@dataclass
class Volume3D:
    """A class to hold Volume3D objects"""

    outline_polygon: Polygon
    altitude_lower: Altitude
    altitude_upper: Altitude
    outline_circle: Circle = None


class OperationalIntentState(str, enum.Enum):
    """A test is either pass or fail or could not be processed, currently not"""

    Accepted = "Accepted"
    Activated = "Activated"
    Nonconforming = "Nonconforming"
    Contingent = "Contingent"


@dataclass
class Volume4D:
    """A class to hold Volume4D objects"""

    volume: Volume3D
    time_start: Time
    time_end: Time


@dataclass
class OperationalIntentReferenceDSSResponse:
    id: str
    manager: str
    uss_availability: str
    version: int
    state: Literal[
        OperationalIntentState.Accepted,
        OperationalIntentState.Activated,
        OperationalIntentState.Nonconforming,
        OperationalIntentState.Contingent,
    ]
    ovn: str
    time_start: Time
    time_end: Time
    uss_base_url: str
    subscription_id: str


@dataclass
class OperationalIntentUSSDetails:
    volumes: List[Volume4D]
    priority: int
    off_nominal_volumes: Optional[List[Volume4D]]


@dataclass
class OperationalIntentDetailsUSSResponse:
    reference: OperationalIntentReferenceDSSResponse
    details: OperationalIntentUSSDetails


@dataclass
class OperationalIntentDetails:
    operational_intent: OperationalIntentDetailsUSSResponse


@dataclass
class UpdateChangedOpIntDetailsPost:
    operational_intent_id: str
    subscriptions: List[SubscriptionState]
    operational_intent: Optional[OperationalIntentDetailsUSSResponse] = None
