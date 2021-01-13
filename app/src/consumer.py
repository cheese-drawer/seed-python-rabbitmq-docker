#!/home/andrew/dev/cheese-drawer/seed-python-rabbitmq-docker/.env/bin/python
"""
Simple, naive, consumer
"""

import sys
import time
from connect import Consumer

consumer = Consumer()

# severities are supplied at execution time by the user
SEVERITIES = sys.argv[1:]

if not SEVERITIES:
    sys.stderr.write(f'Usage: {sys.argv[0]} n * [source.severity]')
    sys.exit(1)

# create a queue binding for each severity supplied
# using the severity as the routing_key
for severity in SEVERITIES:
    print(f'listening for { severity }')

    consumer.queue_bind(severity)


def handle_task(body: str, topic: str) -> None:
    """Simple task handler

    Simulates complex task via time.sleep
    """
    print(f' [x] {topic}:{body}')

    time.sleep(body.count('.'))

    print(" [x] Done")


def run():
    print(' [*] Waiting for messages. To exit press CTRL+C')
    consumer.consume(handle_task)


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('Exiting consumer...')
        consumer.close()
        sys.exit(0)
