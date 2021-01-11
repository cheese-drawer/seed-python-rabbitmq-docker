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

# change channel to durable, requires renaming it
# because a channel can't be modified after it's been declared
CHANNEL_NAME = 'task_queue'
channel.queue_declare(queue=CHANNEL_NAME, durable=True)


def handle_task(channel, method, properties, body):
    """Simple task handler

    Simulates complex task via time.sleep
    """
    print(f' [x] Received {body.decode()}')

    time.sleep(body.count(b'.'))

    print(" [x] Done")

    # moved acknowledgment to inside the handler
    # this allows a task that was never completed to be
    # reassigned by the broker if this worker fails
    channel.basic_ack(delivery_tag=method.delivery_tag)


# tells this worker to only grab one task at a time,
# waiting until done with it to grab the next
channel.basic_qos(prefetch_count=1)
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
