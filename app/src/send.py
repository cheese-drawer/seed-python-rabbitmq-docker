#!/home/andrew/dev/cheese-drawer/seed-python-rabbitmq-docker/.env/bin/python
"""
Simple, naive, producer
"""

import sys
from connect import connect

# use connection from connection configuration package
connection = connect()

# create channel on connection
channel = connection.channel()

# declare an exchange with a fanout, or pub-sub, model
EXCHANGE_NAME = 'logs'
channel.exchange_declare(
    exchange=EXCHANGE_NAME,
    exchange_type='fanout'
)

# a producer doesn't care a bout what queue they're publishing
# too in a fanout model; instead they want their task to go to
# all available queues simultaneously on the exchange

# send message from cli args
MESSAGE = ''.join(sys.argv[1:])

channel.basic_publish(
    exchange=EXCHANGE_NAME,
    routing_key='',
    body=MESSAGE.encode('UTF8'),
)

print(f' [x] Sent {MESSAGE}')

# close the broker connection
connection.close()
