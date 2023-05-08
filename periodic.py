import asyncio
import datetime as dt
import time
from typing import Callable, Coroutine, List

from config import Params


__all__ = [
    "is_same_day_today",
    "is_next_day_today",

    "add_action",
    "wait_for_next_day",
    "everyday_cron",
]


SECOND_IN_DAYS = 24 * 60 * 60
ACTION_TYPE = Callable[[], Coroutine]

actions: List[ACTION_TYPE] = []


def is_same_day_today() -> bool:
    """
    Returns whether the bot should work today (in UTC) or not.
    """

    if not Params.ONEDAY_MODE:
        # it should always work if it is not a one-day mode
        return True

    utc_now = dt.datetime.utcnow()
    return dt.date.isoweekday(utc_now) == Params.DAY_NUMBER


def is_next_day_today() -> bool:
    """
    Returns whether the bot should shut down today(in UTC) or not.
    """

    if not Params.ONEDAY_MODE:
        # it should not shut down without a one-day mode
        return False

    utc_now = dt.datetime.utcnow()
    next_day_number = Params.DAY_NUMBER % 7 + 1
    return dt.date.isoweekday(utc_now) == next_day_number


def add_action(action: ACTION_TYPE):
    """
    Appends the action to the list of others actions.
    Actions are executed every day at midnight.
    The action must be an asynchronous function, the actions are
    executed one after the other.
    """
    actions.append(action)


async def wait_for_next_day():
    """
    Calculates how much time is left until midnight and waits for that
    time.
    """

    now = dt.datetime.utcnow()
    midnight = now.replace(hour=0, minute=0, second=1)
    seconds_from_midnight = (now - midnight).seconds
    await asyncio.sleep(SECOND_IN_DAYS - seconds_from_midnight)


async def wait_minute():
    # testing function
    await asyncio.sleep(60 - (time.time() % 60))


async def everyday_cron():
    """
    Every day at midnight executes the set actions.
    This is designed to avoid using the system cron and adding
    unnecessary dependencies.
    """

    while True:
        await wait_for_next_day()
        for action in actions:
            await action()
