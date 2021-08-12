from requests.adapters import HTTPResponse
from auth_helper.utils import requires_scopes
import json
from pyproj import Geod
from django.http import HttpResponse
from rest_framework.decorators import api_view
from . import dss_rw_helper
from os import environ as env
import uuid
import shapely.geometry
import uuid
import redis
from .rid_utils import RIDDisplayDataResponse, Position, RIDPositions, RIDFlight, CreateSubscriptionResponse
import hashlib
from flight_feed_operations import flight_stream_helper
from uuid import UUID
import logging
from typing import Any

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
logger = logging.getLogger('django')

class RIDOutputHelper():
        
    def make_json_compatible(self, struct: Any) -> Any:
        if isinstance(struct, tuple) and hasattr(struct, '_asdict'):
            return {k: self.make_json_compatible(v) for k, v in struct._asdict().items()}
        elif isinstance(struct, dict):
            return {k: self.make_json_compatible(v) for k, v in struct.items()}
        elif isinstance(struct, str):
            return struct
        try:
            return [self.make_json_compatible(v) for v in struct]
        except TypeError:
            return struct



class SubscriptionHelper():
    """
    A class to help with DSS subscriptions, check if a subscription exists or create a new one  

    """
    def __init__(self):
        
        self.my_rid_output_helper = RIDOutputHelper()

    def check_subscription_exists(self, view) -> bool:
        r = redis.Redis(host=env.get('REDIS_HOST', "redis"), port=env.get('REDIS_PORT', 6379), decode_responses=True)
        subscription_found = False
        view_hash = int(hashlib.sha256(view.encode('utf-8')).hexdigest(), 16) % 10**8
        view_sub = 'view_sub-'+ str(view_hash)
        subscription_found = r.exists(view_sub)        
        return subscription_found

    def create_new_subscription(self, request_id, view:str, vertex_list:list):
        subscription_time_delta = 15        
        myDSSubscriber = dss_rw_helper.RemoteIDOperations()        
        subscription_r = myDSSubscriber.create_dss_subscription(vertex_list=vertex_list, view=view, request_uuid=request_id, subscription_time_delta = subscription_time_delta)      
        subscription_response = self.my_rid_output_helper.make_json_compatible(subscription_r)
        return subscription_response


def check_view_port(view_port) -> bool:

    geod = Geod(ellps="WGS84")
    if len(view_port) != 4:
        return False
        # return '"view" argument contains the wrong number of coordinates (expected 4, found {})'.format(len(view_port)), 400

    lat_min = min(view_port[0], view_port[2])
    lat_max = max(view_port[0], view_port[2])
    lng_min = min(view_port[1], view_port[3])
    lng_max = max(view_port[1], view_port[3])

    if (lat_min < -90 or lat_min >= 90 or lat_max <= -90 or lat_max > 90 or lng_min < -180 or lng_min >= 360 or lng_max <= -180 or lng_max > 360):
        # return '"view" coordinates do not fall within the valid range of -90 <= lat <= 90 and -180 <= lng <= 360', 400
        return False

    box = shapely.geometry.box(view_port[0], view_port[1], view_port[2], view_port[3])
    area = abs(geod.geometry_area_perimeter(box)[0])
    
    if (area) < 250000 and (area) > 90000:
        return False

    return True


@api_view(['PUT'])
@requires_scopes(['blender.write'])
def create_dss_subscription(request, *args, **kwargs):

    ''' This module takes a lat, lng box from Flight Spotlight and puts in a subscription to the DSS for the ISA '''
    
    my_rid_output_helper = RIDOutputHelper()
    try:
        view = request.query_params['view']
        view_port = [float(i) for i in view.split(",")]
    except Exception as ke:
        incorrect_parameters = {"message": "A view bbox is necessary with four values: minx, miny, maxx and maxy"}
        return HttpResponse(json.dumps(incorrect_parameters), status=400)

    view_port_valid = check_view_port(view_port=view_port)

    if not view_port_valid:
        incorrect_parameters = {"message": "A view bbox is necessary with four values: minx, miny, maxx and maxy"}
        return HttpResponse(json.dumps(incorrect_parameters), status=400)

    b = shapely.geometry.box(view_port[1], view_port[0], view_port[3], view_port[2])
    co_ordinates = list(zip(*b.exterior.coords.xy))
    
    # Convert bounds vertex list
    vertex_list = []
    for cur_co_ordinate in co_ordinates:
        lat_lng = {"lng": 0, "lat": 0}
        lat_lng["lng"] = cur_co_ordinate[0]
        lat_lng["lat"] = cur_co_ordinate[1]
        vertex_list.append(lat_lng)
    # remove the final point
    vertex_list.pop()
    
    request_id = str(uuid.uuid4())
    # TODO: Make this a asnyc call
    my_subscription_helper = SubscriptionHelper()
    subscription_r = my_subscription_helper.create_new_subscription(request_id=request_id, vertex_list=vertex_list, view=view)
    
    if subscription_r.created:
        m = CreateSubscriptionResponse(message= "DSS Subscription created",id=request_id, dss_subscription_response= subscription_r)

        status = 201
    else:
        m = CreateSubscriptionResponse(message= "Error in creating DSS Subscription, please check the log or contact your administrator.",id=request_id, dss_subscription_response= subscription_r)
        m = {"message": "Error in creating DSS Subscription, please check the log or contact your administrator.", 'id': request_id}
        status = 400
    msg = my_rid_output_helper.make_json_compatible(m)
    return HttpResponse(json.dumps(msg), status=status, content_type='application/json')


