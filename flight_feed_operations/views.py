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
from rid_operations.rid_utils import  RIDTime, RIDAircraftPosition, RIDAircraftState, TelemetryFlightDetails,RIDOperatorDetails
from rid_operations import view_port_ops
import arrow
from rid_operations.tasks import stream_rid_data
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
        

        return JsonResponse({"observations":all_traffic_observations},  status=200, content_type='application/json')
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


@api_view(['PUT'])
@requires_scopes(['blender.write'])
def set_telemetry(request):
    ''' A RIDFlightDetails object is posted here'''
    # This endpoints receives data from GCS and / or flights and processes remote ID data. 
    # TODO: Use dacite to parse incoming json into a dataclass
    raw_data = request.data
    
    try: 
        assert 'observations' in raw_data
    except AssertionError as ae:        
        incorrect_parameters = {"message": "A flight observation object with current state and flight details is necessary"}
        return JsonResponse(incorrect_parameters, status=400, content_type='application/json')
    # Get a list of flight data
    rid_observations = raw_data['observations']
    
    all_rid_data = []
    for flight in rid_observations: 
        try: 
            assert 'flight_details' in flight
            assert 'current_states' in flight
        except AssertionError as ae:
            incorrect_parameters = {"message": "A flights object with current states, flight details is necessary"}
            return JsonResponse(incorrect_parameters, status=400, content_type='application/json')
                
        current_states = flight['current_states']
        flight_details = flight['flight_details']
        # 
        for current_state in current_states:
            # mandatory RID Fields
            try: 
                assert 'position' in current_state
                assert 'speed_accuracy' in current_state
            except AssertionError as e: 
                incorrect_parameters = {"message": "A position and speed_accuracy object is necessary "}
                return JsonResponse(incorrect_parameters, status=400, content_type='application/json')
                
            position = current_state['position']
            speed_accuracy = current_state['speed_accuracy']


            # Optional RID Fields
            if ("operational_status","height","timestamp","track","vertical_speed","timestamp_accuracy") <= tuple(current_state.keys()):
                logging.info("All optional information provided")
            else: 
                logging.info("Not all optional information is provided")

            # operational_status = current_state['operational_status']        
            # timestamp = current_state['timestamp']
            # height = current_state['height']
            # track = current_state['track']
            # speed = current_state['speed']
            # timestamp_accuracy = current_state['timestamp_accuracy']
            # vertical_speed = current_state['vertical_speed']
        # TODO: This is the operation id provided by Aerobridge
        flight_id = '61a8044b-d939-4326-a6c9-17bcdbb2e053'
        now = arrow.now().isoformat()    
        time_format = 'RFC3339'
        # Submit the time stamg as now
        time_stamp = RIDTime(value= now, format= time_format)
        logging.info("Submitting observation as now..")
        
        try: 
            assert set(("lat","lng","alt","accuracy_v","accuracy_h","extrapolated")) <= set(position.keys())
        except AssertionError as ae:
            
            incorrect_parameters = {"message": "A full position object is required to submit a RID observation"}
            return JsonResponse(incorrect_parameters, status=400, content_type='application/json')
        else: 
            aircraft_position  = RIDAircraftPosition(lat=position['lat'] , lng= position['lng'], alt =position['alt'], accuracy_h= position['accuracy_h'], accuracy_v=position['accuracy_v'], extrapolated =position['extrapolated'], pressure_altitude =0)
            current_state = RIDAircraftState(timestamp =time_stamp ,timestamp_accuracy= 0, position =aircraft_position, speed_accuracy = speed_accuracy)
        try: 
            assert set(("rid_details","operator_name","aircraft_type")) <= set(flight_details.keys())
        except AssertionError as ae:
            incorrect_parameters = {"message": "A full flight details object is required to submit a RID observation"}
            return JsonResponse(incorrect_parameters, status=400, content_type='application/json')
        rid_details = flight_details['rid_details']
        print(rid_details.keys())
        try: 
            assert set(("serial_number","operation_description","operator_location","operator_id","registration_number")) <= set(rid_details.keys())
        except AssertionError as ae:
            incorrect_parameters = {"message": "A full flight details object is required to submit a RID observation"}
            return JsonResponse(incorrect_parameters, status=400, content_type='application/json')

        else: 
            op_details = RIDOperatorDetails(operation_description=rid_details['operation_description'], serial_number = rid_details['serial_number'], registration_number = rid_details['registration_number'], operator_id =rid_details['operator_id'] )

        flight_id = rid_details['id']
        r  = TelemetryFlightDetails(id =flight_id,aircraft_type =flight_details['aircraft_type'], current_state = current_state, simulated = 0, recent_positions = [], operator_details = op_details)
        all_rid_data.append(asdict(r))

    stream_rid_data.delay(rid_data= all_rid_data)
    submission_success = {"message": "Telemetry data succesfully submitted"}
    return JsonResponse(submission_success, status=201, content_type='application/json')

        