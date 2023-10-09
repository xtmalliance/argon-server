import logging
from os import environ as env

import arrow
from dotenv import find_dotenv, load_dotenv

from flight_blender.celery import app

from .data_definitions import NotificationLevel, NotificationMessage
from .notification_helper import NotificationFactory

logger = logging.getLogger("django")
load_dotenv(find_dotenv())


@app.task(name="send_operational_update_message")
def send_operational_update_message(
    flight_declaration_id: str,
    message_text: str,
    level: NotificationLevel = NotificationLevel.INFO,
    timestamp: str = None,
    log_message: str = "No log message provided",
):
    amqp_connection_url = env.get("AMQP_URL", 0)
    if not amqp_connection_url:
        logger.info("No AMQP URL specified")
        return

    if not timestamp:
        now = arrow.now()
        timestamp = now.isoformat()

    update_message = NotificationMessage(
        body=message_text, level=level, timestamp=timestamp
    )

    my_notification_helper = NotificationFactory(
        flight_declaration_id=flight_declaration_id,
        amqp_connection_url=amqp_connection_url,
    )
    my_notification_helper.declare_queue(queue_name=flight_declaration_id)
    my_notification_helper.send_message(message_details=update_message)
    logger.info(log_message)