@api_view(['GET'])
@requires_scopes(['blender.read'])
def get_rid_data(request, subscription_id):
    ''' This is the GET endpoint for remote id data given a DSS subscription id. Blender will store flight URLs and everytime the data is queried'''

    try:
        is_uuid = UUID(subscription_id, version=4)
    except ValueError as ve:
        return HttpResponse("Incorrect UUID passed in the parameters, please send a valid subscription ID", status=400, mimetype='application/json')

    r = redis.Redis(host=env.get('REDIS_HOST', "redis"), port=env.get('REDIS_PORT', 6379), charset="utf-8", decode_responses=True)
    flights_dict = {}
    # Get the flights URL from the DSS and put it in
    # reasonably we wont have more than 500 subscriptions active
    sub_to_check = 'sub-' + subscription_id

    if r.exists(sub_to_check):
        stored_subscription_details = "all_uss_flights:"+ subscription_id
        flights_dict = r.get(stored_subscription_details)


    if bool(flights_dict):
        # TODO for Pull operations Flights Dict is not being used at all
        all_flights_rid_data = []
        stream_ops = flight_stream_helper.StreamHelperOps()
        push_cg = stream_ops.push_cg()
        obs_helper = flight_stream_helper.ObservationReadOperations()
        all_flights_rid_data = obs_helper.get_observations(push_cg)

        return HTTPResponse(json.dumps(all_flights_rid_data), status=200, content_type='application/json')
    else:
        return HTTPResponse(json.dumps({}), status=404, content_type='application/json')


@api_view(['POST'])
@requires_scopes(['dss.write.identification_service_areas'])
def dss_isa_callback(request, subscription_id):
    ''' This is the call back end point that other USSes in the DSS network call once a subscription is updated '''
    service_areas = request.get('service_area', 0)
    
    try:
        assert service_areas != 0
        r = redis.Redis(host=env.get('REDIS_HOST', "redis"), port=env.get(
            'REDIS_PORT', 6379), decode_responses=True)
        # Get the flights URL from the DSS and put it in the flights_url
        flights_key = "all_uss_flights:" + subscription_id
        subscription_view_key = "sub-" + subscription_id        

        flights_dict = r.hgetall(flights_key)
        
        subscription_view = r.get(subscription_view_key)
        

        all_flights_url = flights_dict['all_flights_url']
        logging.info(all_flights_url)
        for new_flight in service_areas:
            all_flights_url += new_flight['flights_url'] + \
                '?view=' + subscription_view + " "

        flights_dict["all_uss_flights"] = all_flights_url
        r.hmset(flights_key, flights_dict)
        r.expire(name = flights_key, time=30)# if a AOI is updated then keep the subscription active for 30 seconds

    except AssertionError as ae:
        return HttpResponse("Incorrect data in the POST URL", status=400, content_type='application/json')

    else:
        # All OK return a empty response
        return HttpResponse(status=204, content_type='application/json')


