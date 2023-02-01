#!/usr/bin/env python
import pika, sys, os

import argparse
from typing import List
from os import environ as env
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


def parse_args(argv: List[str]):
  parser = argparse.ArgumentParser(description='Retrieve an access token')
  parser.add_argument(
    '--queue', action='store', dest='queue', type=str,
    help='The queue must be the Flight Declaration ID where updates to the flight intent will be sent.')
  
  return parser.parse_args(argv)


def main(queue_id):  
    amqp_connection_url = env.get('AMQP_URL', 'localhost')
    params = pika.URLParameters(amqp_connection_url)                   
    connection = pika.BlockingConnection(params)
    
    channel = connection.channel()
    connection = pika.BlockingConnection(params)    
    channel = connection.channel()

    channel.queue_declare(queue=queue_id)

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body.decode())

    channel.basic_consume(queue=queue_id, on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    args = parse_args(sys.argv[1:])

    if args.queue is None:
        print ("Please set a ID of the Flight Declaration where operational updates will be sent. e.g. --queue 'bc0af3d8-c40a-4544-91dc-b529193d6a18'")
        sys.exit()

    try:
        main(args.queue)
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)