from __future__ import annotations

import asyncio
from typing import Dict, List, Tuple, Optional, Final
from dataclasses import dataclass, field

from telegram import Update, Chat
from telegram.ext.filters import Text
from telegram.error import BadRequest

from libmc import Client as McClient

from config import Args, Params, Checks
from periodic import is_wednesday_today, is_tuesday_today


__all__ = [
    "ChatObserver",
    "Observer",
]

# letter, id_author, id_message
LETTER_MSG_TYPE = Tuple[str, int, int]
TOWER_TYPE = List[LETTER_MSG_TYPE]
TOWER_ON_MC_TYPE = Tuple[TOWER_TYPE, int, bool, bool]
get_null_tower_data = lambda: [[], 0, False, False]

IS_LETTER = Text(list(set(Params.TOWER)))
TOWER_LENGTH = len(Params.TOWER)

TOWER_META_KEY: Final[str] = "all_towers_chat_ids"


@dataclass
class ChatObserver:
    """
    A class that stores information about the tower in the current chat.

    The necessary attributes - letters, user ids and message ids from
    the current tower.
    Also need some flags to control building and crashes: is it
    necessary to observe this chat, is the tower built today and how
    many times the bot crashed it.
    """

    _mutable_fields = ["letters", "crash_times", "is_built", "is_disable"]

    mc_client: McClient
    chat_id: int
    letters: TOWER_TYPE = field(default_factory=list)
    crash_times: int = 0
    is_built: bool = False
    is_disable: bool = False

    @classmethod
    def from_mc(cls, mc_client: McClient, chat_id: int) -> ChatObserver:
        """
        Loads data from MC by chat_id and creates an observer object.
        """

        data: TOWER_ON_MC_TYPE = mc_client.get(str(chat_id)) or get_null_tower_data()
        new_chat_observer = cls(
            mc_client=mc_client,
            chat_id=chat_id,
            letters=data[0],
            crash_times=data[1],
            is_built=data[2],
            is_disable=data[3],
        )
        return new_chat_observer

    def to_mc(self):
        """
        Overwrites its data in the MC.
        """

        data = (
            self.letters,
            self.crash_times,
            self.is_built,
            self.is_disable,
        )
        self.mc_client.set(str(self.chat_id), data)

    @property
    def length(self) -> int:
        """
        Returns the number of already built letters.
        """
        return len(self.letters)

    @property
    def chars(self) -> List[str]:
        """
        A list of letters that are already built.
        """
        return list(letter[0] for letter in self.letters)

    @property
    def user_ids(self) -> List[int]:
        """
        A list of user id's that have participated in the current tower.
        """
        return list(letter[1] for letter in self.letters)

    @property
    def message_ids(self) -> List[int]:
        """
        A list of the id messages that build up the tower.
        """
        return list(letter[2] for letter in self.letters)

    def __str__(self):
        return "".join(self.chars)

    @property
    def is_completed(self) -> bool:
        """
        Checks if the tower is built or not.
        """
        return str(self) == Params.TOWER

    @property
    def _expected_letter(self) -> str:
        """
        The letter that should be next in the tower.
        If the tower is built, it will raise an error.
        """
        return Params.TOWER[self.length]

    @property
    def crash_type(self) -> int:
        """
        Chooses how and when the bot should crash the tower.
        The first breaks are unique, the last one is looped.
        """
        return min(self.crash_times, len(Params.CRASH_LENS)-1)

    @property
    def is_need_to_crash(self) -> bool:
        """
        Checks if the bot should now crash the tower or not.
        The condition is that the tower was already built today, and
        the current tower is long enough for the crash to disappoint
        the builders.
        """
        return (
            self.is_built
            and self.length == Params.CRASH_LENS[self.crash_type]
        )

    def update(
            self,
            letters: TOWER_TYPE = None,
            crash_times: int = None,
            is_built: bool = None,
            is_disable: bool = None,
    ):
        """
        Updates chat information and stores it.
        """

        fields = [letters, crash_times, is_built, is_disable]
        for (name, value) in zip(self._mutable_fields, fields):
            if value is not None:
                setattr(self, name, value)
        self.to_mc()

    def delete(self):
        """
        Deletes all data about this chat from memory.
        """
        self.mc_client.delete(str(self.chat_id))

    def add_letter(self, letter: LETTER_MSG_TYPE):
        """
        Adds the next letter to the tower.
        """
        self.update(letters=self.letters + [letter])

    def _is_no_repetition(self, user_id) -> bool:
        """
        Checks if there is already a letter from that participant.
        """
        return user_id in self.user_ids

    async def _is_no_deleted(self, chat: Chat) -> bool:
        """
        Checks if there are deleted messages in the tower.
        """

        coros = [
            chat.forward_to(Args.NULL_CHAT, message_id)
            for message_id in self.message_ids
        ]
        try:
            await asyncio.gather(*coros)
            return True
        except BadRequest:
            return False

    async def check_correct(self, update: Update) -> Optional[str]:
        """
        Checks the event to see if it breaks the tower.
        If the tower is broken, the reason code is returned, if not,
        nothing is returned.
        If "ignore" is returned, then the message should be ignored.

        Checks (order is important):
        - the event does not change a letter in the tower
        - the event is the expected letter
        - the letter is not from an already participating user
        - no one has deleted a letter (checked only at the end of tower)
        """

        message = update.message
        if update.edited_message is not None:
            # some message has been edited
            if Checks.CHANGING and update.edited_message.id in self.message_ids:
                # if the message is from the tower, the tower has fallen
                return "fall_edited"
            else:
                # if not, we just ignore the event
                return "ignore"

        if not (IS_LETTER.filter(message) and message.text == self._expected_letter):
            # if message is not an expected letter, the tower is fallen
            return "fall"

        if Checks.UNIQUENESS and not self._is_no_repetition(message.from_user.id):
            # if the user has already participated, he cannot do it a second time
            return "fall_repetition"

        # since it is too high cost, we check only at the very end of building
        if Checks.DELETING and self.length == (TOWER_LENGTH - 1):
            if not (await self._is_no_deleted(message.chat)):
                # if any message from the tower has been deleted, the tower has fallen
                return "fall_deleted"