@api_view(['GET'])
@requires_scopes(['dss.read.identification_service_areas'])
def get_display_data(request):
    ''' This is the end point for the rid_qualifier test DSS network call once a subscription is updated '''

    # get the view bounding box
    # get the existing subscription id , if no subscription exists, then reject
    request_id = str(uuid.uuid4())
    my_rid_output_helper = RIDOutputHelper()
    try:
        view = request.query_params['view']
        view_port = [float(i) for i in view.split(",")]
    except Exception as ke:
        incorrect_parameters = {"message": "A view bbox is necessary with four values: minx, miny, maxx and maxy"}
        return HttpResponse(json.dumps(incorrect_parameters), status=400, content_type='application/json')
    view_port_valid = check_view_port(view_port=view_port)

    b = shapely.geometry.box(view_port[1], view_port[0], view_port[3], view_port[2])
    co_ordinates = list(zip(*b.exterior.coords.xy))
    # Convert bounds vertex list
    vertex_list = []
    for cur_co_ordinate in co_ordinates:
        lat_lng = {"lng": 0, "lat": 0}
        lat_lng["lng"] = cur_co_ordinate[0]
        lat_lng["lat"] = cur_co_ordinate[1]
        vertex_list.append(lat_lng)
    # remove the final point
    vertex_list.pop()

    if view_port_valid:
        # stream_id = hashlib.md5(view.encode('utf-8')).hexdigest()
        # create a subscription
        my_subscription_helper = SubscriptionHelper()
        subscription_exists = my_subscription_helper.check_subscription_exists(view)        
        if not subscription_exists:
            logger.info("Creating Subscription..")
            subscription_response = my_subscription_helper.create_new_subscription(request_id=request_id, vertex_list=vertex_list, view= view)
            logger.debug(subscription_response)

        # TODO: Get existing flight details from subscription
        stream_ops = flight_stream_helper.StreamHelperOps()
        pull_cg = stream_ops.get_pull_cg()
        all_streams_messages = pull_cg.read()

        unique_flights =[]
        # Keep only the latest message
        try:
            for message in all_streams_messages:          
                unique_flights.append({'timestamp': message.timestamp,'seq': message.sequence, 'msg_data':message.data, 'address':message.data['icao_address']})
            
            # sort by date
            unique_flights.sort(key=lambda item:item['timestamp'], reverse=True)
            # Keep only the latest message
            distinct_messages = {i['address']:i for i in reversed(unique_flights)}.values()
            
        except KeyError as ke: 
            logger.error("Error in sorting distinct messages, ICAO name not defined")                     
            distinct_messages = []
        rid_flights = []
        
        for all_observations_messages in distinct_messages:                   
            all_recent_positions = []
            recent_paths = []
            try:
                observation_data = all_observations_messages['msg_data']                
            except KeyError as ke:
                logger.error("Error in data in the stream %s" % ke)                
            else:
                try:                
                    observation_metadata = observation_data['metadata']
                    observation_metadata_dict = json.loads(observation_metadata)
                    recent_positions = observation_metadata_dict['recent_positions']

                    for recent_position in recent_positions:    
                        all_recent_positions.append(Position(lat=recent_position['position']['lat'], lng= recent_position['position']['lng'], alt = recent_position['position']['alt']))

                    recent_paths.append(RIDPositions(positions = all_recent_positions))
                    
                except KeyError as ke:
                    logger.error("Error in metadata data in the stream %s" % ke)
                    

            most_recent_position = Position(lat=observation_data['lat_dd'], lng=observation_data['lon_dd'] ,alt= observation_data['altitude_mm'])

            current_flight = RIDFlight(id=observation_data['icao_address'], most_recent_position= most_recent_position,recent_paths = recent_paths)


            rid_flights.append(current_flight)

        
        rid_display_data = RIDDisplayDataResponse(flights=rid_flights, clusters = [])
        
        rid_flights_dict = my_rid_output_helper.make_json_compatible(rid_display_data)
        
        return HttpResponse(json.dumps({"flights":rid_flights_dict['flights'], "clusters": rid_flights_dict['clusters']}),  status=200, content_type='application/json')
    else:
        view_port_error = {
            "message": "A incorrect view port bbox was provided"}
        return HttpResponse(json.dumps(view_port_error), status=400, content_type='application/json')


@api_view(['GET'])
@requires_scopes(['dss.read.identification_service_areas'])
def get_flight_data(request, flight_id):
    ''' This is the end point for the rid_qualifier to get details of a flight '''

    # get the flight ID
    # query the /uss/flights/{id}/details with the ID (should return the RID details / https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/uastech/standards/master/remoteid/canonical.yaml#tag/p2p_rid/paths/~1v1~1uss~1flights~1{id}~1details/get
    # {
    # "details": {
    #     "id": "a3423b-213401-0023",
    #     "operator_id": "string",
    #     "operator_location": {
    #     "lng": -118.456,
    #     "lat": 34.123
    #     },
    #     "operation_description": "SafeFlightDrone company doing survey with DJI Inspire 2. See my privacy policy www.example.com/privacy.",
    #     "auth_data": {
    #     "format": "string",
    #     "data": "string"
    #     },
    #     "serial_number": "INTCJ123-4567-890",
    #     "registration_number": "FA12345897"
    # }
    # }

    return HttpResponse(json.dumps({"details": {}}), mimetype='application/json')
