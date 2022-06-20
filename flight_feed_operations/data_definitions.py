from dataclasses import dataclass
from typing import Optional

@dataclass
class RIDMetadata():
    ''' A class to store RemoteID metadata '''
    aircraft_type: str

@dataclass
class SingleRIDObservation():
    ''' This is the object stores details of the obervation  '''
    lat_dd: float
    lon_dd: float
    altitude_mm: float
    traffic_source: int
    source_type:int
    icao_address: str
    metadata: RIDMetadata

@dataclass
class SingleAirtrafficObervation():
    ''' This is the object stores details of the obervation  '''
    lat_dd: float
    lon_dd: float
    altitude_mm: float
    traffic_source: int
    source_type:int
    icao_address: str
    metadata: Optional[dict]

@dataclass 
class FlightObservationsProcessingResponse():
    message:str
    status: int
