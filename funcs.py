"""
Things that are necessary but get in the way of reading business logic.
"""

import json
from pathlib import Path
from typing import List


__all__ = [
    "get_args",
    "ReadonlyEnum",
    "SIMILAR_CHARS",
    "get_all_possible_chars",
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


SIMILAR_CHARS = {
    "a": ["а"],
    "b": ["Ь"],
    "c": ["с"],
    "e": ["е"],
    "k": ["к"],
    "l": ["|", "I"],
    "n": ["п"],
    "o": ["о"],
    "p": ["р"],
    "r": ["г"],
    "x": ["х"],
    "y": ["у"],
    "A": ["А"],
    "B": ["В"],
    "C": ["С"],
    "E": ["Е"],
    "H": ["Н"],
    "I": ["|", "l"],
    "K": ["К"],
    "M": ["М"],
    "O": ["О"],
    "P": ["Р"],
    "T": ["Т"],
    "X": ["Х"],
    "Y": ["У"],
}


def get_all_possible_chars(tower: str, *, similar_emabled: bool = True) -> List[str]:
    """
    Returns a character set of tower chars and similar chars (if any).
    """

    tower_chars = list(set(tower))
    similar_chars = []

    if similar_emabled:
        for char in tower_chars:
            similar_chars.extend(SIMILAR_CHARS.get(char, []))

    return list(set(tower_chars + similar_chars))
