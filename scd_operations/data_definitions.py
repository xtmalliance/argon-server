from implicitdict import ImplicitDict, StringBasedDateTime
from typing import List, Optional, Literal

class LatLngPoint(ImplicitDict):
    """A class to hold information about a location as Latitude / Longitude pair"""

    lat: float
    lng: float


class Radius(ImplicitDict):
    """A class to hold the radius of a circle for the outline_circle object"""

    value: float
    units: str


class Polygon(ImplicitDict):
    """A class to hold the polygon object, used in the outline_polygon of the Volume3D object"""

    vertices: List[LatLngPoint]  # A minimum of three LatLngPoints are required


class Circle(ImplicitDict):
    """A class the details of a circle object used in the outline_circle object"""

    center: LatLngPoint
    radius: Radius


class Altitude(ImplicitDict):
    """A class to hold altitude information"""

    value: float
    reference: Literal["W84"]
    units: str


class Time(ImplicitDict):
    """A class to hold Time details"""

    value: StringBasedDateTime
    format: Literal["RFC3339"]


class Volume3D(ImplicitDict):
    """A class to hold Volume3D objects"""

    outline_circle: Optional[Circle]
    outline_polygon: Optional[Polygon]
    altitude_lower: Optional[Altitude]
    altitude_upper: Optional[Altitude]


class Volume4D(ImplicitDict):
    """A class to hold Volume4D objects"""

    volume: Volume3D
    time_start: Optional[Time]
    time_end: Optional[Time]


class OperationalIntentReference(ImplicitDict):
    id: str
    manager: str
    uss_availability: str
    version: int
    state: str
    ovn: str
    time_start: Time
    time_end: Time
    uss_base_url: str
    subscription_id: str


class OperationalIntentDetails(ImplicitDict):
    volumes: List[Volume4D]
    off_nominal_volumes: List[Volume4D]
    priority: int


class OperationalIntent(ImplicitDict):
    reference: OperationalIntentReference
    details: OperationalIntentDetails
