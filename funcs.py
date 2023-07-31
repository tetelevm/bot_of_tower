"""
Things that are necessary but get in the way of reading business logic.
"""

import json
from pathlib import Path


__all__ = [
    "get_args",
    "ReadonlyEnum",
]


def get_args() -> dict:
    """
    Reads envs from the file in the root of the project.
    """

    envs_file = Path().absolute() / ".envs"
    try:
        with open(envs_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError("Requires the settings file `.envs` in the root of the project")


class ReadonlyEnum(type):
    def __setattr__(self, key, value):
        pass
