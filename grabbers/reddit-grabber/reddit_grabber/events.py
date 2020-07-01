import json
from typing import List, Optional, Dict

from praw.reddit import Submission

from reddit_grabber.utils import get_current_utc_timestamp, GrabberConfiguration


class GotRedditEvent:
    def __init__(
        self,
        tags: List[str],
        url: str,
        ups: Optional[int],
        downs: Optional[int],
        source: str,
        subreddit_name_prefixed: str,
        title: str,
        over_18: bool,
        author: str,
        is_original_content: bool,
        shortlink: str,
    ) -> None:
        self.tags: List[str] = tags
        self.url: str = url
        self.e_type: Optional[str] = "Got_Reddit_Submission"
        self.ups: Optional[int] = ups
        self.downs: Optional[int] = downs
        self.source: str = source
        self.subreddit_name_prefixed: str = subreddit_name_prefixed
        self.title: str = title
        self.author: str = author
        self.shortlink: str = shortlink
        self.over_18: bool = over_18
        self.is_original_content: bool = is_original_content
        self.version = "1.1"

    def as_dict(self) -> Dict:
        base_dict = {
            "version": self.version,
            "tags": self.tags,
            "url": self.url,
            "type": self.e_type,
            "ts": get_current_utc_timestamp(),
            "source": self.source,
            "ups": self.ups,
            "downs": self.downs,
            "subreddit_name_prefixed": self.subreddit_name_prefixed,
            "title": self.title,
            "author": self.author,
            "shortlink": self.shortlink,
            "over_18": self.over_18,
            "is_original_content": self.is_original_content,
        }

        return base_dict

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), separators=(",", ":"))

    @staticmethod
    def from_submission(
        sub: Submission, conf: GrabberConfiguration
    ) -> "GotRedditEvent":
        tags: List[str] = conf.tags
        url: str = sub.url if hasattr(sub, "url") else None
        ups: Optional[int] = sub.ups if hasattr(sub, "ups") else None
        downs: Optional[int] = sub.downs if hasattr(sub, "downs") else None
        source: str = conf.service_id
        subreddit_name_prefixed: str = sub.subreddit_name_prefixed if hasattr(
            sub, "subreddit_name_prefixed"
        ) else None
        title: str = sub.title if hasattr(sub, "title") else None
        author: str = str(sub.author) if hasattr(sub, "author") else None
        shortlink: str = sub.shortlink if hasattr(sub, "shortlink") else None
        over_18: bool = sub.over_18 if hasattr(sub, "over_18") else False
        is_original_content: bool = sub.is_original_content if hasattr(
            sub, "is_original_content"
        ) else False

        return GotRedditEvent(
            tags=tags,
            url=url,
            ups=ups,
            downs=downs,
            source=source,
            subreddit_name_prefixed=subreddit_name_prefixed,
            title=title,
            over_18=over_18,
            author=author,
            is_original_content=is_original_content,
            shortlink=shortlink,
        )
