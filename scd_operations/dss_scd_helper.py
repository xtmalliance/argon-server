import uuid
import redis, json
import requests
import logging
from dataclasses import asdict
from typing import List
from auth_helper import dss_auth_helper
from rid_operations.tasks import submit_dss_subscription
from shapely.ops import unary_union
from shapely.geometry import Point, Polygon, LineString
import shapely.geometry
from pyproj import Proj
from .scd_data_definitions import ImplicitSubscriptionParameters, Volume4D, OperationalIntentReference,DSSOperationalIntentCreateResponse, OperationalIntentReferenceDSSResponse, Time
from os import environ as env
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

class VolumesConverter():
    ''' A class to covert a Volume4D in to GeoJSON '''
    def __init__(self):
        
        self.geo_json = {"type":"FeatureCollection","features":[]}
        self.utm_zone = '54N'
        self.all_volume_features =[]
        
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

    def convert_extents_to_geojson(self, volumes: List[Volume4D]) -> None:
        for volume in volumes:            
            geo_json_features = self._convert_volume_to_geojson_feature(volume)
            self.geo_json['features'] += geo_json_features

    def get_volume_bounds(self)-> List[float]:
        union = unary_union(self.all_volume_features)
        bounds = union.bounds
        
        return list(bounds)


    def _convert_volume_to_geojson_feature(self, volume: Volume4D):
        volume = volume['volume']
        geo_json_features = []
        
        if ('outline_polygon' in volume.keys()):
            outline_polygon = volume['outline_polygon']
            point_list = []
            for vertex in outline_polygon['vertices']:
                p = Point(vertex['lng'], vertex['lat'])
                point_list.append(p)
            outline_polygon = Polygon([[p.x, p.y] for p in point_list])
            self.all_volume_features.append(outline_polygon)
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
            self.all_volume_features.append(converted_circle)
            outline_c = shapely.geometry.mapping(converted_circle)

            circle_feature = {'type': 'Feature', 'properties': {}, 'geometry': outline_c}
            
            geo_json_features.append(circle_feature)
        
        return geo_json_features


class SCDOperations():
    def __init__(self):
        self.dss_base_url = env.get('DSS_BASE_URL')        
        self.r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))  
    
    def create_operational_intent_reference(self, state:str, priority:str, volumes:List[Volume4D], off_nominal_volumes:List[Volume4D]):        
        my_authorization_helper = dss_auth_helper.AuthorityCredentialsGetter()
        audience = env.get("DSS_SELF_AUDIENCE", 0)        
        try: 
            assert audience
        except AssertionError as ae:
            logger.error("Error in getting Authority Access Token DSS_SELF_AUDIENCE is not set in the environment")

        try:
            auth_token = my_authorization_helper.get_cached_credentials(audience= audience, token_type='scd')
        except Exception as e:
            logger.error("Error in getting Authority Access Token %s " % e)            
        else:
            error = auth_token.get("error")            
        
        # A token from authority was received, we can now submit the operational intent
        new_entity_id = str(uuid.uuid4())
        dss_subscription_url = self.dss_base_url + 'dss/v1/operational_intent_references/' + new_entity_id
        headers = {"Content-Type": "application/json", 'Authorization': 'Bearer ' + auth_token['access_token']}
        management_key = str(uuid.uuid4())        
        blender_base_url = env.get("BLENDER_FQDN", 0)
        implicit_subscription_parameters = ImplicitSubscriptionParameters(uss_base_url=blender_base_url)
        operational_intent_reference = OperationalIntentReference(extents = [asdict(volumes[0])], key =[management_key], state = state, uss_base_url = blender_base_url, new_subscription = implicit_subscription_parameters)

        p = json.loads(json.dumps(asdict(operational_intent_reference)))

        try:
            dss_r = requests.put(dss_subscription_url, json =p , headers=headers)
        except Exception as re:
            logger.error("Error in putting operational intent in the DSS %s " % re)
            
        d_r = {}
        
        try: 
            assert dss_r.status_code == 201            
        except AssertionError as ae:              
            logger.error("Error submitting operational intent to the DSS %s" % dss_r.text)            
        else: 	        
            dss_response = dss_r.json()
            subscribers = dss_response['subscribers']
            o_i_r = dss_response['operational_intent_reference']
            time_start = Time(format=o_i_r['time_start']['format'], value=o_i_r['time_start']['value'])
            time_end = Time(format=o_i_r['time_end']['format'], value=o_i_r['time_end']['value'])
            operational_intent_r = OperationalIntentReferenceDSSResponse(id=o_i_r['id'], manager=o_i_r['manager'],uss_availability=o_i_r['uss_availability'], version=o_i_r['version'], state = o_i_r['state'], ovn= o_i_r['ovn'], time_start=time_start, time_end=time_end, uss_base_url=o_i_r['uss_base_url'], subscription_id=o_i_r['subscription_id'])

            dss_creation_response = DSSOperationalIntentCreateResponse(operational_intent_reference=operational_intent_r, subscribers=subscribers)
            logger.success("Successfully created operational intent in the DSS %s" % dss_r.text)
            d_r = asdict(dss_creation_response)
        return d_r
            
        