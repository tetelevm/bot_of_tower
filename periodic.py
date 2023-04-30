import asyncio
import datetime as dt
import time
from typing import Callable, Coroutine, List


__all__ = [
    "is_wednesday_today",
    "is_thursday_today",
    "add_action",
    "wait_for_next_day",
    "everyday_cron",
]


SECOND_IN_DAYS = 24 * 60 * 60
ACTION_TYPE = Callable[[], Coroutine]

actions: List[ACTION_TYPE] = []


def is_wednesday_today() -> bool:
    """
    Returns, Wednesday today in UTC or not.
    """

    utc_now = dt.datetime.utcnow()
    return dt.date.isoweekday(utc_now) == 3


def is_thursday_today() -> bool:
    """
    Returns, Thursday today in UTC or not.
    """

    utc_now = dt.datetime.utcnow()
    return dt.date.isoweekday(utc_now) == 4


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

    now = dt.datetime.now()
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
        await wait_minute()
        for action in actions:
            await action()
