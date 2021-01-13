"""
Simple, naive, producer
"""

import sys
from messenger import Messenger


TOPIC = sys.argv[1]
MESSAGE = ' '.join(sys.argv[2:])

Messenger().produce(MESSAGE, TOPIC).close()

print(f'Sent {TOPIC}: {MESSAGE}')
