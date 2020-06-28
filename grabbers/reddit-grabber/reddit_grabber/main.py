import time
from concurrent.futures.thread import ThreadPoolExecutor

import praw
from praw.reddit import Submission

from reddit_grabber.events import GotRedditEvent
from reddit_grabber.exceptions import RedditGrabberException
from reddit_grabber.redis_utils import (
    register_submission,
    connect_to_redis,
    publish_submission,
    url_was_already_processed,
    phash_was_already_processed,
)
from reddit_grabber.utils import (
    is_image,
    get_hash,
    get_image,
    GrabberConfiguration,
    get_configuration,
    FiniteList,
    get_current_utc_timestamp,
)


def process_submission(submission: Submission, conf: GrabberConfiguration) -> None:
    if not is_image(submission):
        return

    if hasattr(submission, "over_18"):
        if submission.over_18 and (not conf.mature_content_allowed):
            return

    url = submission.url if hasattr(submission, "url") else None

    if url_was_already_processed(url):
        return

    phash = str(get_hash(get_image(submission)))

    if phash_was_already_processed(phash):
        register_submission(url=url, phash=None, ttl=conf.redis_internal_ttl)
        return

    register_submission(url=url, phash=phash, ttl=conf.redis_internal_ttl)
    publish_submission(GotRedditEvent.from_submission(submission, conf))


def stream_loop(conf: GrabberConfiguration) -> None:
    reddit = praw.Reddit(
        client_id=conf.client_id,
        client_secret=conf.client_secret,
        user_agent=conf.user_agent,
    )

    with ThreadPoolExecutor(max_workers=conf.thread_count) as executor:
        for sub in reddit.subreddit(conf.subreddit_name).stream.submissions():
            sub: Submission = sub
            executor.submit(process_submission(sub, conf))


def post_loop(conf: GrabberConfiguration) -> None:

    reddit = praw.Reddit(
        client_id=conf.client_id,
        client_secret=conf.client_secret,
        user_agent=conf.user_agent,
    )

    if conf.mode == "hot":
        source = reddit.subreddit(conf.subreddit_name).hot(limit=config.post_window)
    elif conf.mode == "rising":
        source = reddit.subreddit(conf.subreddit_name).rising(limit=config.post_window)
    else:
        raise RedditGrabberException(
            f"Critical error. Mode {conf.mode} can't be used for post_loop"
        )

    seen_posts: FiniteList = FiniteList(conf.post_history_cache_len)

    with ThreadPoolExecutor(max_workers=conf.thread_count) as executor:
        while True:
            scheduled_timestamp: float = get_current_utc_timestamp() + conf.sleep_time

            for sub in source:
                sub: Submission = sub
                if hasattr(sub, "url"):
                    if sub.url in seen_posts:
                        continue
                    seen_posts.append(sub.url)
                executor.submit(process_submission(sub, conf))

            current_timestamp = get_current_utc_timestamp()

            if current_timestamp < scheduled_timestamp:
                time.sleep(scheduled_timestamp - current_timestamp)


if __name__ == "__main__":

    config = get_configuration()
    connect_to_redis(config)

    if config.stream_mode():
        stream_loop(config)
    else:
        post_loop(config)
