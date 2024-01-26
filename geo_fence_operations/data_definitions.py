import enum
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Union

from implicitdict import ImplicitDict


class GeoAwarenessStatusResponseEnum(str, enum.Enum):
    """A enum to specify if the USS is ready (or not)"""

    Starting = "Starting"
    Ready = "Ready"


@dataclass
class GeoAwarenessTestHarnessStatus:
    status: Literal[GeoAwarenessStatusResponseEnum.Starting, GeoAwarenessStatusResponseEnum.Ready]
    version: str


class HTTPSSource(ImplicitDict):
    url: str
    format: str


class GeoZoneHttpsSource(ImplicitDict):
    https_source: HTTPSSource


class GeoAwarenessRestrictions(str, enum.Enum):
    """A enum to specify the result of processing of a GeoZone"""

    PROHIBITED = "PROHIBITED"
    REQ_AUTHORISATION = "REQ_AUTHORISATION"
    CONDITIONAL = "CONDITIONAL"
    NO_RESTRICTION = "NO_RESTRICTION"


class GeozoneCheckResultEnum(str, enum.Enum):
    """A enum to specify the result of processing of a GeoZone"""

    Present = "Present"
    Absent = "Absent"
    UnsupportedFilter = "UnsupportedFilter"
    Error = "Error"


class GeoAwarenessImportResponseEnum(str, enum.Enum):
    """A enum to specify the result of processing of a GeoZone"""

    Activating = "Activating"
    Ready = "Ready"
    Deactivating = "Deactivating"
    Unsupported = "Unsupported"
    Rejected = "Rejected"
    Error = "Error"


@dataclass
class GeoAwarenessTestStatus:
    result: Literal[
        GeoAwarenessImportResponseEnum.Activating,
        GeoAwarenessImportResponseEnum.Ready,
        GeoAwarenessImportResponseEnum.Deactivating,
        GeoAwarenessImportResponseEnum.Unsupported,
        GeoAwarenessImportResponseEnum.Rejected,
        GeoAwarenessImportResponseEnum.Error,
    ]
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


@dataclass
class ParseValidateResponse:
    all_zones: List[bool]
    feature_list: Union[None, List[GeoZoneFeature]]


class GeoZone(ImplicitDict):
    title: str
    description: str
    features: List[GeoZoneFeature]


class GeoZoneFilterPosition(ImplicitDict):
    uomDimensions: str
    verticalReferenceType: str
    height: int
    longitude: float
    latitude: float


class ED269Filter(ImplicitDict):
    uSpaceClass: str
    acceptableRestrictions: Literal[
        GeoAwarenessRestrictions.PROHIBITED,
        GeoAwarenessRestrictions.REQ_AUTHORISATION,
        GeoAwarenessRestrictions.CONDITIONAL,
        GeoAwarenessRestrictions.NO_RESTRICTION,
    ]


class GeoZoneFilterSet(ImplicitDict):
    position: Optional[GeoZoneFilterPosition]
    after: Optional[str]
    before: Optional[str]
    ed269: List[ED269Filter]


class GeozonesCheck(ImplicitDict):
    filterSets: List[GeoZoneFilterSet]


class GeoZoneCheckRequestBody(ImplicitDict):
    checks: List[GeozonesCheck]


@dataclass
class GeoZoneCheckResult:
    geozone: Literal[
        GeozoneCheckResultEnum.Present,
        GeozoneCheckResultEnum.Present,
        GeozoneCheckResultEnum.UnsupportedFilter,
        GeozoneCheckResultEnum.Error,
    ]


@dataclass
class GeoZoneChecksResponse:
    applicableGeozone: List[GeoZoneCheckResult]
    message: str
