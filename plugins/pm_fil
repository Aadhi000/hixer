import asyncio
import logging
import re
import ast
import math
import random
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid, ChatWriteForbidden, MessageIdInvalid
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, make_inactive
from utils import get_size, is_subscribed, get_settings, save_group_settings, send_all
from database.ia_filterdb import get_search_results
from database.filters_mdb import del_all, find_filter
from database.gfilters_mdb import find_gfilter, get_gfilters, del_allg

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

@Client.on_message((filters.group | filters.private) & filters.text & filters.incoming)
async def give_filter(client, message):
    if message.chat.id != SUPPORT_CHAT_ID:
        if not await global_filters(client, message):
            if not await manual_filters(client, message):
                settings = await get_settings(message.chat.id)
                if settings.get("auto_ffilter", False):
                    await auto_filter(client, message)

@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    if message.text.startswith(("/", "#")):
        return

    if message.from_user.id in ADMINS:
        return

    try:
        await message.reply_text("Your message has been sent to moderators.")
        await bot.send_message(LOG_CHANNEL, f"🔔 PM Message

👤 Name: {message.from_user.first_name}
🆔 ID: {message.from_user.id}
💬 Message: {message.text}")
    except ChatWriteForbidden:
        logger.error("Bot does not have permission to send messages in the chat.")

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        ident, req, key, offset = query.data.split("_")
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer("This is not your request.", show_alert=True)

        offset = int(offset) if offset.isdigit() else 0
        search = BUTTONS.get(key)

        if not search:
            return await query.answer("Search results expired.", show_alert=True)

        files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=offset, filter=True)
        if not files:
            return

        settings = await get_settings(query.message.chat.id)
        temp.SEND_ALL_TEMP[query.from_user.id] = files

        btn = [
            [InlineKeyboardButton(f"{file.file_name}", callback_data=f"files#{file.file_id}")] for file in files
        ]

        btn.append([InlineKeyboardButton("Next ➡", callback_data=f"next_{req}_{key}_{n_offset}")]) if n_offset else None
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))

    except MessageNotModified:
        pass
    except MessageIdInvalid:
        logger.error("Message ID is invalid, possibly deleted.")
    except Exception as e:
        logger.exception(f"Error in next_page: {e}")
