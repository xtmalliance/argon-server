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
from datetime import datetime, timedelta
import redis
from flight_feed_operations import flight_stream_helper
from uuid import UUID
import logging
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def create_new_subscription(request_id, view, vertex_list):
    r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))  
    myDSSubscriber = dss_rw_helper.RemoteIDOperations()
    subscription_respone = myDSSubscriber.create_dss_subscription(vertex_list = vertex_list, view = view, request_uuid = request_id)
    
    if subscription_respone['created']:
        sub_id = 'sub-' + request_id
        view_details = view
        r.set(sub_id , view_details)
        r.expire(sub_id, timedelta(minutes=3))

    return subscription_respone

def check_view_port(view_port) -> bool:
    geod = Geod(ellps="WGS84")
    if len(view_port) != 4:
        return False
        # return '"view" argument contains the wrong number of coordinates (expected 4, found {})'.format(len(view_port)), 400

    lat_min = min(view_port[0], view_port[2])
    lat_max = max(view_port[0], view_port[2])
    lng_min = min(view_port[1], view_port[3])
    lng_max = max(view_port[1], view_port[3])

    if (lat_min < -90 or lat_min >= 90 or lat_max <= -90 or lat_max > 90 or
        lng_min < -180 or lng_min >= 360 or lng_max <= -180 or lng_max > 360):
        # return '"view" coordinates do not fall within the valid range of -90 <= lat <= 90 and -180 <= lng <= 360', 400
        return False

    box = shapely.geometry.box(view_port[0], view_port[1], view_port[2],view_port[3])
    area = abs(geod.geometry_area_perimeter(box)[0])
    if (area) < 250000 and (area) > 90000:
        return False

    return True



@api_view(['PUT'])
@requires_scopes(['blender.write'])
def create_dss_subscription(request, *args, **kwargs):
    ''' This module takes a lat, lng box from Flight Spotlight and puts in a subscription to the DSS for the ISA '''

    try:        
        view = request.query_params['view']
        view_port = [float(i) for i in view.split(",")]
    except Exception as ke:        
        incorrect_parameters = {"message":"A view bbox is necessary with four values: minx, miny, maxx and maxy"}
        return HttpResponse(json.dumps(incorrect_parameters), status=400)

    view_port_valid = check_view_port(view_port=view_port)

    if not view_port_valid:
        incorrect_parameters = {"message":"A view bbox is necessary with four values: minx, miny, maxx and maxy"}
        return HttpResponse(json.dumps(incorrect_parameters), status=400)

    b = shapely.geometry.box(view_port[0], view_port[1], view_port[2],view_port[3])
    co_ordinates = list(zip(*b.exterior.coords.xy))
    # Convert bounds vertex list
    vertex_list = []
    for cur_co_ordinate in co_ordinates:
        lat_lng = {"lng":0, "lat":0}
        lat_lng["lng"] = cur_co_ordinate[0]
        lat_lng["lat"] = cur_co_ordinate[1]
        vertex_list.append(lat_lng)
    # remove the final point 
    vertex_list.pop()
    
    request_id = str(uuid.uuid4())    
    # TODO: Make this a asnyc call
    subscription_response = create_new_subscription(request_id=request_id, vertex_list=vertex_list, view= view)
    if subscription_response['created']:
        msg = {"message":"DSS Subscription created", 'id': uuid, "subscription_response":subscription_response}
        status = 201
    else:
        msg = {"message":"Error in creating DSS Subscription, please check the log or contact your administrator.", 'id': request_id}
        status = 400
        
    return HttpResponse(json.dumps(msg), status=status)


@api_view(['GET'])
@requires_scopes(['blender.read'])
def get_rid_data(request, subscription_id):
    ''' This is the GET endpoint for remote id data given a subscription id. Blender will store flight URLs and everytime '''

    try:
        is_uuid = UUID(subscription_id, version=4)
    except ValueError as ve: 
        return HttpResponse("Incorrect UUID passed in the parameters, please send a valid subscription ID", status=400, mimetype='application/json')

    r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
    flights_dict = {}
    # Get the flights URL from the DSS and put it in 
    for keybatch in flight_stream_helper.batcher(r.scan_iter('all_uss_flights-*'),500): # reasonably we wont have more than 500 subscriptions active
        stored_subscription_id = keybatch.split('-')[1]        
        if (subscription_id == stored_subscription_id):
            flights_dict = r.get(*keybatch)
            break
    
    if bool(flights_dict):
        # TODO for Pull operations Flights Dict is not being used at all
        all_flights_rid_data = []
        stream_ops = flight_stream_helper.StreamHelperOps()
        push_cg = stream_ops.push_cg()
        obs_helper = flight_stream_helper.ObservationReadOperations()
        all_flights_rid_data = obs_helper.get_observations(push_cg)
        
        return HTTPResponse(json.dumps(all_flights_rid_data), status = 200, mimetype='application/json')
    else:
        return HTTPResponse(json.dumps({}), status = 404, mimetype='application/json')

            

