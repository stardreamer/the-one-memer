import dataclasses
import json
from dataclasses import dataclass
from typing import List, Optional, Dict

from telegram_voter.votes import Vote


class GotEvent:
    def __init__(
        self,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None,
        e_type: Optional[str] = None,
        original_event: str = None,
    ) -> None:
        self.tags: Optional[List[str]] = tags
        self.url: Optional[str] = url
        self.e_type: Optional[str] = e_type
        self.original_event: Optional[str] = original_event

    @property
    def description(self) -> str:
        return ""

    @staticmethod
    def from_dict(d: Dict) -> "GotEvent":
        js = json.dumps(d, separators=(",", ":"))

        return GotEvent(
            url=d["url"], tags=d["tags"], e_type=d["type"], original_event=js,
        )


class GotRedditEvent(GotEvent):
    def __init__(
        self,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None,
        ups: Optional[int] = None,
        downs: Optional[int] = None,
        source: Optional[str] = None,
        subreddit_name_prefixed: Optional[str] = None,
        title: Optional[str] = None,
        over_18: Optional[bool] = None,
        author: Optional[str] = None,
        is_original_content: Optional[bool] = None,
        shortlink: Optional[str] = None,
        ts: Optional[float] = None,
        type: Optional[str] = None,
        original_event: Optional[str] = None,
    ) -> None:
        super().__init__(tags, url, type, original_event)
        self.ups: Optional[int] = ups
        self.downs: Optional[int] = downs
        self.source: Optional[str] = source
        self.subreddit_name_prefixed: Optional[str] = subreddit_name_prefixed
        self.title: Optional[str] = title
        self.author: Optional[str] = author
        self.shortlink: Optional[str] = shortlink
        self.over_18: Optional[bool] = over_18
        self.is_original_content: Optional[bool] = is_original_content
        self.ts: Optional[float] = ts
        self.original_event: str = original_event

    @property
    def description(self) -> str:
        striped_title = self.title.strip()
        real_title = striped_title[:-1] if striped_title[-1] == "." else striped_title
        return f"""[{self.subreddit_name_prefixed}]({self.shortlink}) ({self.ups})

*{real_title}.* 
— _{self.author}_

{'🔞' if self.over_18 else ''}
"""

    @staticmethod
    def from_dict(d: Dict) -> "GotRedditEvent":
        js = json.dumps(d, separators=(",", ":"))
        d["original_event"] = js
        return GotRedditEvent(**d)


def get_event_from_dict(d: Dict) -> GotEvent:
    if d["type"] == "Got_Reddit_Submission":
        return GotRedditEvent.from_dict(d)
    else:
        return GotEvent.from_dict(d)


def get_event_from_string(s: str) -> GotEvent:
    d = json.loads(s)
    return get_event_from_dict(d)


@dataclass
class TgApprovedEvent:
    tags: Optional[List[str]]
    original_event: str
    up: int
    down: int
    type: str = "Approved_Tg_Submission"

    def as_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), separators=(",", ":"))

    @staticmethod
    def from_vote(v: Vote, tags: List[str]) -> "TgApprovedEvent":
        return TgApprovedEvent(
            tags=tags, up=v.up, down=v.down, original_event=v.base_event
        )
