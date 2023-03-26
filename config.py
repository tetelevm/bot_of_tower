"""
File with the all project configuration (observation parameters and telegram bot
parameters).
"""

import json
from pathlib import Path

from typing import Final, Tuple


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


VERSION: Final[str] = "0.49"
# VERSION: Final[str] = "0.5"  # create README
# VERSION: Final[str] = "0.7"  # + add a deletion check and testing
# VERSION: Final[str] = "1.0"  # + add tower storing in memcache


TOWER: Final[str] = "ITSWEDNESDAYMYDUDES!"
CRASH_LENS: Tuple[int, ...] = (3, 14, 12, 7, 3)
MINIMAL_CHECK_LEN: Final[int] = 3
WEDNESDAY_MODE: Final[bool] = False

TOKEN = _args["TOKEN"]
BOT_USERNAME = _args["BOT_USERNAME"]