@api_view(['POST'])
@requires_scopes(['dss.write.identification_service_areas'])
def dss_isa_callback(request, subscription_id):
    ''' This is the call back end point that other USSes in the DSS network call once a subscription is updated '''
    service_areas = request.get('service_area',0)
    try:        
        assert service_areas != 0
        r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
        # Get the flights URL from the DSS and put it in the flights_url
        
        flights_key = "all_uss_flights-"+ subscription_id

        flights_dict = r.hgetall(flights_key)        
        all_flights_url = flights_dict['all_flights_url']

        for new_flight in service_areas:
            all_flights_url += " " + new_flight['flights_url']

        flights_dict["all_uss_flights"] = all_flights_url
        r.hmset(flights_key, flights_dict)
        
    except AssertionError as ae:
        return HttpResponse("Incorrect data in the POST URL", status=400, mimetype='application/json')
        
    else:
        # All OK return a empty response
        return HttpResponse(status=204, mimetype='application/json')


@api_view(['GET'])
@requires_scopes(['dss.read.identification_service_areas'])
def get_display_data(request):
    ''' This is the end point for the rid_qualifier test DSS network call once a subscription is updated '''
    
    # get the view bounding box 
    # get the existing subscription id , if no subscription exists, then reject
    request_id = str(uuid.uuid4())   
    try:        
        view = request.query_params['view']
        view_port = [float(i) for i in view.split(",")]
    except Exception as ke:        
        incorrect_parameters = {"message":"A view bbox is necessary with four values: minx, miny, maxx and maxy"}
        return HttpResponse(json.dumps(incorrect_parameters), status=400)
    view_port_valid = check_view_port(view_port=view_port)
    
    b = shapely.geometry.box(view_port[0], view_port[1], view_port[2],view_port[3])
    co_ordinates = list(zip(*b.exterior.coords.xy))
    # Convert bounds vertex list
    vertex_list = []
    for cur_co_ordinate in co_ordinates:
        lat_lng = {"lng":0, "lat":0}
        lat_lng["lng"] = cur_co_ordinate[0]
        lat_lng["lat"] = cur_co_ordinate[1]
        vertex_list.append(lat_lng)
    # remove the final point 
    vertex_list.pop()
    
    if view_port_valid:   
        # stream_id = hashlib.md5(view.encode('utf-8')).hexdigest()
        # create a subscription 
        # subscription_response = create_new_subscription(request_id=request_id, vertex_list=vertex_list, view= view)  
        # TODO: Get existing flight details from subscription
        stream_ops = flight_stream_helper.StreamHelperOps()
        pull_cg = stream_ops.get_pull_cg()


        all_streams_messages = pull_cg.read()
        
        pending_messages = []
        
        for all_observations_messages in all_streams_messages:        
            timestamp = all_observations_messages.timestamp
            print(timestamp)
            try:
                pending_messages.append({'timestamp':timestamp.isoformat() ,'seq': all_observations_messages.sequence, 'msg_data':all_observations_messages.data, 'address':all_observations_messages.data['icao_address'], 'metadata':all_observations_messages.data['metadata']})
            except KeyError as ke: 
                logging.error("Error in data in the stream %s" % ke)

        return HttpResponse(json.dumps({"flights":pending_messages, "clusters":[]}),)
    else:
        view_port_error = {"message":"A incorrect view port bbox was provided"}
        return HttpResponse(json.dumps(view_port_error), status=400)


@api_view(['GET'])
@requires_scopes(['dss.read.identification_service_areas'])
def get_flight_data(request, flight_id):
    ''' This is the end point for the rid_qualifier test DSS network call once a subscription is updated '''

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

    return HttpResponse(json.dumps({"details":{}}), mimetype='application/json')

