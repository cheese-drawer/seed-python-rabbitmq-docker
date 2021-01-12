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
EXCHANGE_NAME = 'logs'
channel.exchange_declare(
    exchange=EXCHANGE_NAME,
    exchange_type='fanout'
)


# using an empty queue name allows for the creation of a new,
# anonymous queue every time a producer or consumer connects
# this means that a consumer won't receive all the old messages
# from the queue upon connection, & will only begin receiving
# messages created after connection
# by assigning the queue to a variable, we can refer to it
# later, allowing us to close the queue when this worker ends
CHANNEL_NAME = ''
queue = channel.queue_declare(queue=CHANNEL_NAME, exclusive=True)
QUEUE_NAME = queue.method.queue
channel.queue_bind(
    exchange=EXCHANGE_NAME,
    queue=QUEUE_NAME
)


def handle_task(cb_channel, method, _, body):
    """Simple task handler

    Simulates complex task via time.sleep
    """
    print(f' [x] Received {body.decode()}')

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
