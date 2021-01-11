#!/home/andrew/dev/cheese-drawer/seed-python-rabbitmq-docker/.env/bin/python
"""
Simple, naive, producer
"""

import sys
import pika
from connect import connect

# use connection from connection configuration package
connection = connect()

# create channel on connection
channel = connection.channel()

# change channel to durable, requires renaming it
# because a channel can't be modified after it's been declared
CHANNEL_NAME = 'task_queue'
channel.queue_declare(queue=CHANNEL_NAME, durable=True)

# send message from cli args
MESSAGE = ''.join(sys.argv[1:])

channel.basic_publish(
    exchange='',
    routing_key=CHANNEL_NAME,
    # encode as bytes to match expected type
    body=MESSAGE.encode('UTF8'),
    # make message persistent
    properties=pika.BasicProperties(
        delivery_mode=2
    )
)

print(f' [x] Sent {MESSAGE}')

# close the broker connection
connection.close()
