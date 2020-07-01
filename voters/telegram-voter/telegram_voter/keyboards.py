from typing import Optional, Callable, Dict

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from telegram_voter.votes import Vote

up_code = "tv_upvote"
down_code = "tv_downvote"
accepted_code = "tv_accepted"
declined_code = "tv_declined"


def get_two_button_markup(vote: Optional[Vote] = None) -> InlineKeyboardMarkup:
    upvotes = vote.up if vote else 0
    downvotes = vote.down if vote else 0

    upvote_btn = InlineKeyboardButton(f"🔥 {upvotes}", callback_data=up_code)
    downvote_btn = InlineKeyboardButton(f"🗑 {downvotes}", callback_data=down_code)
    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.row(upvote_btn, downvote_btn)
    return inline_kb


def get_default_keyboard(vote: Optional[Vote]) -> InlineKeyboardMarkup:
    if not vote:
        return get_two_button_markup()
    else:
        if vote.finished:
            if vote.accepted:
                finished_btn = InlineKeyboardButton(
                    "Submission was accepted 🚀", callback_data=accepted_code
                )
            else:
                finished_btn = InlineKeyboardButton(
                    "Submission was declined 👾", callback_data=declined_code
                )
            inline_kb = InlineKeyboardMarkup(row_width=1)
            inline_kb.row(finished_btn)
            return inline_kb
        else:
            return get_two_button_markup(vote)


keyboard_mapping: Dict[str, Callable] = {"default": get_default_keyboard}


def get_keyboard(
    style: Optional[str] = None, vote: Optional[Vote] = None
) -> InlineKeyboardMarkup:
    if style and style in keyboard_mapping.keys():
        return keyboard_mapping[style](vote)
    else:
        return get_default_keyboard(vote)
