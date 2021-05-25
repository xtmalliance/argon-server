# Create your views here.
import json
import logging
from django.http import JsonResponse
from auth_helper.utils import requires_scopes
from rest_framework.decorators import api_view
from .tasks import write_incoming_data
from typing import NamedTuple, Type

class RIDMetadata(NamedTuple):
    ''' A class to store RemoteID metadata '''
    aircraft_type: str

class SingleObervation(NamedTuple):
    ''' This is the object stores details of the obervation  '''

    lat_dd: float
    lon_dd: float
    altitude_mm: float
    traffic_source: int
    source_type:int
    icao_address: str
    metadata: RIDMetadata


@api_view(['GET'])
def ping(request):
    return JsonResponse({"message":"pong"}, status=200)

@api_view(['POST'])
@requires_scopes(['blender.write'])
def set_air_traffic(request):

    ''' This is the main POST method that takes in a request for Air traffic observation and processes the input data '''  

    try:
        assert request.headers['Content-Type'] == 'application/json'   
    except AssertionError as ae:     
        msg = {"message":"Unsupported Media Type"}
        return JsonResponse(msg, status=415)
    else:    
        req = request.data
    
    try:
        observations = req['observations']
    except KeyError as ke:
        msg = {"message":"At least one observation is required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object"}

        
        return JsonResponse(msg, status=400)

    for observation in observations:  
        try: 
            lat_dd = observation['lat_dd']
            lon_dd = observation['lon_dd']
            altitude_mm = observation['altitude_mm']
            traffic_source = observation['traffic_source']
            source_type = observation['source_type']
            icao_address = observation['icao_address']
            
        except KeyError as obs_ke:
            msg = {"message":"One of your obervations do not have the mandatory required field"}
            
            return JsonResponse(msg, status=400)
            # logging.error("Not all data was provided")

        metadata = {}
        try: 
            metadata = observation['metadata']            
        except KeyError as mt_ke:
            pass
        else:
            try:
                mtd = RIDMetadata(aircraft_type = metadata['aircraft_type'])
            except(KeyError, TypeError) as mt_ve:
                pass
            else:
                metadata = {"aircraft_type": mtd.aircraft_type}
        

        single_observation = {'lat_dd': lat_dd,'lon_dd':lon_dd,'altitude_mm':altitude_mm, 'traffic_source':traffic_source, 'source_type':source_type, 'icao_address':icao_address , 'metadata' : json.dumps(metadata)}
        
        task = write_incoming_data.delay(json.dumps(single_observation))  # Send a job to the task queue

    op = {"message":"OK"}
    return JsonResponse(op, status=200)

                