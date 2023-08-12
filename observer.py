from __future__ import annotations

import asyncio
from typing import Dict, List, Tuple, Optional, Final, Literal
from dataclasses import dataclass, field

from telegram import Update, Chat
from telegram.ext.filters import Text
from telegram.error import BadRequest

from libmc import Client as McClient

from config import Args, Params, Checks
from funcs import SIMILAR_CHARS, get_all_possible_chars
from periodic import is_same_day_today


__all__ = [
    "ChatObserver",
    "Observer",
]


LETTER_TYPE = str
ID_AUTHOR_TYPE = int
ID_MESSAGE_TYPE = int
LETTER_MSG_TYPE = Tuple[LETTER_TYPE, ID_AUTHOR_TYPE, ID_MESSAGE_TYPE]
TOWER_LETTERS_TYPE = List[LETTER_MSG_TYPE]
CRASH_TIMES_TYPE = int
IS_BUILT_TYPE = bool
IS_DISABLE_TYPE = bool
TOWER_ON_MC_TYPE = Tuple[
    TOWER_LETTERS_TYPE,
    CRASH_TIMES_TYPE,
    IS_BUILT_TYPE,
    IS_DISABLE_TYPE,
]

IS_LETTER = Text(get_all_possible_chars(Params.TOWER, similar_emabled=Checks.SIMILAR))
TOWER_LENGTH: Final[int] = len(Params.TOWER)

TOWER_META_KEY: Final[str] = "all_towers_chat_ids"
get_null_tower_data = lambda: [[], 0, False, False]


@dataclass
class Tower:
    """
    A tower class that stores the letters and includes all the methods
    for tower checks.
    """

    letters: TOWER_LETTERS_TYPE = field(default_factory=list)
    CHECKING_CODES = Optional[Literal[
        "ignore",
        "fall",
        "fall_edited",
        "fall_repetition",
    ]]
    CHECKING_COMPLETE_CODES = Optional[Literal[
        "fail_similar",
        "fall_deleted",
    ]]

    def __len__(self):
        """
        Returns the number of already built letters.
        """
        return len(self.letters)

    def __str__(self):
        return "".join(self._chars)

    @property
    def _chars(self) -> List[LETTER_TYPE]:
        """
        A list of letters that are already built.
        """
        return list(letter[0] for letter in self.letters)

    @property
    def _user_ids(self) -> List[ID_AUTHOR_TYPE]:
        """
        A list of user id's that have participated in the current tower.
        """
        return list(letter[1] for letter in self.letters)

    @property
    def _message_ids(self) -> List[ID_MESSAGE_TYPE]:
        """
        A list of the id messages that build up the tower.
        """
        return list(letter[2] for letter in self.letters)

    @property
    def _expected_letters(self) -> List[LETTER_TYPE]:
        """
        A list of letters, one of which may be the next in the tower.
        If the tower is built, it will raise an error.
        """

        expected_char = Params.TOWER[len(self)]
        possible_chars = [expected_char]

        if Checks.SIMILAR:
            possible_chars += SIMILAR_CHARS.get(expected_char, [])

        return possible_chars

    def _is_repeat_participant(self, user_id) -> bool:
        """
        Checks if there is already a letter from that participant.
        """
        return user_id in self._user_ids

    async def _is_no_deleted(self, chat: Chat) -> bool:
        """
        Checks if there are deleted messages in the tower.
        """

        coros = [
            chat.forward_to(Args.NULL_CHAT, message_id)
            for message_id in self._message_ids
        ]
        try:
            await asyncio.gather(*coros)
            return True
        except BadRequest:
            return False

    # =====

    @property
    def is_completed(self) -> bool:
        """
        Checks if the tower is built or not.
        """
        return len(self) == TOWER_LENGTH

    def add_letter(self, letter: LETTER_MSG_TYPE):
        """
        Adds the next letter to the tower.
        """
        self.letters.append(letter)

    async def check_correct(self, update: Update) -> CHECKING_CODES:
        """
        Checks the event to see if it breaks the tower.
        If the tower is broken, the reason code is returned, if not,
        nothing is returned.
        If "ignore" is returned, then the message should be ignored.

        Checks (order is important):
        - the event does not change a letter in the tower
        - the event is the expected letter
        - the letter is not from an already participating user

        Some checks may not be run depending on the settings.
        """

        message = update.message
        if Checks.CHANGING and (update.edited_message is not None):
            # some message has been edited
            if update.edited_message.id in self._message_ids:
                # if the message is from the tower, the tower has fallen
                return "fall_edited"
            else:
                # if not, we just ignore the event
                return "ignore"

        if (not IS_LETTER.filter(message)) or (message.text not in self._expected_letters):
            # if message is not an expected letter, the tower is fallen;
            # remember to check for correctness after building
            return "fall"

        if Checks.UNIQUENESS and self._is_repeat_participant(message.from_user.id):
            # if the user has already participated, he cannot do it a second time
            return "fall_repetition"

    async def check_after_completion(self, update: Update) -> CHECKING_COMPLETE_CODES:
        """
        Checks that are run after the tower is built.
        That is, if the tower was seemingly built, but something went
        wrong, the bot will report it at the end.
        If the tower is broken, the reason code is returned, if not,
        nothing is returned.

         Checks (order is important):
         - in the tower were not the correct symbols, but similar ones
        - no one has deleted a letter (checked only at the end of tower)

        Some checks may not be run depending on the settings.
        """

        if Checks.SIMILAR and (str(self) != Params.TOWER):
            # if the tower is built but does not equal the required tower, then
            # someone tricked it!
            return "fail_similar"

        if Checks.DELETING:
            # since it is too high cost, checking is the most recent
            if not (await self._is_no_deleted(update.effective_chat)):
                # if any message from the tower has been deleted, the tower has fallen
                return "fall_deleted"



