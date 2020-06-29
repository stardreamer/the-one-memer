from threading import Thread
from typing import Optional, Dict, Callable

import redis
from redis import StrictRedis

from telegram_voter.exceptions import TelegramVoterException
from telegram_voter.utils import VoterConfiguration

gr_events = "grabbers.events"
vt_events = "voters.events"

events_to_process_stack: Optional[str] = None

connection: Optional[StrictRedis] = None


def connect_to_redis(config: VoterConfiguration) -> None:
    global connection
    global events_to_process_stack
    if connection is not None:
        return

    events_to_process_stack = f"{config.service_id}_ev_st"

    connection = redis.StrictRedis(
        host=config.redis_host, port=config.redis_port, db=config.redis_db
    )


def subscribe(channel: str, handler: Callable) -> Thread:
    if not connection:
        raise TelegramVoterException("There is no connection to redis")

    p = connection.pubsub()
    p.subscribe(**{channel: handler})

    return p.run_in_thread(sleep_time=0.001)


def subscribe_to_grabber_events(handler: Callable) -> Thread:
    return subscribe(gr_events, handler)


def push_gr_event(event: str) -> None:
    connection.lpush(events_to_process_stack, event)


def pop_gr_event() -> Optional[str]:
    return connection.lpop(events_to_process_stack)


def clear_gr_event_stack() -> None:
    connection.delete(events_to_process_stack)
