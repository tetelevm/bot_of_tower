import asyncio
from functools import wraps, partial
from typing import Coroutine, Callable

from telegram import Update, Message, Bot
from telegram.constants import ParseMode
from telegram.ext.filters import MessageFilter, ChatType, COMMAND
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
)

from messages import *
from config import Args, Params
from observer import Observer
from periodic import everyday_cron, add_action, is_same_day_today, is_next_day_today


UNTRACEABLE_CHATS = (Args.NULL_CHAT, )


class NotTrackFilter(MessageFilter):
    """
    A filter that ignores messages that come in the standard untraceable
    chats.
    """

    def filter(self, message: Message) -> bool:
        return message.chat.id not in UNTRACEABLE_CHATS


class CommandWithName(MessageFilter):
    def filter(self, message: Message) -> bool:
        command = message.text.splitlines()[0].split(" ")[0]
        return command.endswith(Args.BOT_USERNAME)


NOTRACK_FILTER = NotTrackFilter()
COMMAND_WITH_NAME = CommandWithName()


def private_checker(func: Callable):
    """
    Decorator, which allows the execution of the function only in private
    messages. Otherwise, the stub "refer to private messages" will be
    returned.
    """

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        if ChatType.PRIVATE.filter(update.message):
            return await func(update, context)
        return await update.effective_chat.send_message(MSG_only_for_private)

    return wrapped


def group_checker(func: Callable):
    """
    A decorator that allows the execution of the function only in groups.
    Otherwise, a "this works only in groups" stub will be returned.
    """

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        if ChatType.GROUPS.filter(update.message):
            return await func(update, context)
        return await update.effective_chat.send_message(MSG_only_for_groups)

    return wrapped


def wednesday_checker(func: Callable):
    """
    Decorator, which allows the execution of the function only on
    Wednesdays. Otherwise, the "this only works on Wednesdays" stub will
    return.
    It is directly related to the `WEDNESDAY_MODE` parameter (if it is
    inactive, the decorator is just ignored).
    """

    if not Params.ONEDAY_MODE:
        return func

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        # `observer.is_enable == True` only on Wednesdays
        if not observer.is_enable:
            return await update.effective_chat.send_message(MSG_not_wednesday)
        return await func(update, context)

    return wrapped


def ignore_checker(func: Callable):
    """
    Decorator, which ignores all messages in chats with the observer
    disabled.
    """

    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        if not observer.is_looked(update.effective_chat.id):
            return

        if observer.get(update.effective_chat.id).is_disable:
            return

        return await func(update, context)

    return wrapped


# === handlers =========================================================


@private_checker
async def start(update: Update, context: CallbackContext):
    """
    Standard welcome for the bot.
    """
    await update.effective_chat.send_message(
        MSG_start,
        parse_mode=ParseMode.HTML,
    )


