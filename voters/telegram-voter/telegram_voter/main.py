import asyncio
import json
from datetime import datetime
from typing import Optional, Dict

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from telegram_voter.events import get_event_from_dict, get_event_from_string
from telegram_voter.redis_utils import (
    connect_to_redis,
    subscribe_to_grabber_events,
    push_gr_event,
    pop_gr_event,
)
from telegram_voter.utils import get_configuration, get_current_utc_timestamp

config = get_configuration()

bot = Bot(token=config.telegram_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hi!\nI'm VoterBot!")


async def poll_for_memes():
    while True:
        scheduled_timestamp: float = get_current_utc_timestamp() + config.vote_interval
        event_str = pop_gr_event()
        try:
            if event_str:
                event = get_event_from_string(event_str)
                await bot.send_photo(
                    config.target_group,
                    event.url,
                    caption=event.description,
                    parse_mode="Markdown",
                )
        except:
            pass

        current_timestamp = get_current_utc_timestamp()
        if current_timestamp < scheduled_timestamp:
            await asyncio.sleep(scheduled_timestamp - current_timestamp)


def grabber_handler(event: Dict) -> None:
    push_gr_event(event["data"])


if __name__ == "__main__":
    connect_to_redis(config)
    gr_event_thread = subscribe_to_grabber_events(grabber_handler)

    dp.loop.create_task(poll_for_memes())
    executor.start_polling(dp, skip_updates=True)
