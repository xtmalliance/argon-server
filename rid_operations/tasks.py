import uuid
from flight_blender.celery import app
import logging
from . import dss_rid_helper
import redis
from .rid_utils import RIDTestInjection, AllRequestedFlightDetails
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
    rf = json.loads(requested_flights)
    for requested_flight in rf:       
        requested_flight = RIDTestInjection(injection_id = requested_flight['injection_id'], telemetry = requested_flight['telemetry'], details_responses=requested_flight['details_responses'])
        all_requested_flights.append(requested_flight)
    

    all_requested_flight_details = []
    max_telemetry_data_length = 0
    telemetry_length = []
    for flight_id, r_f in enumerate(all_requested_flights):
        internal_flight_id = str(uuid.uuid4())
        telemetry_length.append(len(r_f.telemetry))
        all_requested_flight_details.append(AllRequestedFlightDetails(id= internal_flight_id,telemetry_length = len(r_f.telemetry), injection = asdict(r_f)))

    max_telemetry_data_length = max(telemetry_length)
    
    for telemetry_idx in range(0, max_telemetry_data_length):
        for current_flight_idx in all_requested_flight_details:                        
            if telemetry_idx < current_flight_idx.telemetry_length:
                telemetry_data = current_flight_idx.injection['telemetry'][telemetry_idx]
                flight_details_id = current_flight_idx.id
                print(telemetry_data)

                lat_dd = telemetry_data['position']['lat']
                lon_dd = telemetry_data['position']['lng']    
                altitude_mm = telemetry_data['position']['alt']
                traffic_source = 3
                source_type = 0
                icao_address = flight_details_id
                mtd = json.dumps(telemetry_data)
                so = SingleObervation(lat_dd= lat_dd, lon_dd=lon_dd, altitude_mm=altitude_mm, traffic_source= traffic_source, source_type= source_type, icao_address=icao_address, metadata= mtd)
                
                msgid = write_incoming_air_traffic_data.delay(json.dumps(asdict(so)))  # Send a job to the task queue
                # Sleep for 2 seconds before submitting the next iteration.

                time.sleep(int(heartbeat))
