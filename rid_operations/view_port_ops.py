from math import atan2, cos, radians, sin, sqrt

import shapely
from pyproj import Geod
from shapely.geometry import box


def build_view_port_box(view_port_coords) -> box:
    box = shapely.geometry.box(
        view_port_coords[0],
        view_port_coords[1],
        view_port_coords[2],
        view_port_coords[3],
    )
    return box


def get_view_port_area(view_box: box) -> int:
    geod = Geod(ellps="WGS84")
    area = abs(geod.geometry_area_perimeter(view_box)[0])
    return area


def get_view_port_diagonal_length_kms(view_port_coords) -> float:
    # Source: https://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude
    R = 6373.0

    lat1 = radians(min(view_port_coords[0], view_port_coords[2]))
    lon1 = radians(min(view_port_coords[1], view_port_coords[3]))
    lat2 = radians(max(view_port_coords[0], view_port_coords[2]))
    lon2 = radians(max(view_port_coords[1], view_port_coords[3]))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    diagonal_distance = R * c
    return diagonal_distance


def check_view_port(view_port_coords) -> bool:
    if len(view_port_coords) != 4:
        return False
        # return '"view" argument contains the wrong number of coordinates (expected 4, found {})'.format(len(view_port)), 400

    lat_min = min(view_port_coords[0], view_port_coords[2])
    lat_max = max(view_port_coords[0], view_port_coords[2])
    lng_min = min(view_port_coords[1], view_port_coords[3])
    lng_max = max(view_port_coords[1], view_port_coords[3])

    if lat_min < -90 or lat_min >= 90 or lat_max <= -90 or lat_max > 90 or lng_min < -180 or lng_min >= 360 or lng_max <= -180 or lng_max > 360:
        # return '"view" coordinates do not fall within the valid range of -90 <= lat <= 90 and -180 <= lng <= 360', 400
        return False
    else:
        return True


# def get_view_port_area(view_port) -> float:
#     geod = Geod(ellps="WGS84")
#     box = shapely.geometry.box(view_port[0], view_port[1], view_port[2], view_port[3])
#     area = abs(geod.geometry_area_perimeter(box)[0])
#     return area
