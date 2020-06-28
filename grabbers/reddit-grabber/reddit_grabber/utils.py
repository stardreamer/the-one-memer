import datetime
import os
from dataclasses import dataclass
from datetime import timezone
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from urllib.parse import urlparse

import imagehash
import requests
from PIL import Image

from reddit_grabber.exceptions import RedditGrabberException


class FiniteList(List):
    def __init__(self, max_len: int):
        super().__init__()
        self.max_len = max_len

    def append(self, item):
        list.append(self, item)
        if len(self) > 5:
            del self[0]


@dataclass
class GrabberConfiguration:
    client_id: str
    client_secret: str
    user_agent: str
    subreddit_name: str
    tags: List[str]
    redis_host: str
    redis_port: int
    redis_db: int
    redis_internal_ttl: Optional[int]
    service_id: str
    mode: str
    post_window: int
    sleep_time: int
    thread_count: int
    post_history_cache_len: int
    mature_content_allowed: bool

    def stream_mode(self) -> bool:
        return self.mode == "stream"


def get_current_utc_timestamp() -> float:
    dt = datetime.datetime.now()
    return dt.replace(tzinfo=timezone.utc).timestamp()


def is_image(submission) -> bool:
    return hasattr(submission, "post_hint") and submission.post_hint == "image"


def get_extension(submission) -> str:
    return os.path.splitext(urlparse(submission.url).path)[1]


def download_submission(submission) -> Path:
    ext = get_extension(submission)
    r = requests.get(submission.url, allow_redirects=True)

    with open(f"img/{submission.id}.{ext}", "wb") as f:
        f.write(r.content)

    return Path(f"img/{submission.id}.{ext}")


def get_image(submission) -> Image.Image:
    r = requests.get(submission.url, allow_redirects=True)
    return Image.open(BytesIO(r.content))


def get_hash(im: Image) -> imagehash.ImageHash:
    return imagehash.phash(im)


def validate_mode(mode: str) -> None:
    if mode == "stream":
        return

    if mode == "hot":
        return

    if mode == "rising":
        return

    raise RedditGrabberException(
        f"Unknown mode {mode}. Acceptable values for RG_MODE are: stream, hot, rising"
    )


def str_as_bool(l: str) -> bool:
    if l.lower().strip() == "true":
        return True

    return False


def get_configuration() -> GrabberConfiguration:
    client_id: str = os.environ.get("RG_CLIENT_ID")
    client_secret: str = os.environ.get("RG_CLIENT_SECRET")
    user_agent: str = os.environ.get("RG_USER_AGENT")
    rg_id: str = os.environ.get("RG_ID")

    unfilled_req_parameters: List[str] = []

    if not client_id:
        unfilled_req_parameters.append("RG_CLIENT_ID")
    if not client_secret:
        unfilled_req_parameters.append("RG_CLIENT_SECRET")
    if not user_agent:
        unfilled_req_parameters.append("RG_USER_AGENT")
    if not rg_id:
        unfilled_req_parameters.append("RG_ID")

    if unfilled_req_parameters:
        raise RedditGrabberException(
            f"You have to set all of the environment variables: {','.join(unfilled_req_parameters)}"
        )

    subreddit_name: str = os.environ.get("RG_SUBREDDIT")
    subreddit_name = subreddit_name if subreddit_name else "all"
    tags_line: Optional[str] = os.environ.get("RG_TAGS")
    tags: List[str] = ["img", "reddit"]
    if tags_line:
        tags.extend(tags_line.split(";"))

    mode: Optional[str] = os.environ.get("RG_MODE")

    mode: str = mode.lower() if mode else "stream"

    validate_mode(mode)

    post_limit: Optional[str] = os.environ.get("RG_POST_WINDOW")
    post_limit: int = int(post_limit) if post_limit else 100

    sleep_time: Optional[str] = os.environ.get("RG_SLEEP_TIME")
    sleep_time: int = int(sleep_time) if sleep_time else 600

    thread_count: Optional[str] = os.environ.get("RG_THREAD_NUMBER")
    thread_count: int = int(thread_count) if thread_count else 4

    history_cache_l: Optional[str] = os.environ.get("RG_H_CACHE_LEN")
    history_cache_l: int = int(history_cache_l) if history_cache_l else 1000

    mature_content_allowed: Optional[str] = os.environ.get("RG_MATURE_ALLOWED")
    mature_content_allowed: bool = str_as_bool(
        mature_content_allowed
    ) if mature_content_allowed else False

    redis_host: str = os.environ.get("RG_REDIS_HOST")
    redis_host = redis_host if redis_host else "localhost"

    redis_port_line: str = os.environ.get("RG_REDIS_PORT")
    redis_db_line: str = os.environ.get("RG_REDIS_DB")
    redis_internal_ttl_line: str = os.environ.get("RG_REDIS_INTERNAL_TTL")

    redis_port: int = int(redis_port_line) if redis_port_line else 6379
    redis_db: int = int(redis_db_line) if redis_db_line else 0
    redis_internal_ttl: Optional[int] = int(
        redis_internal_ttl_line
    ) if redis_internal_ttl_line else None

    return GrabberConfiguration(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        subreddit_name=subreddit_name,
        tags=tags,
        redis_port=redis_port,
        redis_db=redis_db,
        redis_host=redis_host,
        service_id=rg_id,
        redis_internal_ttl=redis_internal_ttl,
        mode=mode,
        sleep_time=sleep_time,
        post_window=post_limit,
        thread_count=thread_count,
        post_history_cache_len=history_cache_l,
        mature_content_allowed=mature_content_allowed,
    )
