from threading import Thread
from typing import Optional, Dict, Callable, Union

import redis
from redis import StrictRedis

from telegram_voter.exceptions import TelegramVoterException
from telegram_voter.utils import VoterConfiguration, get_current_utc_timestamp
from telegram_voter.votes import Vote

gr_events = "grabbers.events"
vt_events = "voters.events"

votes_ttl: Optional[str] = None
votes: Optional[str] = None

up_voters: Optional[str] = None
down_voters: Optional[str] = None

events_to_process_stack: Optional[str] = None

connection: Optional[StrictRedis] = None


def connect_to_redis(config: VoterConfiguration) -> None:
    global connection
    global events_to_process_stack
    global votes_ttl
    global votes
    global up_voters
    global down_voters
    if connection is not None:
        return

    events_to_process_stack = f"{config.service_id}_ev_st"
    votes_ttl = f"{config.service_id}_votes_ttl"
    votes = f"{config.service_id}_votes"
    up_voters = f"{config.service_id}_upv"
    down_voters = f"{config.service_id}_dwv"

    connection = redis.StrictRedis(
        host=config.redis_host, port=config.redis_port, db=config.redis_db
    )


def remove_expired_votes(func: Callable) -> Callable:
    def func_wrapper(*args, **kwargs):
        res = func(*args, **kwargs)

        if not connection:
            raise TelegramVoterException("There is no connection to ")
        current_time = int(get_current_utc_timestamp())

        expired_votes = connection.zrangebyscore(votes_ttl, "-inf", current_time)

        if expired_votes:
            connection.hdel(votes, expired_votes)
            connection.zremrangebyscore(votes_ttl, "-inf", current_time)

        return res

    return func_wrapper


@remove_expired_votes
def vote(vid: str, voter: int, up: bool) -> Optional[Vote]:
    v = get_vote(vid)

    if not v:
        return

    if v.finished:
        return v

    if up:
        if voter in v.against_votes:
            connection.zincrby(down_voters, -1, voter)
        v.upvote(voter)
        connection.zincrby(up_voters, 1, voter)
    else:
        if voter in v.for_votes:
            connection.zincrby(up_voters, -1, voter)
        v.downvote(voter)
        connection.zincrby(down_voters, 1, voter)

    connection.hset(votes, vid, v.as_json())

    return v


def upvote(vid: str, voter: int) -> Optional[Vote]:
    return vote(vid, voter, True)


def downvote(vid: str, voter: int) -> Optional[Vote]:
    return vote(vid, voter, False)


def move_vote(vt: Vote, new_vid: str) -> Optional[Vote]:
    original_vote = get_vote(vt.vid)

    if not original_vote:
        return None

    connection.hdel(votes, original_vote.vid)
    ttl = connection.zscore(votes_ttl, original_vote.vid)

    connection.zrem(votes_ttl, original_vote.vid)
    vt.vid = new_vid
    connection.zadd(votes_ttl, vt.vid, ttl)
    connection.hset(votes, vt.vid, vt.as_json())

    return vt


@remove_expired_votes
def register_vote(vote: Vote) -> None:
    if not connection:
        raise TelegramVoterException("There is no connection to Redis")

    try:
        js = vote.as_json()

        connection.zadd(votes_ttl, {vote.vid: "+inf"})

        connection.hset(votes, vote.vid, js)
    except TypeError as e:
        raise TelegramVoterException(str(e))


@remove_expired_votes
def update_vote(vote: Vote, ttl: Optional[int]) -> None:
    if not connection:
        raise TelegramVoterException("There is no connection to Redis")

    if vote.finished:
        utc_timestamp = get_current_utc_timestamp()
        expire_time: Union[int, str] = int(utc_timestamp + ttl) if ttl else "+inf"
        connection.zadd(votes_ttl, {vote.vid: expire_time})

    connection.hset(votes, vote.vid, vote.as_json())


@remove_expired_votes
def get_vote(vid: str) -> Optional[Vote]:
    s_vote = connection.hget(votes, vid)
    return Vote.from_str(s_vote) if s_vote else None


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