@dataclass
class ChatObserver:
    """
    A class that stores information about the tower in the current chat.
    Also stores some flags to control building and crashes: is it
    necessary to observe this chat, is the tower built today and how
    many times the bot crashed it.
    """

    mc_client: McClient
    chat_id: int
    tower: Tower = field(default_factory=Tower)
    crash_times: CRASH_TIMES_TYPE = 0
    is_built: IS_BUILT_TYPE = False
    is_disable: IS_DISABLE_TYPE = False

    def __str__(self):
        return str(self.tower)

    def __repr__(self):
        return f"<{self.chat_id} - \"{self.tower}\" - {self.is_built} / {self.crash_times}>"

    @classmethod
    def _from_mc(cls, mc_client: McClient, chat_id: int) -> ChatObserver:
        """
        Loads data from MC by chat_id and creates an observer object.
        """

        data: TOWER_ON_MC_TYPE = mc_client.get(str(chat_id))
        data = data or get_null_tower_data()
        new_chat_observer = cls(
            mc_client=mc_client,
            chat_id=chat_id,
            tower=Tower(letters=data[0]),
            crash_times=data[1],
            is_built=data[2],
            is_disable=data[3],
        )
        return new_chat_observer

    def _to_mc(self):
        """
        Overwrites its data in the MC.
        """

        data: TOWER_ON_MC_TYPE = (
            self.tower.letters,
            self.crash_times,
            self.is_built,
            self.is_disable,
        )
        self.mc_client.set(str(self.chat_id), data)

    def _delete(self):
        """
        Deletes all data about this chat from memory.
        """
        self.mc_client.delete(str(self.chat_id))

    def add_letter(self, letter: LETTER_MSG_TYPE):
        """
        Adds the next letter to the tower and stores it.
        """

        self.tower.add_letter(letter)
        self._to_mc()

    def nullify(self):
        """
        Nullifies the chat tower and stores it.
        """

        self.tower = Tower()
        self._to_mc()

    def set(
            self,
            crash_times: CRASH_TIMES_TYPE = None,
            is_built: IS_BUILT_TYPE = None,
            is_disable: IS_DISABLE_TYPE = None,
    ):
        """
        Updates chat parameters and
        """

        fields = ["crash_times", "is_built", "is_disable"]
        for name in fields:
            value = locals()[name]
            if value is not None:
                setattr(self, name, value)
        self._to_mc()

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
            and len(self.tower) == Params.CRASH_LENS[self.crash_type]
        )

    @property
    def crash_type(self) -> int:
        """
        Chooses how and when the bot should crash the tower.
        The first breaks are unique, the last one is looped.
        """
        return min(self.crash_times, len(Params.CRASH_LENS)-1)


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
        self.is_enable = is_same_day_today()
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
            self.infos[chat_id] = ChatObserver._from_mc(self.mc_client, chat_id)

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
            chat._delete()
        self.infos = dict()
        self.mc_client.set(TOWER_META_KEY, [])
