#!/usr/bin/env/python
"""
Simple, naive, producer
"""

import os
import pika
from dotenv import load_dotenv

# load environment variables from secrets
load_dotenv('.secrets')

# setup broker credentials using secrets or defaults
BROKER_USER = os.getenv('BROKER_USER', 'guest')
BROKER_PASS = os.getenv('BROKER_PASS', 'guest')
print(f'creating credentials with user {BROKER_USER} & pass {BROKER_PASS}')
credentials = pika.PlainCredentials(BROKER_USER, BROKER_PASS)

# create connection, assumes broker available at
# default 5672 port on localhost & using credentials
# loaded from secrets
parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)

# create channel on connection
channel = connection.channel()

# name channel hello
channel.queue_declare(queue='hello')

# send message
MESSAGE = 'Hello world!'
channel.basic_publish(
    exchange='',
    routing_key='hello',
    body=MESSAGE.encode('UTF8')  # encode as bytes to match expected type
)

print(f' [x] Sent {MESSAGE}')

# close the broker connection
connection.close()
