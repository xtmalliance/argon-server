from dotenv import load_dotenv, find_dotenv
import json
from flight_blender.celery import app
from scd_operations.opint_helper import DSSOperationalIntentsCreator
from flight_declaration_operations.models import FlightDeclaration
import logging
from notification_operations.notification_helper import NotificationFactory
from notification_operations.data_definitions import FlightDeclarationUpdateMessage
from os import environ as env
import arrow

logger = logging.getLogger('django')
load_dotenv(find_dotenv())


@app.task(name='submit_flight_declaration_to_dss')
def submit_flight_declaration_to_dss(flight_declaration_id: str):
    amqp_connection_url = env.get('AMQP_URL', 0)
    usingDss = env.get('DSS', 'false')

    if usingDss == 'true':
        my_dss_opint_creator = DSSOperationalIntentsCreator(
            flight_declaration_id)

        start_end_time_validated = my_dss_opint_creator.validate_flight_declaration_start_end_time()

        logging.info("Flight Operation Validation status %s" %
                     start_end_time_validated)
        if start_end_time_validated:
            if amqp_connection_url:
                validation_ok_msg = "Flight Operation with ID {operation_id} validated for start and end time, submitting to DSS..".format(
                    operation_id=flight_declaration_id)
                send_operational_update_message.delay(
                    flight_declaration_id=flight_declaration_id, message_text=validation_ok_msg, level='info')

            opint_submission_result = my_dss_opint_creator.submit_flight_declaration_to_dss()
            if opint_submission_result.status_code == 500:
                logger.error("Error in submitting Flight Declaration to the DSS %s" %
                             opint_submission_result.status)
                if amqp_connection_url:
                    dss_submission_error_msg = "Flight Operation with ID {operation_id} could not be submitted to the DSS, check the Auth server and / or the DSS URL".format(
                        operation_id=flight_declaration_id)
                    send_operational_update_message.delay(
                        flight_declaration_id=flight_declaration_id, message_text=dss_submission_error_msg, level='error')

            elif opint_submission_result.status_code in [200, 201]:
                logger.info("Successfully submitted Flight Declaration to the DSS %s" %
                            opint_submission_result.status)
                if amqp_connection_url:
                    submission_success_msg = "Flight Operation with ID {operation_id} submitted successfully to the DSS".format(
                        operation_id=flight_declaration_id)
                    send_operational_update_message.delay(
                        flight_declaration_id=flight_declaration_id, message_text=submission_success_msg, level='info')

                fo = FlightDeclaration.objects.get(id=flight_declaration_id)
                # Update state of the flight operation
                fo.state = 1
                if amqp_connection_url:
                    submission_state_updated_msg = "Flight Operation with ID {operation_id} has a updated state: Accepted. ".format(
                        operation_id=flight_declaration_id)
                    send_operational_update_message.delay(
                        flight_declaration_id=flight_declaration_id, message_text=submission_state_updated_msg, level='info')
                fo.save()
            logging.info("Details of the submission status %s" %
                         opint_submission_result.message)

        else:
            logging.error(
                "Flight Declaration start / end times are not valid, please check the submitted declaration, this operation will not be sent to the DSS for strategic deconfliction")
            if amqp_connection_url:
                validation_not_ok_msg = "Flight Operation with ID {operation_id} did not pass time validation, start and end time may not be ahead of two hours".format(
                    operation_id=flight_declaration_id)
                send_operational_update_message.delay(
                    flight_declaration_id=flight_declaration_id, message_text=validation_not_ok_msg, level='error')
    else:
        if amqp_connection_url:
            fo = FlightDeclaration.objects.get(id=flight_declaration_id)
            # Update state of the flight operation
            fo.state = 1
            if amqp_connection_url:
                id_str = str(fo.id)
                message = {
                    "id": id_str,
                    "approved": True
                }
                # json_message = json.dumps(message)
                # submission_state_updated_msg = "Flight Operation with ID {operation_id} has a updated state: Accepted. ".format(operation_id = flight_declaration_id)
                send_flight_approved_message.delay(
                    flight_declaration_id=flight_declaration_id, message_text=message, level='info')
            fo.save()


@app.task(name="send_operational_update_message")
def send_operational_update_message(flight_declaration_id: str, message_text: str, level: str = 'info', timestamp: str = None):

    if not timestamp:
        now = arrow.now()
        timestamp = now.isoformat()

    update_message = FlightDeclarationUpdateMessage(
        body=message_text, level=level, timestamp=timestamp)
    amqp_connection_url = env.get('AMQP_URL', 0)
    if amqp_connection_url:
        my_notification_helper = NotificationFactory(
            flight_declaration_id=flight_declaration_id, amqp_connection_url=amqp_connection_url)
        my_notification_helper.declare_queue(queue_name=flight_declaration_id)
        my_notification_helper.send_message(message_details=update_message)
        logger.info("Submitted Flight Declaration Notification")
    else:
        logger.info("No AMQP URL specified ")


@app.task(name="send_flight_approved_message")
def send_flight_approved_message(flight_declaration_id: str, message_text: str, level: str = 'info', timestamp: str = None):

    if not timestamp:
        now = arrow.now()
        timestamp = now.isoformat()

    update_message = FlightDeclarationUpdateMessage(
        body=message_text, level=level, timestamp=timestamp)
    amqp_connection_url = env.get('AMQP_URL', 0)
    if amqp_connection_url:
        my_notification_helper = NotificationFactory(
            flight_declaration_id=flight_declaration_id, amqp_connection_url=amqp_connection_url)
        my_notification_helper.declare_queue(queue_name='flight-approvals-'+flight_declaration_id)
        my_notification_helper.send_message(message_details=update_message)
        logger.info("Submitted Flight Declaration Approval")
    else:
        logger.info("No AMQP URL specified ")
