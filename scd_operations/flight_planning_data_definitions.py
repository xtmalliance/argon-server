import enum
from dataclasses import dataclass


class FlightPlanningStatusResponseEnum(str, enum.Enum):
    """A enum to specify if the USS is ready (or not)"""

    Starting = "Starting"
    Ready = "Ready"


class FlightPlanCloseResultEnum(str, enum.Enum):
    Closed = "Closed"
    Failed = "Failed"


class FlightPlanAdvisoriesEnum(str, enum.Enum):
    Unknown = "Unknown"
    Yes = "Yes"
    No = "No"


class FlightPlanProcessingResultEnum(str, enum.Enum):
    Planned = "Planned"
    ReadyToFly = "ReadyToFly"
    Rejected = "Rejected"
    Failed = "Failed"
    NotSupported = "NotSupported"


@dataclass
class CloseFlightPlanResponse:
    result: FlightPlanCloseResultEnum
    notes: str


@dataclass
class UpsertFlightPlanResponse:
    result: FlightPlanProcessingResultEnum
    notes: str
    includes_advisories: FlightPlanAdvisoriesEnum


@dataclass
class FlightPlanningTestStatus:
    status: FlightPlanningStatusResponseEnum
    system_version: str
    api_name: str
    api_version: str
