from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.utils.decorators import method_decorator
from auth_helper.utils import requires_scopes, BearerAuth
# Create your views here.
import json
import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .tasks import write_incoming_data


@api_view(['GET'])
def ping(request):
    return JsonResponse(json.dumps({"message":"pong"}), status=200,mimetype='application/json')

@api_view(['POST'])
@requires_scopes(['blender.write'])
def set_air_traffic(request):

    ''' This is the main POST method that takes in a request for Air traffic observation and processes the input data '''  

    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return Response(json.dumps(msg), status=415, mimetype='application/json')
    else:    
        req = json.loads(request.data)
    
    try:
        observations = req['observations']
    except KeyError as ke:
        msg = json.dumps({"message":"One parameter are required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object"})
        
        return JsonResponse(msg, status=400, mimetype='application/json')

    else:
        for observation in observations:  
            lat_dd = observation['lat_dd']
            lon_dd = observation['lon_dd']
            altitude_mm = observation['altitude_mm']
            traffic_source = observation['traffic_source']
            source_type = observation['source_type']
            icao_address = observation['icao_address']
            single_observation = {'lat_dd': lat_dd,'lon_dd':lon_dd,'altitude_mm':altitude_mm, 'traffic_source':traffic_source, 'source_type':source_type, 'icao_address':icao_address }
            task = write_incoming_data.delay(single_observation)  # Send a job to the task queue

        op = json.dumps ({"message":"OK"})
        return JsonResponse(op, status=200, mimetype='application/json')

                    