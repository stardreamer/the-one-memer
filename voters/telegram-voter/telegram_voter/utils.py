import datetime
import os
from dataclasses import dataclass
from typing import List, Optional, Dict

from telegram_voter.exceptions import TelegramVoterException


def get_current_utc_timestamp() -> float:
    dt = datetime.datetime.now()
    return dt.replace(tzinfo=datetime.timezone.utc).timestamp()


def str_as_bool(l: str) -> bool:
    if l.lower().strip() == "true":
        return True

    return False


@dataclass
class VoterConfiguration:
    tags: List[str]
    redis_host: str
    redis_port: int
    redis_db: int
    redis_internal_ttl: Optional[int]
    service_id: str
    mature_content_allowed: bool
    telegram_token: str
    target_group: int
    vote_interval: int
    vote_threshold: int
    vote_throttle: float
    vote_batch_size: int


def get_configuration() -> VoterConfiguration:
    tv_id: str = os.environ.get("TV_ID")

    telegram_token: str = os.environ.get("TV_API_TOKEN")

    target_group: str = os.environ.get("TV_TARGET_GROUP")

    unfilled_req_parameters: List[str] = []

    if not tv_id:
        unfilled_req_parameters.append("TV_ID")

    if not telegram_token:
        unfilled_req_parameters.append("TV_API_TOKEN")

    if not target_group:
        unfilled_req_parameters.append("TV_TARGET_GROUP")

    target_group: int = int(target_group)

    if unfilled_req_parameters:
        raise TelegramVoterException(
            f"You have to set all of the environment variables: {','.join(unfilled_req_parameters)}"
        )

    tags_line: Optional[str] = os.environ.get("TV_TAGS")

    tags: List[str] = []
    if tags_line:
        tags.extend(tags_line.split(";"))
        tags = list(set(tags))

    mature_content_allowed: Optional[str] = os.environ.get("TV_MATURE_ALLOWED")
    mature_content_allowed: bool = str_as_bool(
        mature_content_allowed
    ) if mature_content_allowed else False

    vote_interval: Optional[str] = os.environ.get("TV_VOTE_INTERVAL")
    vote_interval: int = int(vote_interval) if vote_interval else 300

    vote_throttle: Optional[str] = os.environ.get("TV_VOTE_THROTTLE")
    vote_throttle: float = float(vote_throttle) if vote_throttle else 0.5

    vote_threshold: Optional[str] = os.environ.get("TV_VOTE_THRESHOLD")
    vote_threshold: int = int(vote_threshold) if vote_threshold else 1

    vote_batch_size: Optional[str] = os.environ.get("TV_BATCH_SIZE")
    vote_batch_size: int = int(vote_threshold) if vote_threshold else 5

    redis_host: str = os.environ.get("TV_REDIS_HOST")
    redis_host = redis_host if redis_host else "localhost"

    redis_port_line: str = os.environ.get("TV_REDIS_PORT")
    redis_db_line: str = os.environ.get("TV_REDIS_DB")
    redis_internal_ttl_line: str = os.environ.get("TV_REDIS_INTERNAL_TTL")

    redis_port: int = int(redis_port_line) if redis_port_line else 6379
    redis_db: int = int(redis_db_line) if redis_db_line else 0
    redis_internal_ttl: Optional[int] = int(
        redis_internal_ttl_line
    ) if redis_internal_ttl_line else None

    return VoterConfiguration(
        tags=tags,
        redis_port=redis_port,
        redis_db=redis_db,
        redis_host=redis_host,
        service_id=tv_id,
        redis_internal_ttl=redis_internal_ttl,
        mature_content_allowed=mature_content_allowed,
        target_group=target_group,
        vote_interval=vote_interval,
        telegram_token=telegram_token,
        vote_threshold=vote_threshold,
        vote_throttle=vote_throttle,
        vote_batch_size=vote_batch_size
    )
