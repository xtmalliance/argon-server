from dataclasses import dataclass
from typing import List, Optional
from scd_operations.scd_data_definitions import OperationalIntentDetailsUSSResponse
from rid_operations.rid_utils import RIDOperatorDetails
@dataclass
class OperationalIntentNotFoundResponse:
    message:str

@dataclass
class OperationalIntentDetails:
    operational_intent: OperationalIntentDetailsUSSResponse
    
@dataclass
class UpdateOperationalIntent: 
    message:str
    
@dataclass
class GenericErrorResponseMessage:
  message:str

@dataclass
class SummaryFlightsOnly:
  number_of_flights:int


@dataclass
class FlightDetailsNotFoundMessage:
  message:str

@dataclass
class OperatorDetailsSuccessResponse: 
  details:RIDOperatorDetails

@dataclass
class SubscriptionState:
   subscription_id: str
   notification_index: int

@dataclass
class UpdateChangedOpIntDetailsPost:
   operationaal_intent_id: str
   subscriptions: List[SubscriptionState]
   operational_intent: Optional[OperationalIntentDetailsUSSResponse]= None