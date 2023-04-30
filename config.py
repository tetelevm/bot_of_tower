"""
File with the all project configuration (observation parameters and telegram bot
parameters).
"""

import json
from pathlib import Path

from typing import Final, Tuple


VERSION: Final[str] = "1.0"


__args__ = [
    "Args",
    "Params",
    "Checks",
]


def _get_args() -> dict:
    """
    Reads envs from the file in the root of the project.
    """

    envs_file = Path().absolute() / ".envs"
    try:
        with open(envs_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError("Requires the settings file `.envs` in the root of the project")


_args = _get_args()


class _CustomEnum(type):
    def __setattr__(self, key, value):
        pass


class Args(metaclass=_CustomEnum):
    TOKEN = _args["TOKEN"]
    BOT_USERNAME = _args["BOT_USERNAME"]
    NULL_CHAT = _args["NULL_CHAT"]

    MEMCACHED_HOST: Final[str] = "localhost:11211"


class Params(metaclass=_CustomEnum):
    TOWER: Final[str] = "ITSWEDNESDAYMYDUDES!"
    CRASH_LENS: Tuple[int, ...] = (3, 14, 12, 7, 3)
    MINIMAL_CHECK_LEN: Final[int] = 3
    WEDNESDAY_MODE: Final[bool] = True


# types of checks
class Checks(metaclass=_CustomEnum):
    UNIQUENESS = False
    DELETING = True
    CHANGING = True
