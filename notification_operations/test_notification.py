import os
from os import environ as env
from unittest.mock import MagicMock, call, patch

from django.test import TestCase

from notification_operations import notification
from notification_operations.data_definitions import NotificationLevel
from notification_operations.notification_helper import InitialNotificationFactory


class NotificationSendingTests(TestCase):
    @patch("notification_operations.notification.logger", autospec=True)
    @patch.dict(os.environ, {"AMQP_URL": ""})
    def test_no_amqp_url(self, mock_notification_logger):
        mock_notification_logger.info = MagicMock()
        notification.send_operational_update_message(
            flight_declaration_id="0001",
            message_text="Test Message",
            level=NotificationLevel.INFO,
        )
        mock_notification_logger.info.assert_called_once_with("No AMQP URL specified")

    @patch("notification_operations.notification.logger", autospec=True)
    def test_notification_without_timestamp_without_logger_message(
        self, mock_notification_logger
    ):
        mock_notification_logger.info = MagicMock()
        notification.send_operational_update_message(
            flight_declaration_id="0001",
            message_text="Test Message",
            level=NotificationLevel.INFO,
        )
        mock_notification_logger.info.assert_called_once_with("No log message provided")

    @patch("notification_operations.notification.logger", autospec=True)
    def test_notification_without_timestamp_with_logger_message(
        self, mock_notification_logger
    ):
        mock_notification_logger.info = MagicMock()
        notification.send_operational_update_message(
            flight_declaration_id="0001",
            message_text="Test Message",
            level=NotificationLevel.ERROR,
            log_message="This is a test log message",
        )
        mock_notification_logger.info.assert_called_once_with(
            "This is a test log message"
        )

    @patch("notification_operations.notification.logger", autospec=True)
    def test_notification_without_timestamp(self, mock_notification_logger):
        mock_notification_logger.info = MagicMock()
        notification.send_operational_update_message(
            flight_declaration_id="0001",
            message_text="Test Message",
            level=NotificationLevel.ERROR,
            timestamp="Test time string",
            log_message="This is a test log message",
        )
        mock_notification_logger.info.assert_called_once_with(
            "This is a test log message"
        )

    @patch("notification_operations.notification.logger", autospec=True)
    @patch("notification_operations.notification_helper.logger", autospec=True)
    def test_notification_with_all_logs(
        self, mock_notification_helper_logger, mock_notification_logger
    ):
        mock_notification_logger.info = MagicMock()
        mock_notification_helper_logger.info = MagicMock()
        notification.send_operational_update_message(
            flight_declaration_id="0001",
            message_text="Test Message",
            level=NotificationLevel.CRITICAL,
            timestamp="Test time string",
            log_message="This is a test log message",
        )

        # Logs from notification_helper
        mock_notification_helper_logger.info.assert_has_calls(
            calls=[
                call("Trying to declare queue (0001)..."),
                call(
                    "Trying to bind queue (operational_events) with routing key (0001)..."
                ),
                call(
                    'Sent message. Exchange: operational_events, Routing Key: 0001, Body: {"body": "Test Message", "level": "critical", "timestamp": "Test time string"}'
                ),
            ],
            any_order=False,
        )
        # Logs from notification

        mock_notification_logger.info.assert_called_once_with(
            "This is a test log message"
        )


class NotificationExchangeInitialTests(TestCase):
    def setUp(self):
        _amqp_connection_url = env.get("AMQP_URL", 0)
        self.notification_declaration = InitialNotificationFactory(
            amqp_connection_url=_amqp_connection_url,
            exchange_name="operational_events",
        )

    @patch("notification_operations.notification_helper.logger", autospec=True)
    def test_declare_exchange(self, mock_notification_helper_logger):
        mock_notification_helper_logger.info = MagicMock()
        self.notification_declaration.declare_exchange()
        self.notification_declaration.close()
        mock_notification_helper_logger.info.assert_has_calls(
            calls=[
                call("Trying to declare exchange (operational_events)..."),
                call("Trying to close connection..."),
            ],
            any_order=False,
        )
