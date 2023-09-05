import logging
from enum import Enum
from os import environ as env

import arrow
from dotenv import find_dotenv, load_dotenv
from flight_blender.celery import app
from notification_operations.data_definitions import \
    FlightDeclarationUpdateMessage
from notification_operations.notification_helper import NotificationFactory
from rest_framework import status
from scd_operations.opint_helper import DSSOperationalIntentsCreator

from flight_declaration_operations.models import FlightDeclaration

logger = logging.getLogger("django")
load_dotenv(find_dotenv())


class LogLevel(str, Enum):
    INFO = "info"
    ERROR = "error"


@app.task(name="_send_flight_approved_message")
def _send_flight_approved_message(
    flight_declaration_id: str,
    message_text: str,
    level: str = LogLevel.INFO,
    timestamp: str = None,
):
    amqp_connection_url = env.get("AMQP_URL", 0)
    if not amqp_connection_url:
        logger.info("No AMQP URL specified")
        return

    if not timestamp:
        now = arrow.now()
        timestamp = now.isoformat()

    update_message = FlightDeclarationUpdateMessage(
        body=message_text, level=level, timestamp=timestamp
    )

    my_notification_helper = NotificationFactory(
        flight_declaration_id=flight_declaration_id,
        amqp_connection_url=amqp_connection_url,
    )
    my_notification_helper.declare_queue(
        queue_name="flight-approvals-" + flight_declaration_id
    )
    my_notification_helper.send_message(message_details=update_message)
    logger.info("Submitted Flight Declaration Approval")


@app.task(name="send_operational_update_message")
def send_operational_update_message(
    flight_declaration_id: str,
    message_text: str,
    level: str = LogLevel.INFO,
    timestamp: str = None,
):
    amqp_connection_url = env.get("AMQP_URL", 0)
    if not amqp_connection_url:
        logger.info("No AMQP URL specified")
        return

    if not timestamp:
        now = arrow.now()
        timestamp = now.isoformat()

    update_message = FlightDeclarationUpdateMessage(
        body=message_text, level=level, timestamp=timestamp
    )

    my_notification_helper = NotificationFactory(
        flight_declaration_id=flight_declaration_id,
        amqp_connection_url=amqp_connection_url,
    )
    my_notification_helper.declare_queue(queue_name=flight_declaration_id)
    my_notification_helper.send_message(message_details=update_message)
    logger.info("Submitted Flight Declaration Notification")


@app.task(name="submit_flight_declaration_to_dss")
def submit_flight_declaration_to_dss(flight_declaration_id: str):
    usingDss = env.get("DSS", "false")

    if usingDss == "false":
        fo = FlightDeclaration.objects.get(id=flight_declaration_id)
        # Update state of the flight operation
        fo.state = 1
        id_str = str(fo.id)
        message = {"id": id_str, "approved": True}
        _send_flight_approved_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text=message,
            level=LogLevel.INFO,
        )
        fo.save()
        return

    my_dss_opint_creator = DSSOperationalIntentsCreator(flight_declaration_id)
    start_end_time_validated = (
        my_dss_opint_creator.validate_flight_declaration_start_end_time()
    )
    logging.info("Flight Operation Validation status %s" % start_end_time_validated)

    if not start_end_time_validated:
        logging.error(
            "Flight Declaration start / end times are not valid, please check the submitted declaration, this operation will not be sent to the DSS for strategic deconfliction"
        )

        validation_not_ok_msg = "Flight Operation with ID {operation_id} did not pass time validation, start and end time may not be ahead of two hours".format(
            operation_id=flight_declaration_id
        )
        send_operational_update_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text=validation_not_ok_msg,
            level=LogLevel.ERROR,
        )
        return

    validation_ok_msg = "Flight Operation with ID {operation_id} validated for start and end time, submitting to DSS..".format(
        operation_id=flight_declaration_id
    )
    send_operational_update_message.delay(
        flight_declaration_id=flight_declaration_id,
        message_text=validation_ok_msg,
        level=LogLevel.INFO,
    )

    opint_submission_result = my_dss_opint_creator.submit_flight_declaration_to_dss()

    if opint_submission_result.status_code not in [
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    ]:
        logger.error(
            "Error in submitting Flight Declaration to the DSS %s"
            % opint_submission_result.status
        )

        dss_submission_error_msg = "Flight Operation with ID {operation_id} could not be submitted to the DSS, check the Auth server and / or the DSS URL".format(
            operation_id=flight_declaration_id
        )
        send_operational_update_message.delay(
            flight_declaration_id=flight_declaration_id,
            message_text=dss_submission_error_msg,
            level=LogLevel.ERROR,
        )
        return

    logger.info(
        "Successfully submitted Flight Declaration to the DSS %s"
        % opint_submission_result.status
    )

    submission_success_msg = "Flight Operation with ID {operation_id} submitted successfully to the DSS".format(
        operation_id=flight_declaration_id
    )
    send_operational_update_message.delay(
        flight_declaration_id=flight_declaration_id,
        message_text=submission_success_msg,
        level=LogLevel.INFO,
    )

    fo = FlightDeclaration.objects.get(id=flight_declaration_id)
    # Update state of the flight operation
    fo.state = 1

    submission_state_updated_msg = "Flight Operation with ID {operation_id} has a updated state: Accepted. ".format(
        operation_id=flight_declaration_id
    )
    send_operational_update_message.delay(
        flight_declaration_id=flight_declaration_id,
        message_text=submission_state_updated_msg,
        level=LogLevel.INFO,
    )
    fo.save()
    logging.info(
        "Details of the submission status %s" % opint_submission_result.message
    )
