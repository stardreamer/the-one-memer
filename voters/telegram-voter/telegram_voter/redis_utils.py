from enum import Enum, auto
from threading import Thread
from typing import Optional, Dict, Callable, Union, Tuple, List

import redis
from redis import StrictRedis

from telegram_voter.events import TgApprovedEvent, get_event_from_string
from telegram_voter.exceptions import TelegramVoterException
from telegram_voter.utils import VoterConfiguration, get_current_utc_timestamp
from telegram_voter.votes import Vote, VoteAttemptResult

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
def vote(mid: int, voter: int, up: bool) -> Tuple[Optional[Vote], VoteAttemptResult]:
    v = get_vote(mid)

    if not v:
        return None, VoteAttemptResult.VoteWasFinished

    if v.finished:
        return v, VoteAttemptResult.VoteWasFinished

    if up:
        if voter in v.against_votes:
            connection.zincrby(down_voters, -1, voter)
        res = v.upvote(voter)
        connection.zincrby(up_voters, 1, voter)
    else:
        if voter in v.for_votes:
            connection.zincrby(up_voters, -1, voter)
        res = v.downvote(voter)
        connection.zincrby(down_voters, 1, voter)

    connection.hset(votes, mid, v.as_json())

    return v, res


def upvote(mid: int, voter: int) -> Tuple[Optional[Vote], VoteAttemptResult]:
    return vote(mid, voter, True)


def downvote(mid: int, voter: int) -> Tuple[Optional[Vote], VoteAttemptResult]:
    return vote(mid, voter, False)


def move_vote(vt: Vote, new_vid: int) -> Optional[Vote]:
    original_vote = get_vote(vt.mid)

    if not original_vote:
        return None

    connection.hdel(votes, original_vote.mid)
    ttl = connection.zscore(votes_ttl, original_vote.mid)

    connection.zrem(votes_ttl, original_vote.mid)
    vt.mid = new_vid
    connection.zadd(votes_ttl, vt.mid, ttl)
    connection.hset(votes, vt.mid, vt.as_json())

    return vt


@remove_expired_votes
def register_vote(vote: Vote) -> None:
    if not connection:
        raise TelegramVoterException("There is no connection to Redis")

    try:
        js = vote.as_json()

        connection.zadd(votes_ttl, {vote.mid: "+inf"})

        connection.hset(votes, vote.mid, js)
    except TypeError as e:
        raise TelegramVoterException(str(e))


@remove_expired_votes
def update_vote(vote: Vote, ttl: Optional[int]) -> None:
    if not connection:
        raise TelegramVoterException("There is no connection to Redis")

    if vote.finished:
        utc_timestamp = get_current_utc_timestamp()
        expire_time: Union[int, str] = int(utc_timestamp + ttl) if ttl else "+inf"
        connection.zadd(votes_ttl, {vote.mid: expire_time})

    connection.hset(votes, vote.mid, vote.as_json())


@remove_expired_votes
def get_vote(mid: int) -> Optional[Vote]:
    s_vote = connection.hget(votes, mid)
    return Vote.from_str(s_vote) if s_vote else None


def subscribe(channel: str, handler: Callable) -> Thread:
    if not connection:
        raise TelegramVoterException("There is no connection to redis")

    p = connection.pubsub()
    p.subscribe(**{channel: handler})

    return p.run_in_thread(sleep_time=0.001)


def subscribe_to_grabber_events(handler: Callable) -> Thread:
    return subscribe(gr_events, handler)


def push_gr_event(event: str, accepted_tags: List[str]) -> None:
    if not accepted_tags:
        connection.lpush(events_to_process_stack, event)
    else:
        ev = get_event_from_string(event)

        if all([at in ev.tags for at in accepted_tags]):
            connection.lpush(events_to_process_stack, event)


def pop_gr_event() -> Optional[str]:
    return connection.lpop(events_to_process_stack)


def clear_gr_event_stack() -> None:
    connection.delete(events_to_process_stack)


@remove_expired_votes
def publish_approved_submission(v: Vote, tags: List[str]) -> None:
    if not connection:
        raise TelegramVoterException("There is no connection to Redis")

    event = TgApprovedEvent.from_vote(v, tags)

    connection.publish(vt_events, event.as_json())
