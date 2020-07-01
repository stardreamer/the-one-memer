import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


class ApprovedEvent:
    def __init__(
        self,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None,
        up: Optional[int] = None,
        down: Optional[int] = None,
        type: Optional[str] = None,
        original_event: str = None,
        original_tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        version: Optional[str] = None,
    ) -> None:
        self.tags: Optional[List[str]] = tags
        self.original_tags: Optional[List[str]] = original_tags
        self.url: Optional[str] = url
        self.up: Optional[int] = up
        self.down: Optional[int] = down
        self.type: Optional[str] = type
        self.source: Optional[str] = source
        self.version: Optional[str] = version
        self.original_event: Optional[str] = original_event

    @property
    def description(self) -> str:
        return ""

    @property
    def all_tags(self) -> List[str]:
        t = [] if not self.tags else self.tags
        ot = [] if not self.original_tags else self.original_tags
        ct = t + ot
        return list(set(ct)) if ct else []

    @staticmethod
    def from_dict(d: Dict) -> "ApprovedEvent":
        js = json.dumps(d, separators=(",", ":"))

        or_ev = d["original_event"]

        return ApprovedEvent(
            url=or_ev["url"],
            tags=d["tags"],
            type=d["type"],
            original_event=js,
            up=d["up"],
            down=d["down"],
            source=d["source"],
            original_tags=or_ev["tags"],
            version=d["version"],
        )


@dataclass
class RedditDetails:
    tags: List[str]
    url: str
    source: str
    subreddit_name_prefixed: str
    title: str
    over_18: bool
    author: str
    is_original_content: bool
    shortlink: str
    ups: Optional[int] = None
    downs: Optional[int] = None
    version: Optional[str] = None

    @staticmethod
    def from_str(rs: str) -> "RedditDetails":
        d: Dict[str, Any] = json.loads(rs)

        return RedditDetails(
            tags=d.get("tags") if d.get("tags") else [],
            url=d["url"],
            source=d["source"],
            subreddit_name_prefixed=d["subreddit_name_prefixed"],
            title=d["title"],
            over_18=d["over_18"],
            author=d.get("author") if d.get("author") else "",
            is_original_content=d["is_original_content"],
            shortlink=d.get("shortlink") if d.get("shortlink") else "",
            ups=d.get("ups"),
            downs=d.get("downs"),
            version=d.get("version"),
        )


class ApprovedRedditEvent(ApprovedEvent):
    def __init__(
        self,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None,
        up: Optional[int] = None,
        down: Optional[int] = None,
        type: Optional[str] = None,
        original_event: str = None,
        source: Optional[str] = None,
        reddit_details: Optional[RedditDetails] = None,
        version: Optional[str] = None,
    ) -> None:
        super().__init__(
            tags=tags,
            original_tags=reddit_details.tags,
            original_event=original_event,
            url=url,
            up=up,
            down=down,
            type=type,
            source=source,
            version=version,
        )

        self.reddit_details = reddit_details

    @property
    def description(self) -> str:
        striped_title = self.reddit_details.title.strip()
        real_title = striped_title[:-1] if striped_title[-1] == "." else striped_title
        return f"""[{self.reddit_details.subreddit_name_prefixed}]({self.reddit_details.shortlink}) ({self.reddit_details.ups})

*{real_title}.* 
— _{self.reddit_details.author}_

{'🔞' if self.reddit_details.over_18 else ''}
"""

    @staticmethod
    def from_dict(d: Dict) -> "ApprovedRedditEvent":
        js = json.dumps(d, separators=(",", ":"))

        reddit_details = RedditDetails.from_str(d["original_event"])

        return ApprovedRedditEvent(
            url=reddit_details.url,
            tags=d["tags"],
            type=d["type"],
            original_event=js,
            up=d["up"],
            down=d["down"],
            source=d["source"],
            reddit_details=reddit_details,
            version=d["version"],
        )


def get_event_from_dict(d: Dict) -> ApprovedEvent:
    or_d = json.loads(d["original_event"])
    if or_d["type"] == "Got_Reddit_Submission":
        return ApprovedRedditEvent.from_dict(d)
    else:
        return ApprovedEvent.from_dict(d)


def get_event_from_string(s: str) -> ApprovedEvent:
    d = json.loads(s)
    return get_event_from_dict(d)
