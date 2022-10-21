
import uuid
from flight_blender.celery import app
import logging
from . import dss_rid_helper
from auth_helper.common import get_redis
from .rid_utils import RIDAircraftPosition, RIDAircraftState, RIDTestInjection, FullRequestedFlightDetails,RIDTestDetailsResponse, RIDFlightDetails, LatLngPoint, RIDHeight, AuthData,SingleObeservationMetadata,RIDFootprint, RIDTestInjectionProcessing, RIDTestDataStorage
import time
import arrow
import json
from arrow.parser import ParserError     
from typing import List
from dataclasses import asdict
from os import environ as env
from flight_feed_operations import flight_stream_helper
from flight_feed_operations.data_definitions import SingleRIDObservation
from flight_feed_operations.tasks import write_incoming_air_traffic_data
from shapely.geometry import Point, MultiPoint, box
from .rid_utils import RIDVertex, RIDVolume3D, RIDVolume4D

logger = logging.getLogger('django')
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

@app.task(name='submit_dss_subscription')
def submit_dss_subscription(view , vertex_list, request_uuid):
    subscription_time_delta = 30
    myDSSSubscriber = dss_rid_helper.RemoteIDOperations()
    subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view, request_uuid = request_uuid,subscription_time_delta=subscription_time_delta)
    logger.success("Subscription creation status: %s" % subscription_created['created'])

@app.task(name='poll_uss_for_flights_async')
def poll_uss_for_flights_async():
    myDSSSubscriber = dss_rid_helper.RemoteIDOperations()

    stream_ops = flight_stream_helper.StreamHelperOps()
    push_cg = stream_ops.get_push_cg()
    all_observations = push_cg.all_observations

    # TODO: Get existing flight details from subscription
    r = get_redis()
    flights_dict = {}
    # Get the flights URL from the DSS and put it in 
    for keybatch in flight_stream_helper.batcher(r.scan_iter('all_uss_flights:*'), 100): # reasonably we wont have more than 100 subscriptions active        
        key_batch_set = set(keybatch)        
        for key in key_batch_set:
            if key:
                flights_dict = r.hgetall(key)      
                logger.debug('Flights Dict %s' % flights_dict)    
                if bool(flights_dict):
                    subscription_id = key.split(':')[1]                    
                    myDSSSubscriber.query_uss_for_rid(flights_dict, all_observations,subscription_id)


@app.task(name='stream_rid_data')
def stream_rid_data(rid_data):
    rid_data = json.loads(rid_data)
    for r_data in rid_data:
        observation_metadata = SingleObeservationMetadata(telemetry= r_data, details_response=r_data)                
        flight_details_id = r_data['id']
        lat_dd = r_data['current_state']['position']['lat']
        lon_dd = r_data['current_state']['position']['lng']                    
        altitude_mm = r_data['current_state']['position']['alt']
        traffic_source = 11 # Per the Air-traffic data protocol a source type of 11 means that the data is associated with RID observations
        source_type = 0
        icao_address = flight_details_id

        so = SingleRIDObservation(lat_dd= lat_dd, lon_dd=lon_dd, altitude_mm=altitude_mm, traffic_source= traffic_source, source_type= source_type, icao_address=icao_address, metadata= json.dumps(asdict(observation_metadata)))                    
        msgid = write_incoming_air_traffic_data.delay(json.dumps(asdict(so)))  # Send a job to the task queue
        logger.debug("Submitted observation..")                    
        logger.debug("...")


