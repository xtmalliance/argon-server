import logging
from os import environ as env

from django.apps import AppConfig
from dotenv import find_dotenv, load_dotenv

from notification_operations.notification_helper import InitialNotificationFactory

load_dotenv(find_dotenv())
logger = logging.getLogger("django")


class FlightDeclarationOperationsConfig(AppConfig):
    name = "flight_declaration_operations"

    def ready(self):
        amqp_connection_url = env.get("AMQP_URL", 0)

        if amqp_connection_url:
            my_notification_helper = InitialNotificationFactory(
                amqp_connection_url=amqp_connection_url,
                exchange_name="operational_events",
            )
            my_notification_helper.declare_exchange()
            my_notification_helper.close()
            logger.info("Exchange declared on AMQP...")
        else:
            logger.info("AMQP not set, skipping exchange creation..")