class Observer:
    """
    A class that groups observers from all chats.
    The is_enable parameter indicates whether observers are working now
    or not (needed for WEDNESDAY_MODE).
    """

    is_enable: bool
    infos: Dict[int, ChatObserver]
    mc_client: McClient

    def __init__(self):
        # self.is_enable = not Params.WEDNESDAY_MODE or is_tuesday_today()
        self.is_enable = not Params.WEDNESDAY_MODE or is_wednesday_today()
        self.mc_client = McClient([Args.MEMCACHED_HOST], prefix="tower_")
        self._init_infos()

    def _init_infos(self):
        """
        Loads from MC the data of all chats that are already building a
        towers.
        """

        self.infos = dict()
        all_chats = self.mc_client.get(TOWER_META_KEY)
        if all_chats is None:
            all_chats = []
            self.mc_client.set(TOWER_META_KEY, [])

        for chat_id in all_chats:
            self.infos[chat_id] = ChatObserver.from_mc(self.mc_client, chat_id)

    @property
    def all_chats(self) -> List[int]:
        """
        Returns a list with the ids of all chats that have observers.
        """
        return list(self.infos.keys())

    def is_looked(self, chat_id: int) -> bool:
        """
        Checks if there is an observer for this chat.
        """
        return chat_id in self.infos

    def get(self, chat_id: int) -> ChatObserver:
        """
        Returns the observer for this chat.
        """
        return self.infos[chat_id]

    def add(self, chat_id: int):
        """
        Creates a new observer for the given chat.
        """

        self.infos[chat_id] = ChatObserver(mc_client=self.mc_client, chat_id=chat_id)
        self.mc_client.set(TOWER_META_KEY, list(self.infos.keys()))

    def delete_all(self):
        """
        Deletes all observers.
        """

        for chat in self.infos.values():
            chat.delete()
        self.infos = dict()
        self.mc_client.set(TOWER_META_KEY, [])
