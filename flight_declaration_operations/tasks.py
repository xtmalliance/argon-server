from flight_blender.celery import app
from scd_operations.opint_helper import DSSOperationalIntentsCreator
from flight_declaration_operations.models import FlightDeclaration
import logging
from notification_operations.notification_helper import NotificationFactory
from notification_operations.data_definitions import FlightDeclarationUpdateMessage
from os import environ as env

logger = logging.getLogger('django')
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

@app.task(name='submit_flight_declaration_to_dss')
def submit_flight_declaration_to_dss(flight_declaration_id:str):

    my_dss_opint_creator = DSSOperationalIntentsCreator(flight_declaration_id)
    
    flight_operation_validated = my_dss_opint_creator.validate_flight_declaration_details()
    
    logging.info("Flight Operation Validation status %s"% flight_operation_validated)
    if flight_operation_validated:            
        opint_submission_result = my_dss_opint_creator.submit_flight_declaration_to_dss()            
        if opint_submission_result.status_code == 500:
            logger.error("Error in submitting Flight Declaration to the DSS %s" % opint_submission_result.status)
        elif opint_submission_result.status_code in [200, 201]:
            logger.info("Successfully submitted Flight Declaration to the DSS %s" % opint_submission_result.status)
            
            fo = FlightDeclaration.objects.get(id = flight_declaration_id)
            # Update state of the flight operation
            fo.state = 1
            fo.save()
        logging.info("Details of the submission status %s" % opint_submission_result.message)
    else:            
        logging.error("Flight Declaration details are not valid, please check the submitted GeoJSON, this operation will not be sent to the DSS for strategic deconfliction")


@app.task(name="send_operational_update_message")
def send_operational_update_message(flight_declaration_id:str, message_text:str , level:str = 'info'):

    update_message = FlightDeclarationUpdateMessage(body=message_text, level=level)
    amqp_connection_url = env.get('AMQP_URL', 0)
    if amqp_connection_url:
        my_notification_helper = NotificationFactory(flight_declaration_id = flight_declaration_id, amqp_connection_url=amqp_connection_url)
        my_notification_helper.declare_queue(queue_name=flight_declaration_id)
        my_notification_helper.send_message(message_details= update_message)
        logger.info("Submitted Flight Declaration Notification")
    else: 
        logger.info("No AMQP URL specified ")
