from .geofence_typing import ImplicitDict
from typing import List, Dict, Literal, Optional
from dataclasses import dataclass
import enum


class GeoAwarenessStatusResponseEnum(str, enum.Enum):
    ''' A enum to specify if the USS is ready (or not) '''
    Starting = 'Starting'
    Ready = 'Ready'

@dataclass
class GeoAwarenessTestHarnessStatus: 
    status: Literal[GeoAwarenessStatusResponseEnum.Starting, GeoAwarenessStatusResponseEnum.Ready]
    version:str

@dataclass
class GeoZoneHttpsSource:
    url: str
    format:str 

class GeoAwarenessImportResponseEnum(str, enum.Enum):
    ''' A enum to specify the result of processing of a GeoZone '''
    Activating = 'Activating'
    Ready = 'Ready'
    Deactivating = 'Deactivating'
    Unsupported = 'Unsupported'
    Rejected = 'Rejected'
    Error = 'Error'

@dataclass
class GeoAwarenessTestStatus: 
    result: Literal[GeoAwarenessImportResponseEnum.Activating, GeoAwarenessImportResponseEnum.Ready, GeoAwarenessImportResponseEnum.Deactivating, GeoAwarenessImportResponseEnum.Unsupported, GeoAwarenessImportResponseEnum.Rejected, GeoAwarenessImportResponseEnum.Error]
    message: Optional[str]



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
    horizontalProjection: HorizontalProjection

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
    zoneAuthority: List[ZoneAuthority]
    geometry: List[ED269Geometry]


class GeoZone(ImplicitDict):
    title: str
    description: str
    features: List[GeoZoneFeature]