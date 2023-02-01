import pika, os, signal, sys
from .data_definitions import FlightDeclarationUpdateMessage
import logging
import json
from dataclasses import asdict
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
logger = logging.getLogger('django')

def signal_handler(signal, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


class NotificationFactory():
    '''
    A class to publish messages to the AMQP queue    '''

    def __init__(self, flight_declaration_id:str, amqp_connection_url: str):     
        params = pika.URLParameters(amqp_connection_url)                   
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.exchange = 'operational_updates'
        self.flight_declaration_id = flight_declaration_id

    def send_message(self, message_details:FlightDeclarationUpdateMessage):
        msg_details = json.dumps(asdict(message_details))
        self.channel.basic_publish(exchange=self.exchange, routing_key=self.flight_declaration_id, body=msg_details)
        logger.info(f"Sent message. Exchange: {self.exchange}, Routing Key: {self.flight_declaration_id}, Body: {msg_details}")

    def declare_queue(self, queue_name):
        logger.info(f"Trying to declare queue({queue_name})...")
        self.channel.queue_declare(queue=queue_name)
        
    def close(self):
        self.channel.close()
        self.connection.close()