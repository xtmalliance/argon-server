from django.shortcuts import render

# Create your views here.

# Create your views here.
from django.shortcuts import render
from django.utils.decorators import method_decorator
from auth_helper.utils import requires_scopes, BearerAuth
# Create your views here.
import json, os
import logging
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import dss_rw_helper
import uuid
from shapely.geometry import box
import redis

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


@api_view(['POST'])
@requires_scopes(['blender.write'])
def create_dss_subscription(request):
    ''' This module takes a lat, lng box from Flight Spotlight and puts in a subscription to the DSS for the ISA '''

    try: 
        view = request.POST['view']
        # view = request.POST.get['view'] # view is a bbox list
        view = [float(i) for i in view.split(",")]
    except Exception as ke:
        
        incorrect_parameters = {"message":"A view bbox is necessary with four values: minx, miny, maxx and maxy"}
        return HttpResponse(json.dumps(incorrect_parameters), status=400)
    else:
        b = box(view[0], view[1], view[2],view[3])
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
        uuid = str(uuid.uuid4())
        myDSSubscriber = dss_rw_helper.RemoteIDOperations()
        subscription_respone = myDSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view, request_uuid = uuid)

        if subscription_respone['created']:
            msg = {"message":"DSS Subscription created", 'id': uuid}
        else:
            msg = {"message":"Error in creating DSS Subscription, please check the log or contact your administrator.", 'id': uuid}
        return HttpResponse(json.dumps(msg), status=200)



@api_view(['GET'])
@requires_scopes(['blender.read'])
def get_rid_data(request, subscription_id):
    ''' This is the GET endpoint for remote id data '''
    pass


@api_view(['POST'])
@requires_scopes(['dss.write.identification_service_areas'])
def dss_isa_callback(request, id):
    ''' This is the call back end point that other USSes in the DSS network call once a subscription is updated '''
    new_flights_url = request.args.get('flights_url',0)
    try:        
        assert new_flights_url != 0
        redis = redis.Redis(host=os.getenv(['REDIS_HOST']), port =os.getenv(['REDIS_PORT']))   
        # Get the flights URL from the DSS and put it in 
        flights_dict = redis.hgetall("all_uss_flights")        
        all_flights_url = flights_dict['all_flights_url']
        all_flights_url = all_flights_url.append(new_flights_url)
        flights_dict["all_uss_flights"] = all_flights_url
        redis.hmset("all_uss_flights", flights_dict)
        
    except AssertionError as ae:
        return HttpResponse("Incorrect data in the POST URL", status=400, mimetype='application/json')
        
    else:
        # All OK return a empty response
        return HttpResponse("", status=204, mimetype='application/json')
