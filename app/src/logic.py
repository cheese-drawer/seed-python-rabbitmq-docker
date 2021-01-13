import time


def do_a_thing(an_arg: str) -> str:
    return f'{an_arg} was done'


def do_a_longer_thing(an_arg: str, another: int) -> str:
    time.sleep(another)

    return f'{an_arg} took a lot of time, but was done'


def log_everything(body: str, topic: str) -> str:
    return f'{topic}:{body} was done'
