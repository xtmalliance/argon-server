import os, json
import logging
from .utils import BlenderConformanceOps
from flight_blender.celery import app
from os import environ as env
from common.database_operations import BlenderDatabaseReader
import arrow
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

#### Airtraffic Endpoint


# This method conducts flight conformance checks
@app.task(name='check_flight_conformance')
def check_flight_conformance():
    # This method checks the conformance status for ongoing operations and sends notifications / via the notificaitons chanel
    my_conformance_ops = BlenderConformanceOps()

    # Get the 

    my_database_reader = BlenderDatabaseReader()
    now = arrow.now().isoformat()
    relevant_flight_declarations = my_database_reader.get_relevant_flight_declaration_ids(now = now)  
    
    for relevant_flight_declaration in relevant_flight_declarations:     
        non_telemetry_conformance = my_conformance_ops.check_flight_authorization_conformance(flight_declaration_id=relevant_flight_declaration)
        

