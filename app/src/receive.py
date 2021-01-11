#!/usr/bin/env/python
"""
Simple, naive, consumer
"""

import sys
import os
import pika
from dotenv import load_dotenv

# load environment variables from secrets
load_dotenv(os.path.abspath('app/.secrets'))

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


def handle_task(channel, method, properties, body):
    """Simple task handler"""
    print(f' [x] Received {body}')


# setup handler
channel.basic_consume(
    queue='hello',
    on_message_callback=handle_task,
    auto_ack=True,
)


def run():
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('Exiting consumer...')
        connection.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
