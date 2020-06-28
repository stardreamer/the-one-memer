from typing import Optional, Union, Callable

import redis
from redis import StrictRedis

from reddit_grabber.events import GotRedditEvent
from reddit_grabber.exceptions import RedditGrabberException
from reddit_grabber.utils import GrabberConfiguration, get_current_utc_timestamp

connection: Optional[StrictRedis] = None

url_db = "gr_urls"
phash_db = "gr_phashes"
gr_events = "grabbers.events"


def connect_to_redis(config: GrabberConfiguration) -> None:
    global connection
    connection = redis.StrictRedis(
        host=config.redis_host, port=config.redis_port, db=config.redis_db
    )


def remove_expired_submissions(func: Callable) -> Callable:
    def func_wrapper(*args, **kwargs):
        res = func(*args, **kwargs)

        if not connection:
            raise RedditGrabberException("There is no connection to ")
        current_time = int(get_current_utc_timestamp())
        connection.zremrangebyscore(url_db, "-inf", current_time)
        connection.zremrangebyscore(phash_db, "-inf", current_time)

        return res

    return func_wrapper


@remove_expired_submissions
def register_submission(
    url: Optional[str], phash: Optional[str], ttl: Optional[int]
) -> None:
    if not connection:
        raise RedditGrabberException("There is no connection to Redis")
    utc_timestamp = get_current_utc_timestamp()
    expire_time: Union[int, str] = int(utc_timestamp + ttl) if ttl else "+inf"
    if url:
        connection.zadd(url_db, {url: expire_time})

    if phash:
        connection.zadd(phash_db, {phash: expire_time})


@remove_expired_submissions
def publish_submission(event: GotRedditEvent) -> None:
    if not connection:
        raise RedditGrabberException("There is no connection to Redis")

    connection.publish(gr_events, event.as_json())


@remove_expired_submissions
def url_was_already_processed(url: Optional[str]) -> bool:
    if not connection:
        raise RedditGrabberException("There is no connection to Redis")

    if not url:
        return False

    return (connection.zscore(url_db, url) is not None)


@remove_expired_submissions
def phash_was_already_processed(phash: Optional[str]) -> bool:
    if not connection:
        raise RedditGrabberException("There is no connection to Redis")

    if not phash:
        return False

    return connection.zscore(phash_db, phash) is not None
