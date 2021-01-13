"""
Simple "server" in RabbitMQ

Listens for incoming messages on a couple of topics, routes work
accordingly, then sends responses when necessary.
"""

import sys
from messenger import Messenger
from logic import do_a_thing, do_a_longer_thing, log_everything

# initialize the messenger class
# sets up the RabbitMQ connection & prepares for commands
server = Messenger()

# Define routes:
#
# Not exactly routes, but similar to routes in flask, Express et. al.


def everything_handler(body: str, topic: str) -> None:
    print(log_everything(body, topic))


server.setup_consumer(['#'], everything_handler)


def short_handler(body: str, topic: str) -> None:
    server.produce(do_a_thing(body), 'processed')


server.setup_consumer(['short'], short_handler)


def long_handler(body: str, topic: str) -> None:
    server.produce(
        do_a_longer_thing(
            body,
            int(topic.split('.')[1])
        ),
        'processed'
    )


server.setup_consumer(['long.*'], long_handler)


def run() -> None:
    print('Starting consumers...')
    server.start_consuming()


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('Exiting consumer.')
        server.close()
        sys.exit(0)
