# Create your views here.
import json
import logging
from django.http import JsonResponse
from auth_helper.utils import requires_scopes
from rest_framework.decorators import api_view
from .tasks import write_incoming_air_traffic_data, start_openskies_stream
from .data_definitions import RIDMetadata, SingleAirtrafficObervation, FlightObservationsProcessingResponse
from dataclasses import asdict
from typing import List
from django.views.generic import TemplateView
import shapely.geometry

from rid_operations import view_port_ops
from . import flight_stream_helper
logger = logging.getLogger('django')

class HomeView(TemplateView):
    template_name = 'homebase/home.html'

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
        
        msg = FlightObservationsProcessingResponse(message="At least one observation is required: observations with a list of observation objects. One or more of these were not found in your JSON request. For sample data see: https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md#sample-traffic-object", status= 400)

        m = asdict(msg)
        return JsonResponse(m, status= m['status'])

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
            logger.error("Metadata not found in submitted observation %s" % mt_ke)
        else:
            try:
                mtd = RIDMetadata(aircraft_type = metadata['aircraft_type'])
            except(KeyError, TypeError) as mt_ve:
                logger.error("Aircraft Type not found in submitted observation details %s" % mt_ve)
                pass            

        # single_observation = {'lat_dd': lat_dd,'lon_dd':lon_dd,'altitude_mm':altitude_mm, 'traffic_source':traffic_source, 'source_type':source_type, 'icao_address':icao_address , 'metadata' : json.dumps(metadata)}
        so = SingleAirtrafficObervation(lat_dd= lat_dd, lon_dd=lon_dd, altitude_mm=altitude_mm, traffic_source= traffic_source, source_type= source_type, icao_address=icao_address, metadata= mtd)
        
        msgid = write_incoming_air_traffic_data.delay(json.dumps(asdict(so)))  # Send a job to the task queue
       
    op = FlightObservationsProcessingResponse(message="OK", status = 200)
    return JsonResponse(asdict(op), status=op.status)

@api_view(['GET'])
@requires_scopes(['blender.read'])
def get_air_traffic(request):
    ''' This is the end point for the rid_qualifier test DSS network call once a subscription is updated '''

    # get the view bounding box
    # get the existing subscription id , if no subscription exists, then reject
    try:
        view = request.query_params['view']
        view_port = [float(i) for i in view.split(",")]
    except Exception as ke:
        incorrect_parameters = {"message": "A view bbox is necessary with four values: minx, miny, maxx and maxy"}
        return JsonResponse(json.loads(json.dumps(incorrect_parameters)), status=400, content_type='application/json')
    
    view_port_valid = view_port_ops.check_view_port(view_port_coords=view_port)

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
        stream_ops = flight_stream_helper.StreamHelperOps()
        pull_cg = stream_ops.get_pull_cg()
        all_streams_messages = pull_cg.read()
        
        unique_flights = []
        # Keep only the latest message
        try:
            for message in all_streams_messages:     
                if message.data != '':
                    unique_flights.append({'timestamp': message.timestamp,'seq': message.sequence, 'msg_data':message.data, 'address':message.data['icao_address']})            
            # sort by date
            unique_flights.sort(key=lambda item:item['timestamp'], reverse=True)
            # Keep only the latest message
            distinct_messages = {i['address']:i for i in reversed(unique_flights)}.values()
            
        except KeyError as ke: 

            logger.error("Error in sorting distinct messages, ICAO name not defined %s" % ke)                     
            distinct_messages = []
        all_traffic_observations: List[SingleAirtrafficObervation] = []
        for observation in distinct_messages:                   
            observation_metadata = observation['metadata']
            so = SingleAirtrafficObervation(lat_dd=observation['lat_dd'], lon_dd=observation['lon_dd'], altitude_mm=observation['altitude_mm'],traffic_source=observation['traffic_source'], icao_address=observation['icao_address'], metadata=observation_metadata)
            all_traffic_observations.append(asdict(so))
        

        return JsonResponse(all_traffic_observations,  status=200, content_type='application/json')
    else:
        view_port_error = {"message": "A incorrect view port bbox was provided"}
        return JsonResponse(json.loads(json.dumps(view_port_error)), status=400, content_type='application/json')


@api_view(['GET'])
@requires_scopes(['blender.read'])
def start_opensky_feed(request):
    # This method takes in a view port as a lat1,lon1,lat2,lon2 co-ordinate system and for 60 seconds starts the stream of data from the OpenSky Network. 

    # Check view port
    # see if it is valid
    try:
        view = request.query_params['view']
        view_port = [float(i) for i in view.split(",")]
    except Exception as ke:
        incorrect_parameters = {"message": "A view bbox is necessary with four values: minx, miny, maxx and maxy"}
        return JsonResponse(json.loads(json.dumps(incorrect_parameters)), status=400, content_type='application/json')
    
    view_port_valid = view_port_ops.check_view_port(view_port_coords=view_port)
    
    if view_port_valid:
        start_openskies_stream.delay(view_port = json.dumps(view_port))
        return JsonResponse({"message":"Openskies Newtork stream started"},  status=200, content_type='application/json')
    else:
        view_port_error = {"message": "An incorrect view port bbox was provided"}
        return JsonResponse(json.loads(json.dumps(view_port_error)), status=400, content_type='application/json')
