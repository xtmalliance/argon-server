import os, json
import logging
from .utils import BlenderConformanceOps
from flight_blender.celery import app
from os import environ as env
from common.database_operations import BlenderDatabaseReader
import arrow
from . import custom_signals
from scd_operations.scd_data_definitions import LatLngPoint
from django.core import management
from flight_feed_operations import flight_stream_helper
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

#### Airtraffic Endpoint

# This method conducts flight conformance checks
@app.task(name='check_flight_conformance')
def check_flight_conformance(dry_run:str = None):
    # This method checks the conformance status for ongoing operations and sends notifications / via the notificaitons channel    
    dry_run = 1 if dry_run =='1' else 0        
    my_conformance_ops = BlenderConformanceOps()    
    my_database_reader = BlenderDatabaseReader()
    now = arrow.now().isoformat()
    relevant_flight_declarations = my_database_reader.get_current_flight_accepted_activated_declaration_ids(now = now)  
    
    logger.info("{num_relevant_operations} relevant operations found...".format(num_relevant_operations=len(relevant_flight_declarations)))
    for relevant_flight_declaration in relevant_flight_declarations:   
        flight_declaration_id = str(relevant_flight_declaration)
        flight_authorization_conformant = my_conformance_ops.check_flight_authorization_conformance(flight_declaration_id=relevant_flight_declaration)
        
        if flight_authorization_conformant:
            logger.info("Operation with {flight_operation_id} is conformant...".format(flight_operation_id=flight_declaration_id))
            # Basic conformance checks passed, check telemetry conformance 
            # check_operation_telemetry_conformance(flight_declaration_id = flight_declaration_id)

        else:
            custom_signals.flight_authorization_conformance_monitoring_signal.send(sender='check_flight_conformance', non_conformance_state= flight_authorization_conformant, flight_declaration_id = flight_declaration_id)
            # Flight Declaration is not conformant             
            logger.info("Operation with {flight_operation_id} is not conformant...".format(flight_operation_id=flight_declaration_id))

# This method conducts flight telemetry checks
@app.task(name='check_operation_telemetry_conformance')
def check_operation_telemetry_conformance(flight_declaration_id:str, dry_run:str = None):
    # This method checks the conformance status for ongoing operations and sends notifications / via the notificaitons channel    
    dry_run = 1 if dry_run =='1' else 0        
    my_conformance_ops = BlenderConformanceOps()     

    # Get Telemetry
    stream_ops = flight_stream_helper.StreamHelperOps()
    read_cg = stream_ops.get_read_cg()
    obs_helper = flight_stream_helper.ObservationReadOperations()
    all_flights_rid_data = obs_helper.get_observations(read_cg)
    # Get the latest telemetry
    if all_flights_rid_data:        
        all_flights_rid_data.sort(key=lambda item:item['timestamp'], reverse=True)               
        distinct_messages = {i['address']:i for i in reversed(all_flights_rid_data)}.values()

        for message in list(distinct_messages):            
            metadata = message['metadata']
            if metadata['flight_details']['id'] == flight_declaration_id:                
                lat_dd = message['msg_data']['lat_dd']
                lon_dd = message['msg_data']['lon_dd']
                altitude_m_wgs84 = message['msg_data']['altitude_mm']
                aircraft_id = message['address']
                
                conformant_via_telemetry = my_conformance_ops.is_operation_conformant_via_telemetry(flight_declaration_id=flight_declaration_id,aircraft_id=aircraft_id, telemetry_location= LatLngPoint(lat = lat_dd, lng= lon_dd),altitude_m_wgs_84=float(altitude_m_wgs84))            
                logger.info("Operation with {flight_operation_id} is not conformant via telemetry failed test {conformant_via_telemetry}...".format(flight_operation_id=flight_declaration_id, conformant_via_telemetry = conformant_via_telemetry))
                if conformant_via_telemetry:
                    pass
                else: 
                    custom_signals.telemetry_conformance_monitoring_signal.send(sender='conformant_via_telemetry', non_conformance_state= conformant_via_telemetry, flight_declaration_id = flight_declaration_id)
                break
                
            