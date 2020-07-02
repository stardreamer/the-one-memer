import datetime
import os
from dataclasses import dataclass
from typing import List, Optional

from telegram_publisher.exceptions import TelegramPublisherException


def str_as_bool(l: str) -> bool:
    return l.lower().strip() == "true"


def get_current_utc_timestamp() -> float:
    dt = datetime.datetime.now()
    return dt.replace(tzinfo=datetime.timezone.utc).timestamp()


@dataclass
class PublisherConfiguration:
    tags: List[str]
    redis_host: str
    redis_port: int
    redis_db: int
    redis_internal_ttl: Optional[int]
    service_id: str
    mature_content_allowed: bool
    telegram_token: str
    target_channel: int
    publishing_interval: int
    accepted_voters: List[str]
    with_description: bool
    max_queue_len: Optional[int]
    max_delay: Optional[int]
    min_delay: Optional[int]


def get_configuration() -> PublisherConfiguration:
    tp_id: str = os.environ.get("TP_ID")

    telegram_token: str = os.environ.get("TP_API_TOKEN")

    target_channel: str = os.environ.get("TP_TARGET_CHANNEL")

    unfilled_req_parameters: List[str] = []

    if not tp_id:
        unfilled_req_parameters.append("TP_ID")

    if not telegram_token:
        unfilled_req_parameters.append("TP_API_TOKEN")

    if not target_channel:
        unfilled_req_parameters.append("TP_TARGET_GROUP")

    target_channel: int = int(target_channel)

    if unfilled_req_parameters:
        raise TelegramPublisherException(
            f"You have to set all of the environment variables: {','.join(unfilled_req_parameters)}"
        )

    tags_line: Optional[str] = os.environ.get("TP_TAGS")

    tags: List[str] = []
    if tags_line:
        tags.extend(tags_line.split(";"))
        tags = list(set(tags))

    accepted_voters_line: Optional[str] = os.environ.get("TP_ACCEPTED_VOTERS")

    accepted_voters: List[str] = []
    if accepted_voters_line:
        accepted_voters.extend(accepted_voters_line.split(";"))
        accepted_voters = list(set(accepted_voters))

    mature_content_allowed: Optional[str] = os.environ.get("TP_MATURE_ALLOWED")
    mature_content_allowed: bool = str_as_bool(
        mature_content_allowed
    ) if mature_content_allowed else False

    with_description: Optional[str] = os.environ.get("TP_WITH_DESCRIPTION")
    with_description: bool = str_as_bool(
        with_description
    ) if with_description else False

    publishing_interval: Optional[str] = os.environ.get("TP_PUBLISHING_INTERVAL")
    publishing_interval: int = int(publishing_interval) if publishing_interval else 300

    max_delay: Optional[str] = os.environ.get("TP_MAX_DELAY")
    max_delay: Optional[int] = abs(int(max_delay)) if max_delay else None

    min_delay: Optional[str] = os.environ.get("TP_MIN_DELAY")
    min_delay: Optional[int] = abs(int(min_delay)) if min_delay else None

    max_queue_len: Optional[str] = os.environ.get("TP_MAX_QUEUE_LEN")
    max_queue_len: Optional[int] = int(max_queue_len) if max_queue_len else None

    redis_host: str = os.environ.get("TP_REDIS_HOST")
    redis_host = redis_host if redis_host else "localhost"

    redis_port_line: str = os.environ.get("TP_REDIS_PORT")
    redis_db_line: str = os.environ.get("TP_REDIS_DB")
    redis_internal_ttl_line: str = os.environ.get("TP_REDIS_INTERNAL_TTL")

    redis_port: int = int(redis_port_line) if redis_port_line else 6379
    redis_db: int = int(redis_db_line) if redis_db_line else 0
    redis_internal_ttl: Optional[int] = int(
        redis_internal_ttl_line
    ) if redis_internal_ttl_line else None

    return PublisherConfiguration(
        tags=tags,
        redis_port=redis_port,
        redis_db=redis_db,
        redis_host=redis_host,
        service_id=tp_id,
        redis_internal_ttl=redis_internal_ttl,
        mature_content_allowed=mature_content_allowed,
        target_channel=target_channel,
        telegram_token=telegram_token,
        publishing_interval=publishing_interval,
        accepted_voters=accepted_voters,
        with_description=with_description,
        max_queue_len=max_queue_len,
        max_delay=max_delay,
        min_delay=min_delay,
    )
