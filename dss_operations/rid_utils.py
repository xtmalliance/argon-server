from typing import List, NamedTuple


class Position(NamedTuple):
    ''' A class to hold most recent position for remote id data '''
    lat:float
    lng:float
    alt:float


class RIDPositions(NamedTuple):
    ''' A list of positions '''
    positions: List[Position]


class RIDFlight(NamedTuple):    
    id:str
    most_recent_position: Position
    recent_paths: RIDPositions

class ClusterDetails(NamedTuple):
    corners:List[Position]
    area_sqm: float
    number_of_flights: float


class RIDDisplayDataResponse(NamedTuple):
    flights: List[RIDFlight]
    clusters: List[ClusterDetails]