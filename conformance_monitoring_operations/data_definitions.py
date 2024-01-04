from dataclasses import dataclass

from shapely.geometry import Polygon


@dataclass
class PolygonAltitude:
    polygon: Polygon
    altitude_upper: float
    altitude_lower: float
