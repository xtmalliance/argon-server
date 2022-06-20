from .geofence_typing import ImplicitDict
from typing import List

class ZoneAuthority(ImplicitDict):
    name: str
    service: str
    email: str
    contactName: str
    siteURL: str
    phone: str
    purpose: str
    intervalBefore: str


class HorizontalProjection(ImplicitDict):
    type: str
    coordinates: List[list]

class ED269Geometry(ImplicitDict):
    uomDimensions: str
    lowerLimit: int
    lowerVerticalReference: str
    upperLimit: float
    upperVerticalReference: str
    horizontalProjection: 

class GeoZoneFeature(ImplicitDict):
    identifier: str
    country: str
    name: str
    type: str
    restriction: str
    restrictionConditions: str
    region: int
    reason: List[str]
    otherReasonInfo: str
    regulationExemption: str
    uSpaceClass: str
    message: str
    applicability: List[Dict[str, str]]
    zoneAuthority: ZoneAuthority
    geometry: ED269Geometry


class GeoZone(ImplicitDict):
    title: str
    description: str
    features: List[GeoZoneFeature]