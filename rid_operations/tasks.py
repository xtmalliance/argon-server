import uuid
from flight_blender.celery import app
import logging
from . import dss_rid_helper
import redis
from .rid_utils import RIDAircraftPosition, RIDAircraftState, RIDTestInjection, AllRequestedFlightDetails,RIDTestDetailsResponse, RIDFlightDetails, LatLngPoint, RIDHeight, AuthData,SingleObeservationMetadata
import time
import arrow
import json
from dataclasses import asdict
from os import environ as env
from flight_feed_operations import flight_stream_helper
from flight_feed_operations.data_definitions import SingleObervation
from flight_feed_operations.tasks import write_incoming_air_traffic_data
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

@app.task(name='submit_dss_subscription')
def submit_dss_subscription(view , vertex_list, request_uuid):
    subscription_time_delta = 30
    myDSSSubscriber = dss_rid_helper.RemoteIDOperations()
    subscription_created = myDSSSubscriber.create_dss_subscription(vertex_list = vertex_list, view_port = view, request_uuid = request_uuid,subscription_time_delta=subscription_time_delta)
    logging.success("Subscription creation status: %s" % subscription_created['created'])

@app.task(name='poll_uss_for_flights_async')
def poll_uss_for_flights_async():
    myDSSSubscriber = dss_rid_helper.RemoteIDOperations()

    stream_ops = flight_stream_helper.StreamHelperOps()
    push_cg = stream_ops.get_push_cg()
    all_observations = push_cg.all_observations

    # TODO: Get existing flight details from subscription
    r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379), decode_responses=True)
    flights_dict = {}
    # Get the flights URL from the DSS and put it in 
    for keybatch in flight_stream_helper.batcher(r.scan_iter('all_uss_flights:*'), 100): # reasonably we wont have more than 100 subscriptions active        
        key_batch_set = set(keybatch)        
        for key in key_batch_set:
            if key:
                flights_dict = r.hgetall(key)      
                logging.debug('Flights Dict %s' % flights_dict)    
                if bool(flights_dict):
                    subscription_id = key.split(':')[1]                    
                    myDSSSubscriber.query_uss_for_rid(flights_dict, all_observations,subscription_id)


@app.task(name='stream_rid_test_data')
def stream_rid_test_data(requested_flights):
    all_requested_flights = []
    heartbeat = env.get('HEARTBEAT_RATE_SECS', 2)
    heartbeat = int(heartbeat)
    rf = json.loads(requested_flights)
    for requested_flight in rf:       
        all_telemetry = []
        all_flight_details = []
        provided_telemetries = requested_flight['telemetry']
        provided_flight_details = requested_flight['details_responses']
        for provided_flight_detail in provided_flight_details: 
            fd = provided_flight_detail['details']
            
            op_location = LatLngPoint(lat = fd['operator_location']['lat'], lng= fd['operator_location']['lng'])
            auth_data = AuthData(format=fd['auth_data']['format'],data=fd['auth_data']['data'])
            flight_detail = RIDFlightDetails(id=fd['id'], operation_description=fd['operation_description'], serial_number= fd['serial_number'], registration_number=fd['registration_number'],operator_location=op_location, operator_id= fd['operator_id'], auth_data=auth_data)
            pfd = RIDTestDetailsResponse(effective_after=provided_flight_detail['effective_after'], details = flight_detail)
            all_flight_details.append(pfd)

            r = redis.Redis(host=env.get('REDIS_HOST',"redis"), port =env.get('REDIS_PORT',6379), decode_responses=True)
            flight_details_storage = 'flight_details:' + fd['id']
            r.set(flight_details_storage, json.dumps(asdict(flight_detail)))
            r.expire(flight_details_storage, time=60)


        for provided_telemetry in provided_telemetries:
            pos = provided_telemetry['position']
            position = RIDAircraftPosition(lat=pos['lat'], lng=pos['lng'],alt=pos['alt'],accuracy_h=pos['accuracy_h'], accuracy_v=pos['accuracy_v'], extrapolated=pos['extrapolated'],pressure_altitude=pos['pressure_altitude'])
            
            height = RIDHeight(distance=provided_telemetry['height']['distance'], reference=provided_telemetry['height']['reference'])
            t = RIDAircraftState(timestamp=provided_telemetry['timestamp'], timestamp_accuracy=provided_telemetry['timestamp_accuracy'], operational_status=provided_telemetry['operational_status'], position=position, track=provided_telemetry['track'], speed=provided_telemetry['speed'], speed_accuracy=provided_telemetry['speed_accuracy'], vertical_speed=provided_telemetry['vertical_speed'], height=height)
            all_telemetry.append(t)

        requested_flight = RIDTestInjection(injection_id = requested_flight['injection_id'], telemetry = all_telemetry, details_responses=all_flight_details)

        all_requested_flights.append(requested_flight)
    
    

    all_requested_flight_details = []
    max_telemetry_data_length = 0
    telemetry_length = []
    for flight_id, r_f in enumerate(all_requested_flights):
        internal_flight_id = str(uuid.uuid4())
        telemetry_length.append(len(r_f.telemetry))
        all_requested_flight_details.append(AllRequestedFlightDetails(id= internal_flight_id,telemetry_length = len(r_f.telemetry), injection_details = asdict(r_f)))

    max_telemetry_data_length = max(telemetry_length)
    
    for telemetry_idx in range(0, max_telemetry_data_length):
        for current_flight_idx in all_requested_flight_details:                        
            if telemetry_idx < current_flight_idx.telemetry_length:
                
                single_telemetry_data = current_flight_idx.injection_details['telemetry'][telemetry_idx]
                # TODO: At the moment, the first details repsonse is always used, check to have appropriate after timestamp
                details_response = current_flight_idx.injection_details['details_responses'][0]
                observation_metadata = SingleObeservationMetadata(telemetry= single_telemetry_data, details_response=details_response)                
                flight_details_id = current_flight_idx.id
                
                lat_dd = single_telemetry_data['position']['lat']
                lon_dd = single_telemetry_data['position']['lng']
                
                altitude_mm = single_telemetry_data['position']['alt']
                traffic_source = 3
                source_type = 0
                icao_address = flight_details_id
                
                so = SingleObervation(lat_dd= lat_dd, lon_dd=lon_dd, altitude_mm=altitude_mm, traffic_source= traffic_source, source_type= source_type, icao_address=icao_address, metadata= json.dumps(asdict(observation_metadata)))
                
                msgid = write_incoming_air_traffic_data.delay(json.dumps(asdict(so)))  # Send a job to the task queue
                # Sleep for 2 seconds before submitting the next iteration.
                time.sleep(heartbeat)
