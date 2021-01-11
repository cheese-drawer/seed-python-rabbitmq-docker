"""
Simplify connecting to the RabbitMQ broker
"""

import os
import pika
from dotenv import load_dotenv

# load environment variables from secrets
load_dotenv(os.path.abspath('app/.secrets'))

# setup broker credentials using secrets or defaults
_BROKER_USER = os.getenv('BROKER_USER', 'guest')
_BROKER_PASS = os.getenv('BROKER_PASS', 'guest')
print(f'creating credentials with user {_BROKER_USER} & pass {_BROKER_PASS}')
_credentials = pika.PlainCredentials(_BROKER_USER, _BROKER_PASS)

# create connection, assumes broker available at
# default 5672 port on localhost & using credentials
# loaded from secrets
_parameters = pika.ConnectionParameters('localhost', 5672, '/', _credentials)


def connect():
    return pika.BlockingConnection(_parameters)
