from django.shortcuts import render

from django.utils.decorators import method_decorator
from requests.adapters import HTTPResponse
from auth_helper.utils import requires_scopes, BearerAuth
import json, os
from . import rtree_helper
import logging
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from . import dss_rw_helper
import uuid
from shapely.geometry import box
import redis
import uuid
import requests
import tldextract
from uuid import UUID
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def create_new_subscription(request_id, view, vertex_list):
    redis = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))  
    redis.set(json.dumps({'sub-' + request_id: view }))

    myDSSubscriber = dss_rw_helper.RemoteIDOperations()
    subscription_respone = myDSSubscriber.create_dss_subscription(vertex_list = vertex_list, view = view, request_uuid = request_id)

    return subscription_respone


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
    else:
        b = box(view_port[0], view_port[1], view_port[2],view_port[3])
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
        # TODO: Make this a asnyc call
        #tasks.submit_dss_subscription(vertex_list = vertex_list, view_port = view)
        request_id = str(uuid.uuid4())
        # my_index_helper = rtree_helper.IndexFactory()

        subscription_respone = create_new_subscription(request_id=request_id, vertex_list=vertex_list, view= view)
        # check if subscription exists.
        # try:
        #     subscription_index = my_index_helper.get_current_subscriptions()
        #     # Query the RTree to get the nearest subscription
        #     intersecting_subscription_list = list(subscription_index.intersection((view_port[0], view_port[1], view_port[2],view_port[3])))
        #     existing_subscription = False
        #     if intersecting_subscription_list:
        #         for current_subscription in intersecting_subscription_list: 
        #             current_box = box(current_subscription.box[0], current_subscription.box[1], current_subscription.box[2],current_subscription.box[3])
        #             if current_box.contains(b.buffer(-1e-14)) and current_box.buffer(1e-14).contains(b):
                        
        #                 existing_subscription = current_subscription['id']
        #                 break
        #         if existing_subscription: 
        #             subscription_respone = {'id':existing_subscription}
        #     else:
        #         subscription_respone = create_new_subscription(request_id=request_id, vertex_list=vertex_list, view= view)

        # except KeyError as ke:
        #     logging.info("No subscription exists for this viewport for view %s" % view)
 
        if subscription_respone['created']:
            msg = {"message":"DSS Subscription created", 'id': uuid, "subscription_response":subscription_respone}
        if subscription_respone['found']:
            msg = {"message":"Existing DSS Subscription found", 'id': subscription_respone['id']} # todo write existing subs
        else:
            msg = {"message":"Error in creating DSS Subscription, please check the log or contact your administrator.", 'id': request_id}
            
        return HttpResponse(json.dumps(msg), status=201)


@api_view(['GET'])
@requires_scopes(['blender.read'])
def get_rid_data(request, subscription_id):
    ''' This is the GET endpoint for remote id data given a subscription id. Blender will store flight URLs and everytime '''

    try:
        is_uuid = UUID(subscription_id, version=4)
    except ValueError as ve: 
        return HttpResponse("Incorrect UUID passed in the parameters, please send a valid subscription ID", status=400, mimetype='application/json')

    redis = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
    # Get the flights URL from the DSS and put it in 

    flights_key = "all_uss_flights-"+ subscription_id
    flights_dict = redis.get(flights_key)
    
    authority_credentials = dss_rw_helper.AuthorityCredentialsGetter()
    
    all_flights_url = flights_dict['all_flights_url']
    for cur_flight_url in all_flights_url:
        ext = tldextract.extract(cur_flight_url)          
        audience = '.'.join(ext[:3]) # get the subdomain, domain and suffix and create a audience and get credentials
        auth_credentials = authority_credentials.get_cached_credentials(audience)

        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + auth_credentials}
    
        flights_response = requests.post(cur_flight_url, headers=headers)
        if flights_response.status_code == 200:
            # https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/uastech/standards/astm_rid_1.0/remoteid/canonical.yaml#tag/p2p_rid/paths/~1v1~1uss~1flights/get
            return HTTPResponse(json.dumps(flights_response), status = 200, mimetype='application/json')
        
        else:
            return HTTPResponse(json.dumps(flights_response), status = 400, mimetype='application/json')
            

@api_view(['POST'])
@requires_scopes(['dss.write.identification_service_areas'])
def dss_isa_callback(request, subscription_id):
    ''' This is the call back end point that other USSes in the DSS network call once a subscription is updated '''
    service_areas = request.get('service_area',0)
    try:        
        assert service_areas != 0
        redis = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379))   
        # Get the flights URL from the DSS and put it in the flights_url
        
        flights_key = "all_uss_flights-"+ subscription_id

        flights_dict = redis.hgetall(flights_key)        
        all_flights_url = flights_dict['all_flights_url']
        for new_flight in service_areas:
            all_flights_url.append(new_flight['flights_url'])

        flights_dict["all_uss_flights"] = all_flights_url
        redis.hmset(flights_key, flights_dict)
        
    except AssertionError as ae:
        return HttpResponse("Incorrect data in the POST URL", status=400, mimetype='application/json')
        
    else:
        # All OK return a empty response
        return HttpResponse(status=204, mimetype='application/json')


@api_view(['GET'])
@requires_scopes(['dss.read.identification_service_areas'])
def get_display_data(request, view):
    ''' This is the end point for the rid_qualifier test DSS network call once a subscription is updated '''
    
    # get the view bounding box 

    # get the existing subscription id , if no subscription exists, then reject

    # get the flights endpoint and poll it every second 

    # send the polled data


    return HttpResponse(json.dumps({"flights":[], "clusters":[]}), mimetype='application/json')


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

