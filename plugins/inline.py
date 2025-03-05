import logging
from pyrogram import Client, emoji, filters
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid, MessageNotModified, MessageIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument, InlineQuery
from database.ia_filterdb import get_search_results
from utils import is_subscribed, get_size, temp
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION
from database.connections_mdb import active_connection

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME

async def inline_users(query: InlineQuery):
    if AUTH_USERS and query.from_user and query.from_user.id in AUTH_USERS:
        return True
    if query.from_user and query.from_user.id not in temp.BANNED_USERS:
        return True
    return False

@Client.on_inline_query()
async def answer(bot, query):
    """Show search results for given inline query"""
    chat_id = await active_connection(str(query.from_user.id))

    if not await inline_users(query):
        try:
            await query.answer(results=[], cache_time=0, switch_pm_text="You are not authorized", switch_pm_parameter="unauthorized")
        except QueryIdInvalid:
            pass
        return

    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        try:
            await query.answer(results=[], cache_time=0, switch_pm_text="Subscribe to use the bot", switch_pm_parameter="subscribe")
        except QueryIdInvalid:
            pass
        return

    results = []
    query_text = query.query.strip()
    file_type = None

    if "|" in query_text:
        query_text, file_type = map(str.strip, query_text.split("|", maxsplit=1))
        file_type = file_type.lower()

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=query_text)

    try:
        files, next_offset, total = await get_search_results(chat_id, query_text, file_type=file_type, max_results=10, offset=offset)
    except Exception as e:
        logger.exception(f"Error fetching search results: {e}")
        files, next_offset, total = [], 0, 0

    for file in files:
        title = file.file_name or "Unknown File"
        size = get_size(file.file_size) or "Unknown Size"
        f_caption = file.caption or title

        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(f"Error formatting caption: {e}")

        results.append(
            InlineQueryResultCachedDocument(
                title=title,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f"Size: {size} | Type: {file.file_type}",
                reply_markup=reply_markup
            )
        )

    switch_pm_text = f"{emoji.FILE_FOLDER} Results - {total}" if results else f"{emoji.CROSS_MARK} No results found"

    try:
        await query.answer(results=results, is_personal=True, cache_time=cache_time, switch_pm_text=switch_pm_text, switch_pm_parameter="start", next_offset=str(next_offset))
    except QueryIdInvalid:
        pass
    except Exception as e:
        logger.exception(f"Error answering query: {e}")

def get_reply_markup(query):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔍 Search Again", switch_inline_query_current_chat=query)]])