@private_checker
async def help(update: Update, context: CallbackContext):
    """
    Standard help for the bot.
    """
    await update.effective_chat.send_message(
        MSG_help,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@group_checker
@wednesday_checker
async def enable(update: Update, context: CallbackContext):
    """
    Activates the bot in the groups where it was called.
    If the bot has already been turned off today, it cannot be turned on
    again.
    """

    chat_id = update.effective_chat.id
    if observer.is_looked(chat_id):
        msg = (
            MSG_enable_but_disable
            if observer.get(chat_id).is_disable else
            MSG_enable_already
        )
        return await update.effective_chat.send_message(msg)

    observer.add(chat_id)
    await update.effective_chat.send_message(MSG_enable)


@group_checker
@wednesday_checker
async def disable(update: Update, context: CallbackContext):
    """
    Turns off the bot in the selected groups.
    You can not turn it back on the same day!
    """

    chat_id = update.effective_chat.id
    if not observer.is_looked(chat_id):
        return await update.effective_chat.send_message(MSG_disable_not_enable)

    if observer.get(chat_id).is_disable:
        return await update.effective_chat.send_message(MSG_disable_already)

    observer.get(chat_id).update(is_disable=True)
    await update.effective_chat.send_message(MSG_disable)


async def dont_understand(update: Update, context: CallbackContext):
    """
    Stub to all messages.
    """
    await update.effective_chat.send_message(MSG_dont_understand)


@ignore_checker
async def standard_message(update: Update, context: CallbackContext):
    """
    Executes all tower observation logic.
    The handler is used only for groups that have tower observation
    enabled.

    The algorithm is as follows:
    - the message is checked if it is another letter or not
    - the tower has fallen, it is notified
    - otherwise the letter is added to the tower
    - if the tower is assembled, it is notified
    - if it is time to automatically crash the tower, then it crashes the tower
    """

    tower = observer.get(update.effective_chat.id)

    # check for a letter
    # code will be returned if the trigger is not the expected letter
    code = (await tower.check_correct(update))
    if code is not None:
        # if the trigger is not important or there are no letters anyway,
        # there is no reason to do anything
        is_scip_update = (code == "ignore") or (not tower.letters)
        if is_scip_update:
            return

        # if the tower is small or the message needs to be ignored,
        # there is no need to notify the fall
        is_show_msg = (not is_scip_update) and (len(tower.letters) < Params.MINIMAL_CHECK_LEN)

        # nullify the tower and notifying of this
        tower.update(letters=[])
        if is_show_msg:
            incorrect_codes = {
                "fall": MSG_fall,
                "fall_edited": MSG_fall_edited,
                "fall_repetition": MSG_fall_repetition,
                "fall_deleted": MSG_fall_deleted,
            }
            return await update.effective_chat.send_message(incorrect_codes[code])

    # add a letter to the tower
    letter = (
        update.message.text,
        update.message.from_user.id,
        update.message.id,
    )
    tower.add_letter(letter)

    # if the tower is built, then it's a win
    if tower.is_completed:
        tower.update(letters=[], is_built=True)
        return await update.effective_chat.send_message(
            MSG_tower_success,
            parse_mode="html"
        )

    # if the tower needs to be crashed, then crash it
    if tower.is_need_to_crash:
        msg = MSG_crashes[tower.crash_type]
        tower.update(letters=[], crash_times=tower.crash_times+1)
        return await update.effective_chat.send_message(msg)


# === cron =============================================================


async def only_wednesday_work_switch():
    """
    Turns the bot on if it's Wednesday and off if it's Thursday.
    """

    if is_same_day_today():
        observer.is_enable = True
    elif is_next_day_today():
        observer.is_enable = False


end_day_message = (
    MSG_wednesday_end
    if Params.ONEDAY_MODE else
    MSG_day_end
)


async def send_end_day_message():
    """
    Notifies all chats that the day is over and clears all towers
    information.
    """

    if not observer.is_enable:
        # if the bot is disabled, nothing needs to do
        return

    send_msg_coros = [
        bot.send_message(chat_id, end_day_message)
        for chat_id in observer.all_chats
    ]
    await asyncio.gather(*send_msg_coros)
    observer.delete_all()


# === bot run ==========================================================


def create_app(token: str):
    """
    Bot initialization and start function.

    Adds the next commands:
    - /start - just a standard hello, available only in private messages
    - /help - help message, available only in private messages
    - /enable@name_bot - starts tower observation, works only in groups
    - /please_disable@name_bot - stops the observation, works only in groups

    Also adds two handlers, one for private messages and one for groups.
    The private message handler just returns an "I don't understand" stub.
    The handler in groups controls the process of building the towers.
    """

    app = Application.builder().token(token).build()

    command_filter = COMMAND & (
        (NOTRACK_FILTER & ChatType.GROUPS & COMMAND_WITH_NAME)  # only with bot_name in groups
        | ChatType.PRIVATE
    )
    command_handler = partial(CommandHandler, filters=command_filter, block=False)
    message_handler = partial(MessageHandler, block=False)

    app.add_handler(command_handler("start", start))
    app.add_handler(command_handler("help", help))
    app.add_handler(command_handler("enable", enable))
    app.add_handler(command_handler("please_disable", disable))

    app.add_handler(message_handler(ChatType.PRIVATE, dont_understand))
    app.add_handler(message_handler(NOTRACK_FILTER & ChatType.GROUPS, standard_message))

    return app


async def run_app(token: str):
    """
    Coroutine, which starts the program and keeps it running.
    """

    app = create_app(token)
    global bot
    bot = app.bot

    updates = [
        Update.MESSAGE,
        Update.EDITED_MESSAGE,
        Update.POLL,
        Update.POLL_ANSWER,
        Update.CHAT_MEMBER,
        Update.CHAT_JOIN_REQUEST,
    ]
    await app.initialize()
    await app.updater.start_polling(allowed_updates=updates)
    await app.start()
    print("Bot is running!")


async def pulling(*coros: Coroutine):
    """
    Just a small extra function that run all the necessary coroutines of
    the bot and does not let the program stop.
    """

    await asyncio.gather(*coros)
    while True:
        await asyncio.sleep(1)


# ===


bot: Bot
observer = Observer()

run_coro = run_app(Args.TOKEN)
add_action(send_end_day_message)
if Params.ONEDAY_MODE:
    add_action(only_wednesday_work_switch)
cron_coro = everyday_cron()

asyncio.run(pulling(run_coro, cron_coro))
