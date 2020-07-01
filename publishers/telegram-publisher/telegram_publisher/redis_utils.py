from threading import Thread
from typing import Optional, Callable, List, Union

import redis
from redis import StrictRedis

from telegram_publisher.events import get_event_from_string
from telegram_publisher.exceptions import TelegramPublisherException
from telegram_publisher.utils import PublisherConfiguration, get_current_utc_timestamp

url_db: Optional[str] = None
vt_events = "voters.events"
connection: Optional[StrictRedis] = None

events_to_process_queue: Optional[str] = None


def connect_to_redis(config: PublisherConfiguration) -> None:
    global connection
    global url_db
    global events_to_process_queue
    if connection is not None:
        return

    events_to_process_queue = f"{config.service_id}_ev_q"
    url_db = f"{config.service_id}_url_db"

    connection = redis.StrictRedis(
        host=config.redis_host, port=config.redis_port, db=config.redis_db
    )


def remove_expired_values(func: Callable) -> Callable:
    def func_wrapper(*args, **kwargs):
        res = func(*args, **kwargs)

        if not connection:
            raise TelegramPublisherException("There is no connection to Redis")
        current_time = int(get_current_utc_timestamp())
        connection.zremrangebyscore(url_db, "-inf", current_time)

        return res

    return func_wrapper


def subscribe(channel: str, handler: Callable) -> Thread:
    if not connection:
        raise TelegramPublisherException("There is no connection to Redis")

    p = connection.pubsub()
    p.subscribe(**{channel: handler})

    return p.run_in_thread(sleep_time=0.001)


def subscribe_to_voter_events(handler: Callable) -> Thread:
    return subscribe(vt_events, handler)


@remove_expired_values
def push_vt_event(event: str, accepted_tags: List[str]) -> None:
    if not accepted_tags:
        connection.rpush(events_to_process_queue, event)
    else:
        ev = get_event_from_string(event)
        all_tags = ev.all_tags
        if all([at in all_tags for at in accepted_tags]):
            connection.rpush(events_to_process_queue, event)


@remove_expired_values
def pop_vt_event() -> Optional[str]:
    return connection.lpop(events_to_process_queue)


@remove_expired_values
def cache_url(url: str, ttl: Optional[int]) -> None:
    expire_time: Union[int, str] = int(
        get_current_utc_timestamp() + ttl
    ) if ttl else "+inf"
    connection.zadd(url_db, {url: expire_time})


@remove_expired_values
def trim_queue(max_len: Optional[int]) -> None:
    if not max_len:
        return

    connection.ltrim(events_to_process_queue, 0, max_len if max_len > 0 else 1)


@remove_expired_values
def url_was_already_processed(url: Optional[str]) -> bool:
    if not connection:
        raise TelegramPublisherException("There is no connection to Redis")

    if not url:
        return False

    return connection.zscore(url_db, url) is not None