@app.task(name='stream_rid_test_data')
def stream_rid_test_data(requested_flights):
    all_requested_flights : List[RIDTestInjection] = []
    rf = json.loads(requested_flights)
    all_positions:List[LatLngPoint] = []    
    
    flight_injection_sorted_set = 'requested_flight_ss'


    r = get_redis()
    # Iterate over requested flights 
    for requested_flight in rf:  
        all_telemetry = []
        
        all_flight_details = []
        provided_telemetries = requested_flight['telemetry']
        provided_flight_details = requested_flight['details_responses']


        for provided_flight_detail in provided_flight_details: 
            fd = provided_flight_detail['details']
            
            op_location = LatLngPoint(lat = fd['operator_location']['lat'], lng= fd['operator_location']['lng'])
            if 'auth_data' in fd.keys():
                auth_data = AuthData(format=fd['auth_data']['format'],data=fd['auth_data']['data'])
            else:
                auth_data = AuthData(format="",data="")

            flight_detail = RIDFlightDetails(id=fd['id'], operation_description=fd['operation_description'], serial_number= fd['serial_number'], registration_number=fd['registration_number'],operator_location=op_location, operator_id= fd['operator_id'], auth_data=auth_data)
            pfd = RIDTestDetailsResponse(effective_after=provided_flight_detail['effective_after'], details = flight_detail)
            all_flight_details.append(pfd)

            flight_details_storage = 'flight_details:' + fd['id']
            r.set(flight_details_storage, json.dumps(asdict(flight_detail)))
            # expire in 5
            r.expire(flight_details_storage, time=3000)
        # Iterate over telemetry details profided
        for (telemetry_id, provided_telemetry) in enumerate(provided_telemetries):
            pos = provided_telemetry['position']
            # In provided telemetry position and pressure altitude and extrapolated values are optional use if provided else generate them.
            pressure_altitude = pos['pressure_altitude'] if 'pressure_altitude' in pos else 0.0
            extrapolated = pos['extrapolated'] if 'extrapolated' in pos else 0

            llp = LatLngPoint(lat = pos['lat'], lng = pos['lng'])
            all_positions.append(llp)
            position = RIDAircraftPosition(lat=pos['lat'], lng=pos['lng'],alt=pos['alt'],accuracy_h=pos['accuracy_h'], accuracy_v=pos['accuracy_v'], extrapolated=extrapolated,pressure_altitude=pressure_altitude)
            
            height = RIDHeight(distance=provided_telemetry['height']['distance'], reference=provided_telemetry['height']['reference'])
            try: 
                formatted_timestamp = arrow.get(provided_telemetry['timestamp'])
            except ParserError as pe: 
                logging.info("Error in parsing telemetry timestamp")
            else:
                
                t = RIDAircraftState(timestamp=provided_telemetry['timestamp'], timestamp_accuracy=provided_telemetry['timestamp_accuracy'], operational_status=provided_telemetry['operational_status'], position=position, track=provided_telemetry['track'], speed=provided_telemetry['speed'], speed_accuracy=provided_telemetry['speed_accuracy'], vertical_speed=provided_telemetry['vertical_speed'], height=height)

                telemetry_timestamp = arrow.get(t.timestamp)
                closest_details_response = min(all_flight_details, key=lambda d: abs(arrow.get(d.effective_after) - telemetry_timestamp))        
                flight_state_storage = RIDTestDataStorage( flight_state = t, details_response = closest_details_response)                
                r.zadd(flight_injection_sorted_set, {json.dumps(asdict(flight_state_storage)):telemetry_timestamp.int_timestamp})

                all_telemetry.append(t)             
                
        requested_flight = RIDTestInjectionProcessing(injection_id = requested_flight['injection_id'], telemetry = all_telemetry, details_responses=all_flight_details)

        all_requested_flights.append(requested_flight)
        
    heartbeat = env.get('HEARTBEAT_RATE_SECS', 2)
    heartbeat = int(heartbeat)
    start_time = arrow.now()
    isa_start_time = start_time.shift(seconds = 5)

    all_requested_flight_details: List[FullRequestedFlightDetails] = []
    max_telemetry_data_length = 0
    telemetry_length = []
    for flight_id, r_f in enumerate(all_requested_flights):

        internal_flight_id = str(uuid.uuid4())
        telemetry_length.append(len(r_f.telemetry))
        all_requested_flight_details.append(FullRequestedFlightDetails(id= internal_flight_id,telemetry_length = len(r_f.telemetry), injection_details = asdict(r_f)))

    max_telemetry_data_length = max(telemetry_length)
    logger.info("Telemetry length: %s" % max_telemetry_data_length)

    # Computing when the requested flight data will end 
    end_time_of_injections = max_telemetry_data_length * heartbeat
    isa_end_time = start_time.shift(seconds = end_time_of_injections)
    astm_rid_standard_end_time = end_time_of_injections + 180 # Enable querying for upto sixty seconds after end time. 
    end_time_of_injections_seconds =  start_time.shift(seconds = astm_rid_standard_end_time)
    
    # Create a ISA in the DSS
    
    position_list: List[Point] = []
    for position in all_positions:
        position_list.append((position.lng, position.lat))

    multi_points = MultiPoint(position_list)
    bounds = multi_points.minimum_rotated_rectangle.bounds

    b = box(bounds[1], bounds[0], bounds[3], bounds[2])
    co_ordinates = list(zip(*b.exterior.coords.xy))
    
    polygon_verticies = []
    for co_ordinate in co_ordinates:
        v = RIDVertex(lat = co_ordinate[0],lng= co_ordinate[1])
        polygon_verticies.append(v)
    polygon_verticies.pop()
    footprint = RIDFootprint(vertices=polygon_verticies)
    altitude_lower = 610
    altitude_upper = 630
                       
    flight_volume = RIDVolume3D(footprint=footprint, altitude_high=altitude_upper, altitude_lo= altitude_lower)
    flight_extents = RIDVolume4D(spatial_volume= flight_volume,time_start= isa_start_time.isoformat(), time_end = isa_end_time.isoformat())

    flights_url = env.get("BLENDER_FQDN", "http://host.docker.internal:8000") + '/uss/flights'
    my_dss_helper = dss_rid_helper.RemoteIDOperations()
    
    logger.info("Creating a DSS ISA")
    my_dss_helper.create_dss_isa(flight_extents=flight_extents, flights_url=flights_url)
    # End create ISA in the DSS

    time.sleep(5) # Wait 5 seconds before starting mission
    should_continue = True

    def _stream_data(now:arrow.arrow.Arrow):
        # get telemetry that is closest to the current time 
        one_second_before_now = now.shift(seconds = -1)
        three_seconds_from_now = now.shift(seconds =4)        
        closest_observation = r.zrange(flight_injection_sorted_set, one_second_before_now.int_timestamp, three_seconds_from_now.int_timestamp)
    
        single_telemetry_data = closest_observation['flight_state']
        single_details_response = closest_observation['details_response']

        # TODO: At the moment, the first details repsonse is always used, check to have appropriate after timestamp
        
        observation_metadata = SingleObeservationMetadata(telemetry= single_telemetry_data, details_response=single_details_response)                
        flight_details_id = single_details_response['id']
        lat_dd = single_telemetry_data['position']['lat']
        lon_dd = single_telemetry_data['position']['lng']                    
        altitude_mm = single_telemetry_data['position']['alt']
        traffic_source = 3
        source_type = 0
        icao_address = flight_details_id
        
        so = SingleRIDObservation(lat_dd= lat_dd, lon_dd=lon_dd, altitude_mm=altitude_mm, traffic_source= traffic_source, source_type= source_type, icao_address=icao_address, metadata= json.dumps(asdict(observation_metadata)))                    
        msgid = write_incoming_air_traffic_data.delay(json.dumps(asdict(so)))  # Send a job to the task queue
        logger.debug("Submitted observation..")                    
        logger.debug("...")
        # Sleep for 2 seconds before submitting the next iteration.
    
    r.expire(flight_injection_sorted_set, time=3000)
    while should_continue:    
        now = arrow.now() 
        _stream_data(now = now)
        if now > end_time_of_injections_seconds:
            should_continue = False

            print("ending.... %s" % arrow.now().isoformat())