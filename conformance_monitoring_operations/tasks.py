import os, json
import logging
from .utils import BlenderConformanceOps
from flight_blender.celery import app
from os import environ as env
from common.database_operations import BlenderDatabaseReader
import arrow
from django.core import management

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

logger = logging.getLogger('django')

#### Airtraffic Endpoint


# This method conducts flight conformance checks
@app.task(name='check_flight_conformance')
def check_flight_conformance(dry_run:str):
    # This method checks the conformance status for ongoing operations and sends notifications / via the notificaitons chanel
                 
    dry_run = 1 if dry_run =='1' else 0
        
    my_conformance_ops = BlenderConformanceOps()

    # Get the 

    my_database_reader = BlenderDatabaseReader()
    now = arrow.now().isoformat()
    relevant_flight_declarations = my_database_reader.get_current_flight_accepted_activated_declaration_ids(now = now)  
    
    for relevant_flight_declaration in relevant_flight_declarations:   
        flight_declaration_id = relevant_flight_declaration.id
        flight_declaration_conformant = my_conformance_ops.check_flight_authorization_conformance(flight_declaration_id=relevant_flight_declaration)
        if flight_declaration_conformant:
            pass
        else:
            # Flight Declaration is not conformant 
            if dry_run: 
                logger.info("Operation with {flight_operation_id} is conformant...".format(flight_operation_id=flight_declaration_id))
            else: 
                # The operation needs to be set as non-conformant and updated to the DSS, there is no need to add off-nominal volumes
                   
                management.call_command('update_non_conforming_op_int_notify',flight_declaration_id = flight_declaration_id, dry_run =0)
                

