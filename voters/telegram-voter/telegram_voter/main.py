import asyncio
from typing import Dict

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.utils import executor

from telegram_voter.events import get_event_from_string
from telegram_voter.keyboards import (
    get_keyboard,
    up_code,
    down_code,
    accepted_code,
    declined_code,
)
from telegram_voter.redis_utils import (
    connect_to_redis,
    subscribe_to_grabber_events,
    push_gr_event,
    pop_gr_event,
    register_vote,
    upvote,
    downvote,
    publish_approved_submission,
)
from telegram_voter.utils import get_configuration, get_current_utc_timestamp
from telegram_voter.votes import Vote, VoteAttemptResult

config = get_configuration()

bot = Bot(token=config.telegram_token)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hi!\nI'm VoterBot!")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("tv_"))
@dp.throttled(
    None, rate=config.vote_throttle,
)
async def process_callback(callback_query: types.CallbackQuery):
    if callback_query.message.chat.id != config.target_group:
        return

    if callback_query.from_user.is_bot:
        return

    mid = callback_query.message.message_id
    voter = callback_query.from_user.id

    if callback_query.data == up_code:
        v, res = upvote(mid, voter)
        await process_vote(callback_query, mid, res, v)
        if v.accepted:
            publish_approved_submission(v, config.tags, config.service_id)

    elif callback_query.data == down_code:
        v, res = downvote(mid, voter)
        await process_vote(callback_query, mid, res, v)

    elif callback_query.data == accepted_code or callback_query.data == declined_code:
        await bot.answer_callback_query(callback_query.id, text="This vote is finished")
    else:
        await bot.answer_callback_query(callback_query.id)


async def process_vote(callback_query, mid, res, v):
    if res == VoteAttemptResult.VoteWasFinished:
        await bot.answer_callback_query(callback_query.id, text="This vote is over!")
    elif res == VoteAttemptResult.VotedAlready:
        await bot.answer_callback_query(callback_query.id, text="You've voted already!")
    elif res == VoteAttemptResult.Accepted:
        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=mid,
            reply_markup=get_keyboard(vote=v),
        )
        await bot.answer_callback_query(callback_query.id, text="Roger that!")
    else:
        await bot.answer_callback_query(callback_query.id, text="Unknown error")


async def poll_for_memes():
    while True:
        vote_interval = 1 if config.vote_interval < 1 else config.vote_interval
        scheduled_timestamp: float = get_current_utc_timestamp() + vote_interval

        for _ in range(config.vote_batch_size):
            event_str = pop_gr_event()
            if event_str:
                try:
                    event = get_event_from_string(event_str)

                    caption = event.description if config.with_description else None
                    mess: Message = await bot.send_photo(
                        config.target_group,
                        event.url,
                        caption=caption,
                        parse_mode="Markdown",
                        reply_markup=get_keyboard(),
                    )
                    vote = Vote.from_got_event(
                        mess.message_id, config.vote_threshold, event
                    )
                    register_vote(vote)
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

        current_timestamp = get_current_utc_timestamp()
        if current_timestamp < scheduled_timestamp:
            await asyncio.sleep(scheduled_timestamp - current_timestamp)


def grabber_handler(event: Dict) -> None:
    push_gr_event(event["data"], config.tags)


if __name__ == "__main__":
    connect_to_redis(config)
    gr_event_thread = subscribe_to_grabber_events(grabber_handler)

    dp.loop.create_task(poll_for_memes())

    executor.start_polling(dp, skip_updates=True)
