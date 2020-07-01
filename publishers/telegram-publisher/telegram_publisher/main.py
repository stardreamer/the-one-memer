import asyncio
from typing import Dict

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.utils import executor

from telegram_publisher.events import get_event_from_string
from telegram_publisher.redis_utils import (
    connect_to_redis,
    subscribe_to_voter_events,
    push_vt_event,
    pop_vt_event,
    trim_queue,
    cache_url,
    url_was_already_processed,
)
from telegram_publisher.utils import get_configuration, get_current_utc_timestamp

config = get_configuration()

bot = Bot(token=config.telegram_token)
dp = Dispatcher(bot)


def voter_handler(event: Dict) -> None:
    push_vt_event(event["data"], config.tags)


async def publish_memes():
    while True:
        publish_interval = (
            10 if config.publishing_interval < 10 else config.publishing_interval
        )
        scheduled_timestamp: float = get_current_utc_timestamp() + publish_interval
        event_str = pop_vt_event()
        if event_str:
            try:
                event = get_event_from_string(event_str)
                if url_was_already_processed(event.url):
                    continue
                await bot.send_photo(
                    config.target_channel,
                    event.url,
                    caption=event.description if config.with_description else None,
                    parse_mode="Markdown",
                )

                trim_queue(config.max_queue_len)
                cache_url(event.url, config.redis_internal_ttl)
            except Exception:
                pass

        current_timestamp = get_current_utc_timestamp()
        if current_timestamp < scheduled_timestamp:
            await asyncio.sleep(scheduled_timestamp - current_timestamp)


if __name__ == "__main__":
    connect_to_redis(config)
    vote_event_thread = subscribe_to_voter_events(voter_handler)

    dp.loop.create_task(publish_memes())

    executor.start_polling(dp, skip_updates=True)
