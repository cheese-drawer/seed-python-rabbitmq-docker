#!/home/andrew/dev/cheese-drawer/seed-python-rabbitmq-docker/.env/bin/python
"""
Simple, naive, consumer
"""

import sys
import time
from connect import connect

connection = connect()

# create channel on connection
channel = connection.channel()


# declare the same exchange as the producer
EXCHANGE_NAME = 'direct_logs'
channel.exchange_declare(
    exchange=EXCHANGE_NAME,
    exchange_type='direct'
)


# severities are supplied at execution time by the user
SEVERITIES = sys.argv[1:]

if not SEVERITIES:
    sys.stderr.write(f'Usage: {sys.argv[0]} [info] [warn] [error]')
    sys.exit(1)

# uses anonymous temporary queues again
CHANNEL_NAME = ''
queue = channel.queue_declare(queue=CHANNEL_NAME, exclusive=True)
QUEUE_NAME = queue.method.queue

# create a queue binding for each severity supplied
# using the severity as the routing_key
for severity in SEVERITIES:
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=QUEUE_NAME,
        routing_key=severity,
    )


def handle_task(cb_channel, method, _, body):
    """Simple task handler

    Simulates complex task via time.sleep
    """
    print(f' [x] {method.routing_key}:{body.decode()}')

    time.sleep(body.count(b'.'))

    print(" [x] Done")

    # moved acknowledgment to inside the handler
    # this allows a task that was never completed to be
    # reassigned by the broker if this worker fails
    cb_channel.basic_ack(delivery_tag=method.delivery_tag)


# setup handler
channel.basic_consume(
    queue=CHANNEL_NAME,
    on_message_callback=handle_task,
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
        sys.exit(0)
