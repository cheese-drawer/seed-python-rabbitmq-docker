#!/home/andrew/dev/cheese-drawer/seed-python-rabbitmq-docker/.env/bin/python
"""
Simple, naive, producer
"""

from typing import List, Tuple
import sys
from connect import Producer


def parse_input(user_input: List[str]) -> Tuple[str, str]:
    if len(user_input) > 3:
        return ('.'.join(user_input[1:3]), ' '.join(user_input[3:]))

    return ('anonymous.info', ' '.join(user_input[1:]))


SEVERITY, MESSAGE = parse_input(sys.argv)

Producer().send_once(MESSAGE, SEVERITY)

print(f' [x] Sent {SEVERITY}: {MESSAGE}')
