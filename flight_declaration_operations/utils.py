from scd_operations.scd_data_definitions import Volume4D
import shapely.geometry
from shapely.geometry import Point, Polygon
from pyproj import Proj
from typing import List
import arrow
from shapely.ops import unary_union

class OperationalIntentsConverter():
    ''' A class to covert a operational Intnet  in to GeoJSON '''
    def __init__(self):
        self.geo_json = {"type":"FeatureCollection","features":[]}
        self.utm_zone = '54N'
        self.all_features = []
        self.start_datetime = None
        self.end_datetime = None
        
    def utm_converter(self, shapely_shape: shapely.geometry, inverse:bool=False) -> shapely.geometry.shape:
        ''' A helper function to convert from lat / lon to UTM coordinates for buffering. tracks. This is the UTM projection (https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system), we use Zone 54N which encompasses Japan, this zone has to be set for each locale / city. Adapted from https://gis.stackexchange.com/questions/325926/buffering-geometry-with-points-in-wgs84-using-shapely '''

        proj = Proj(proj="utm", zone=self.utm_zone, ellps="WGS84", datum="WGS84")

        geo_interface = shapely_shape.__geo_interface__
        point_or_polygon = geo_interface['type']
        coordinates = geo_interface['coordinates']
        if point_or_polygon == 'Polygon':
            new_coordinates = [[proj(*point, inverse=inverse) for point in linring] for linring in coordinates]
        elif point_or_polygon == 'Point':
            new_coordinates = proj(*coordinates, inverse=inverse)
        else:
            raise RuntimeError('Unexpected geo_interface type: {}'.format(point_or_polygon))

        return shapely.geometry.shape({'type': point_or_polygon, 'coordinates': tuple(new_coordinates)})

    def convert_operational_intent_to_geo_json(self,extents: List[Volume4D]):
        for extent in extents:
            volume = extent['volume']            
            geo_json_features = self._convert_operational_intent_to_geojson_feature(volume)
            self.geo_json['features'] += geo_json_features

            time_start = arrow.get(extent['time_start']['value'])
            if self.start_datetime:
                self.start_datetime = self.start_datetime if self.start_datetime < time_start else time_start            
            else:
                self.start_datetime = time_start

                
            time_end = arrow.get(extent['time_end']['value'])
            if self.end_datetime:
                self.end_datetime = self.end_datetime if self.end_datetime > time_end else time_end            
            else:
                self.end_datetime = time_end



    def get_geo_json_bounds(self) -> str:
            
        combined_features = unary_union(self.all_features)
        bnd_tuple = combined_features.bounds
        bounds = ''.join(['{:.7f}'.format(x) for x in bnd_tuple])

        return bounds    

    def _convert_operational_intent_to_geojson_feature(self, volume: Volume4D):
        
        geo_json_features = []
        
        if ('outline_polygon' in volume.keys()):
            outline_polygon = volume['outline_polygon']
            point_list = []
            for vertex in outline_polygon['vertices']:
                p = Point(vertex['lng'], vertex['lat'])
                point_list.append(p)
            outline_polygon = Polygon([[p.x, p.y] for p in point_list])
            self.all_features.append(outline_polygon)

            outline_p = shapely.geometry.mapping(outline_polygon)
            polygon_feature = {'type': 'Feature', 'properties': {}, 'geometry': outline_p}
            geo_json_features.append(polygon_feature)

        if ('outline_circle' in volume.keys()):
            outline_circle = volume['outline_circle']
            circle_radius = outline_circle['radius']['value']
            center_point = Point(outline_circle['center']['lng'],outline_circle['center']['lat'])
            utm_center = self.utm_converter(shapely_shape = center_point)
            buffered_cicle = utm_center.buffer(circle_radius)
            converted_circle = self.utm_converter(buffered_cicle, inverse=True)
            self.all_features.append(converted_circle)
            
            outline_c = shapely.geometry.mapping(converted_circle)

            circle_feature = {'type': 'Feature', 'properties': {}, 'geometry': outline_c}
            
            geo_json_features.append(circle_feature)
        
        return geo_json_features
