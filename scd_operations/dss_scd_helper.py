import uuid
import redis, json
import requests
import logging
from dataclasses import asdict
from typing import List
from auth_helper import dss_auth_helper
from datetime import datetime
from shapely.ops import unary_union
from rid_operations import rtree_helper
from shapely.geometry import Point, Polygon
import shapely.geometry
from pyproj import Proj
from .scd_data_definitions import ImplicitSubscriptionParameters, Volume3D, Volume4D, OperationalIntentReference,OperationalIntentSubmissionSuccess, OperationalIntentReferenceDSSResponse, Time, LatLng, OperationalIntentSubmissionError, OperationalIntentSubmissionStatus, DeleteOperationalIntentConstuctor, CommonDSS4xxResponse,DeleteOperationalIntentResponse, DeleteOperationalIntentResponseSuccess, CommonDSS2xxResponse, QueryOperationalIntentPayload, OperationalIntentDetailsUSSResponse, OperationalIntentUSSDetails, Circle, Altitude, LatLngPoint, Radius
from .scd_data_definitions import Polygon as Plgn
import tldextract
from os import environ as env
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

def is_time_within_time_period(start_time:datetime, end_time:datetime, time_to_check:datetime): 
    if start_time < end_time: 
        return time_to_check >= start_time and time_to_check <= end_time 
    else: 
        #Over midnight: 
        return time_to_check >= start_time or time_to_check <= end_time 

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

    def convert_volumes_to_geojson(self, volumes: List[Volume4D]) -> None:        
        for volume in volumes:                        
            geo_json_features = self._convert_volume_to_geojson_feature(volume)
            self.geo_json['features'] += geo_json_features

    def get_volume_bounds(self)-> List[LatLng]:
        union = unary_union(self.all_volume_features)
        rect_bounds = union.minimum_rotated_rectangle
        g_c = []
        for coord in list(rect_bounds.exterior.coords):
            ll = LatLng(lat = float(coord[1]), lng = float(coord[0]))
            g_c.append(asdict(ll))
        return g_c

    def get_minimum_rotated_rectangle(self)-> Polygon:
        union = unary_union(self.all_volume_features)
        rectangle = union.minimum_rotated_rectangle        
        return rectangle

    def get_bounds(self)-> List[float]:
        union = unary_union(self.all_volume_features)        
        rect_bounds = union.bounds        
        return rect_bounds

    def _convert_volume_to_geojson_feature(self, volume: Volume4D):   

        v = asdict(volume)
        cur_volume = v['volume']
        geo_json_features = []
        
        if ('outline_polygon' in cur_volume.keys()):
            outline_polygon = cur_volume['outline_polygon']
            if outline_polygon:
                point_list = []
                for vertex in outline_polygon['vertices']:
                    p = Point(vertex['lng'], vertex['lat'])
                    point_list.append(p)
                outline_polygon = Polygon([[p.x, p.y] for p in point_list])
                self.all_volume_features.append(outline_polygon)
                outline_p = shapely.geometry.mapping(outline_polygon)
                
                polygon_feature = {'type': 'Feature', 'properties': {}, 'geometry': outline_p}
                geo_json_features.append(polygon_feature)

        if ('outline_circle' in cur_volume.keys()):
            outline_circle = cur_volume['outline_circle']
            if outline_circle:
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
    
    def get_auth_token(self, audience:str=None):
            
        my_authorization_helper = dss_auth_helper.AuthorityCredentialsGetter()
        if audience is None:
            audience = env.get("DSS_SELF_AUDIENCE", 0)        
        try: 
            assert audience
        except AssertionError as ae:
            logger.error("Error in getting Authority Access Token DSS_SELF_AUDIENCE is not set in the environment")
        auth_token = {}
        try:
            auth_token = my_authorization_helper.get_cached_credentials(audience= audience, token_type='scd')
        except Exception as e:
            logger.error("Error in getting Authority Access Token %s " % e)           
            auth_token['error'] = "Error in getting access token {error}".format(error = e)
        else:
            error = auth_token.get("error", None)     
            if error:        
                logger.error("Authority server provided the following error during token request %s " % error)       
        
        return auth_token


    def delete_operational_intent(self, operational_intent_id:uuid.uuid4, ovn:str):
        auth_token = self.get_auth_token()
        
        dss_opint_delete_url = self.dss_base_url + 'dss/v1/operational_intent_references/' + operational_intent_id + '/'+ ovn
        
        headers = {"Content-Type": "application/json", 'Authorization': 'Bearer ' + auth_token['access_token']}
        delete_payload = DeleteOperationalIntentConstuctor(entity_id= operational_intent_id, ovn = ovn)

        dss_r = requests.delete(dss_opint_delete_url, json =json.loads(json.dumps(asdict(delete_payload))), headers=headers)
        
        dss_response = dss_r.json()
        dss_r_status_code = dss_r.status_code

        if dss_r_status_code == 200:
            common_200_response = CommonDSS2xxResponse(message="Successfully deleted operational intent id %s" % operational_intent_id)
            dss_response_formatted = DeleteOperationalIntentResponseSuccess(subscribers= dss_response["subscribers"],operational_intent_reference=dss_response['operational_intent_reference'])
            delete_op_int_status = DeleteOperationalIntentResponse(dss_response=dss_response_formatted, status =200, message= common_200_response)
        elif dss_r_status_code == 404:
            
            common_400_response = CommonDSS4xxResponse(message="URL endpoint not found")
            delete_op_int_status = DeleteOperationalIntentResponse(dss_response=  dss_response, status = 404,message=common_400_response)

        elif dss_r_status_code == 409:
            common_400_response = CommonDSS4xxResponse(message="The provided ovn does not match the current version of existing operational intent")
            delete_op_int_status = DeleteOperationalIntentResponse(dss_response=  dss_response, status = 409,message=common_400_response)

        elif dss_r_status_code == 412:
            common_400_response = CommonDSS4xxResponse(message="The client attempted to delete the operational intent while marked as Down in the DSS")
            delete_op_int_status = DeleteOperationalIntentResponse(dss_response=  dss_response, status = 412,message=common_400_response)
        else:
            common_400_response = CommonDSS4xxResponse(message="A errror occured while deleting the operational intent")
            delete_op_int_status = DeleteOperationalIntentResponse(dss_response=  dss_response, status = 500,message=common_400_response)
        return delete_op_int_status

    def check_volumes_for_conflicts(self, volumes:List[Volume4D])->bool:
        # This method checks if a flight volume has conflicts with any other volume in the airspace
        auth_token = self.get_auth_token()
        # Query the DSS for operational intentns
        query_op_int_url = self.dss_base_url + 'dss/v1/operational_intent_references/query'
        headers = {"Content-Type": "application/json", 'Authorization': 'Bearer ' + auth_token['access_token']}

        for volume in volumes: 
            operational_intent_references = []
            area_of_interest = QueryOperationalIntentPayload(area_of_interest=volume)
            logging.info("Querying DSS for operational intents in the area..")
            try:
                operational_intent_ref_response = requests.post(query_op_int_url, json =json.loads(json.dumps(asdict(area_of_interest))) , headers=headers)
            except Exception as re:
                logger.error("Error in getting operational intent for the volume %s " % re)            
            else:                    
                dss_operational_intent_references = operational_intent_ref_response.json()
                
            operational_intent_references = dss_operational_intent_references['operational_intent_references']

            if operational_intent_references:
                logger.info("{num_intents} existing operational intent references found in the area".format(num_intents = len(operational_intent_references)))
            else:
                logger.info("No operational intent references found in the area")
            # Query the operational intent reference 
            all_opints_to_check = []
            all_uss_operational_intent_details = []
            
            for operational_intent_reference_detail in operational_intent_references:
                # Get the USS URL endpoint              
                dss_op_int_details_url = self.dss_base_url + 'dss/v1/operational_intent_references/' + operational_intent_reference_detail['id']
                # get new auth token for USS 
                try:
                    op_int_uss_details = requests.get(dss_op_int_details_url, headers=headers)
                except Exception as e: 
                    logger.error("Error in getting operational intent details %s" % e)
                else:
                    operational_intent_reference = op_int_uss_details.json()
                    o_i_r = operational_intent_reference['operational_intent_reference']
                    o_i_r_formatted = OperationalIntentReferenceDSSResponse(id= o_i_r['id'], manager=o_i_r['manager'], uss_availability=o_i_r['uss_availability'], version= o_i_r['version'],state = o_i_r['state'], ovn = o_i_r['ovn'], time_start=o_i_r['time_start'], time_end=o_i_r['time_end'], uss_base_url= o_i_r['uss_base_url'], subscription_id= o_i_r['subscription_id'] )
                    all_uss_operational_intent_details.append(o_i_r_formatted)


            for current_uss_operational_intent_detail in all_uss_operational_intent_details:
                # check the USS for flight volume                    
                try:
                    ext = tldextract.extract(current_uss_operational_intent_detail.uss_base_url)  
                except Exception as e: 
                    uss_audience = 'localhost'
                else:
                    if ext.domain in ['localhost', 'internal']:# for host.docker.internal type calls
                        uss_audience = 'localhost'
                    else:
                        uss_audience = '.'.join(ext[:3]) # get the subdomain, domain and suffix and create a audience and get credentials
                
                uss_auth_token = self.get_auth_token(audience = uss_audience)          
                
                uss_headers = {"Content-Type": "application/json", 'Authorization': 'Bearer ' + uss_auth_token['access_token']}
                uss_operational_intent_url = current_uss_operational_intent_detail.uss_base_url + '/uss/v1/operational_intents/'+ current_uss_operational_intent_detail.id
                
                try:
                    uss_operational_intent_request = requests.get(uss_operational_intent_url, headers=uss_headers)
                except Exception as e:                     
                    logger.error("Error in getting operational intent id {uss_op_int_id} details from uss".format(uss_op_int_id= current_uss_operational_intent_detail.id))
                    logger.error("Error details %s " % e)
                else:
                    operational_intent_details_json = uss_operational_intent_request.json()
                    
                    if uss_operational_intent_request.status_code ==200:

                        outline_polygon = None
                        outline_circle = None

                        op_int_det = operational_intent_details_json['operational_intent']['details']
                        op_int_ref = operational_intent_details_json['operational_intent']['reference']

                        all_volumes = op_int_det['volumes']
                        all_v4d = []
                        for cur_volume in all_volumes:

                            if 'outline_polygon' in cur_volume['volume'].keys():
                                all_vertices = cur_volume['volume']['outline_polygon']['vertices']
                                polygon_verticies = []
                                for vertex in all_vertices:
                                    v = LatLngPoint(lat = vertex['lat'],lng=vertex['lng'])
                                    polygon_verticies.append(v)

                                outline_polygon = Plgn(vertices=polygon_verticies)

                            if 'outline_circle' in cur_volume['volume'].keys():                
                                circle_center =  LatLngPoint(lat = cur_volume['volume']['outline_circle']['center']['lat'], lng = cur_volume['volume']['outline_circle']['center']['lng'])
                                circle_radius = Radius(value =cur_volume['volume']['outline_circle']['radius']['value'], units = cur_volume['volume']['outline_circle']['radius']['units'])
                                                
                                outline_circle = Circle(center =circle_center, radius=circle_radius)
                                
                            altitude_lower = Altitude(value = cur_volume['volume']['altitude_lower']['value'],reference= cur_volume['volume']['altitude_lower']['reference'], units =cur_volume['volume']['altitude_lower']['units'] )
                            altitude_upper = Altitude(value = cur_volume['volume']['altitude_upper']['value'],reference=  cur_volume['volume']['altitude_upper']['reference'], units =cur_volume['volume']['altitude_upper']['units'] )                        
                            volume3D = Volume3D(outline_circle=outline_circle, outline_polygon=outline_polygon, altitude_lower = altitude_lower, altitude_upper= altitude_upper)
                         
                         
                            time_start = Time(format = cur_volume['time_start']['format'], value = cur_volume['time_start']['value'])
                            time_end = Time(format =cur_volume['time_end']['format'] , value = cur_volume['time_end']['value'])

                            cur_v4d = Volume4D(volume=volume3D, time_start=time_start, time_end=time_end)

                            all_v4d.append(cur_v4d)

                        op_int_detail = OperationalIntentUSSDetails(volumes =all_v4d, priority = op_int_det['priority'], off_nominal_volumes =  op_int_det['off_nominal_volumes'])

                        time_start = Time(format=op_int_ref['time_start']['format'], value= op_int_ref['time_start']['value'] )
                        
                        time_end = Time(format=op_int_ref['time_end']['format'], value= op_int_ref['time_end']['value'] )

                        op_int_reference = OperationalIntentReferenceDSSResponse(id = op_int_ref['id'], uss_availability =  op_int_ref['uss_availability'], manager= op_int_ref['manager'], version = op_int_ref['version'], state = op_int_ref['state'], ovn = op_int_ref['ovn'], time_start=time_start, time_end=time_end, uss_base_url= op_int_ref['uss_base_url'], subscription_id=op_int_ref['subscription_id'])


                        uss_op_int_details = OperationalIntentDetailsUSSResponse(reference=op_int_reference, details=op_int_detail)

                        operational_intent_volumes = op_int_detail.volumes
                        my_volume_converter = VolumesConverter()
                        
                        my_volume_converter.convert_volumes_to_geojson(volumes = operational_intent_volumes)                    
                        minimum_rotated_rect = my_volume_converter.get_minimum_rotated_rectangle()
                        all_opints_to_check.append(minimum_rotated_rect)

                    else:
                        logger.error("Could not retrieve flight details from USS %s" % uss_operational_intent_request.json())   
                        
        if all_uss_operational_intent_details:
            logging.info("Checking deconfliction status with {num_existing_op_ints} operational intent details".format(num_existing_op_ints = len(all_opints_to_check)))            
            my_ind_volumes_converter = VolumesConverter()
            my_ind_volumes_converter.convert_volumes_to_geojson(volumes = volumes)
            ind_volumes_polygon = my_ind_volumes_converter.get_minimum_rotated_rectangle()

            is_conflicted = rtree_helper.check_polygon_intersection(polygons = all_opints_to_check, polygon_to_check=ind_volumes_polygon)
            deconflicted = False if is_conflicted else True
        else:
            deconflicted = True
            logging.info("No existing operational intents in the DSS, deconfliction status: %s" % deconflicted)
        
        logging.info("Deconfliction status: %s" % deconflicted)
        
        return deconflicted


    def create_operational_intent_reference(self, state:str, priority:str, volumes:List[Volume4D], off_nominal_volumes:List[Volume4D]):        
        auth_token = self.get_auth_token()
        # A token from authority was received, we can now submit the operational intent
        new_entity_id = str(uuid.uuid4())
        dss_subscription_url = self.dss_base_url + 'dss/v1/operational_intent_references/' + new_entity_id
        headers = {"Content-Type": "application/json", 'Authorization': 'Bearer ' + auth_token['access_token']}
        management_key = str(uuid.uuid4())        
        blender_base_url = env.get("BLENDER_FQDN", 0) +'/uss'
        implicit_subscription_parameters = ImplicitSubscriptionParameters(uss_base_url=blender_base_url)
        operational_intent_reference = OperationalIntentReference(extents = volumes, key =[management_key], state = state, uss_base_url = blender_base_url, new_subscription = implicit_subscription_parameters)
        p = json.loads(json.dumps(asdict(operational_intent_reference)))     
        d_r = OperationalIntentSubmissionStatus(status = "not started", status_code = 503, message = "Service is not available / connection not established", dss_response ={}, operational_intent_id = new_entity_id)
        # Query other USSes for operational intent 
        # Check if there are conflicts (or not)
        logging.info("Checking flight deconfliction status")
        if (priority != 100):
            deconflicted = self.check_volumes_for_conflicts(volumes =volumes)
        else:
            deconflicted = True
        logging.info("Flight deconfliction status checked")
        if deconflicted:
            try:
                dss_r = requests.put(dss_subscription_url, json = p , headers=headers)
            except Exception as re:
                logger.error("Error in putting operational intent in the DSS %s " % re)            
                d_r = OperationalIntentSubmissionStatus(status = "failure", status_code = 500, message = re, dss_response={}, operational_intent_id = new_entity_id)
                dss_r_status_code = d_r.status_code
            else:                    
                dss_response = dss_r.json()
                dss_r_status_code = dss_r.status_code
            
            if dss_r_status_code in [200,201]:
                subscribers = dss_response['subscribers']
                o_i_r = dss_response['operational_intent_reference']
                time_start = Time(format=o_i_r['time_start']['format'], value=o_i_r['time_start']['value'])
                time_end = Time(format=o_i_r['time_end']['format'], value=o_i_r['time_end']['value'])
                operational_intent_r = OperationalIntentReferenceDSSResponse(id=o_i_r['id'], manager=o_i_r['manager'],uss_availability=o_i_r['uss_availability'], version=o_i_r['version'], state = o_i_r['state'], ovn= o_i_r['ovn'], time_start=time_start, time_end=time_end, uss_base_url=o_i_r['uss_base_url'], subscription_id=o_i_r['subscription_id'])
                dss_creation_response = OperationalIntentSubmissionSuccess(operational_intent_reference = operational_intent_r, subscribers = subscribers)
                logger.info("Successfully created operational intent in the DSS")
                logger.debug("Response details from the DSS %s" % dss_r.text)
                d_r = OperationalIntentSubmissionStatus(status = "success", status_code = 201, message= "Successfully created operational intent in the DSS", dss_response = dss_creation_response, operational_intent_id = new_entity_id)
            elif dss_r_status_code == 409:            
                dss_creation_response_error = OperationalIntentSubmissionError(status = "failure", result = dss_response["result"], notes = dss_response["notes"])
                logger.error("DSS operational creation error %s" % dss_r.text)
                d_r = OperationalIntentSubmissionStatus(status = "failure", status_code= 409, message= dss_r.text, dss_response = dss_creation_response_error, operational_intent_id = new_entity_id)
                
            else:
                d_r.status_code = dss_r_status_code
                logger.error("Error submitting operational intent to the DSS: %s" % asdict(d_r))
        else:        
            logger.info("Flight not deconflicted, there are other flights in the area")            
            d_r = OperationalIntentSubmissionStatus(status = "conflict_with_flight", status_code = 500, message = "Flight not deconflicted, there are other flights in the area", dss_response={}, operational_intent_id = new_entity_id)

        return d_r