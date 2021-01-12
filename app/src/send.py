#!/home/andrew/dev/cheese-drawer/seed-python-rabbitmq-docker/.env/bin/python
"""
Simple, naive, producer
"""

from typing import List, Tuple
import sys
from connect import connect

# use connection from connection configuration package
connection = connect()

# create channel on connection
channel = connection.channel()

# declare an exchange with a fanout, or pub-sub, model
EXCHANGE_NAME = 'topic_logs'
channel.exchange_declare(
    exchange=EXCHANGE_NAME,
    exchange_type='topic'
)


def parse_input(user_input: List[str]) -> Tuple[str, str]:
    if len(user_input) > 3:
        return ('.'.join(user_input[1:3]), ' '.join(user_input[3:]))

    return ('anonymous.info', ' '.join(user_input[1:]))


SEVERITY, MESSAGE = parse_input(sys.argv)

print(f'severity: { SEVERITY }')
print(f'message: { MESSAGE }')

channel.basic_publish(
    exchange=EXCHANGE_NAME,
    routing_key=SEVERITY,
    body=MESSAGE.encode('UTF8'),
)

print(f' [x] Sent {SEVERITY}: {MESSAGE}')

# close the broker connection
connection.close()
