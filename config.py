"""
File with the all project configuration (observation parameters and telegram bot
parameters).
"""

from typing import Final, Tuple

from funcs import ReadonlyEnum, get_args


__all__ = [
    "VERSION",
    "Args",
    "Params",
    "Checks",
]

_args = get_args()


VERSION: Final[str] = "1.0"


class Args(metaclass=ReadonlyEnum):
    TOKEN = _args["TOKEN"]
    BOT_USERNAME = _args["BOT_USERNAME"]
    NULL_CHAT = _args["NULL_CHAT"]

    MEMCACHED_HOST: Final[str] = "localhost:11211"


class Params(metaclass=ReadonlyEnum):
    TOWER: Final[str] = "ITSWEDNESDAYMYDUDES!"
    CRASH_LENS: Tuple[int, ...] = (3, 14, 12, 7, 3)
    MINIMAL_CHECK_LEN: Final[int] = 3

    ONEDAY_MODE: Final[bool] = True
    DAY_NUMBER: Final[int] = 3


# types of checks
class Checks(metaclass=ReadonlyEnum):
    UNIQUENESS = True
    DELETING = True
    CHANGING = True
    SPECIAL_MODE = True
