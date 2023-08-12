"""
All messages that the bot writes.
"""

from config import Args, Params

_last_crash_chars = Params.TOWER[:Params.CRASH_LENS[-1]]
_github_link = "https://github.com/tetelevm/bot_of_tower"

# (1) - it always says Wednesday when ONEDAY_MODE is on, the DAY_NUMBER parameter
#     is now not considered in the message


MSG_start = (
    "Привет!\n"
    "Я бот, который следит за строительством башен.\n"
    "Добавь меня в чат, где строят башню, и я начну клубнично следить 🍓\n"
    "При добавлении пассивно сижу, но активируюсь (в чате) по команде"
    f" <code>/enable{Args.BOT_USERNAME}</code>."
)


# see (1)
MSG_help = (
    "Я есть бот-надзиратель за башнями.\n"
    "\n"
    "Правила простые:\n"
    f"- башня имеет вид <b>{Params.TOWER}</b>\n"
    "- одна буква - одно сообщение\n"
    "- сообщения с буквами должны идти подряд, не должно быть других сообщений"
    " посреди башни\n"
    "- один участник - одна буква\n"
    "- нельзя менять или удалять сообщения из башни\n"
    f"{'- башня строится только по средам'+chr(10) if Params.ONEDAY_MODE else ''}"
    "- только одна башня в день!\n"
    "\n"
    "Чтобы меня использовать, нужно меня добавить в чат, дать права на отправку"
    f" сообщений и вызвать команду <code>/enable{Args.BOT_USERNAME}</code>.\n"
    f"{' Также важно не забыть, что я работаю только' if Params.ONEDAY_MODE else ''}"
    f"{' по средам, а в остальное время отдыхаю.' if Params.ONEDAY_MODE else ''}\n"
    f"{'В четверг' if Params.ONEDAY_MODE else 'Ежедневно'}"
    " в 00:00 я сбрасываю все собранные башни"
    f"{' и отключаюсь до 00:00 среды' if Params.ONEDAY_MODE else ', чтобы вы не скучали'}.\n"
    "\n"
    f"Мои исходники <a href='{_github_link}'>тут</a>."
)


# see (1)
MSG_not_wednesday = (
    "Отстаньте от меня, у меня важные занятия!\n"
    "Сегодня я авокадюсь, приходите в среду 🥑"
)

MSG_get_ords_no_text = "Соре, здесь нет буков 🤖"
MSG_get_ords_too_long = "Соре, здесь слишком много буков (максимум 30) 🤖"

MSG_only_for_private = (
    "Обращайся с этим в личку, котик 🐈"
)
MSG_only_for_groups = (
    "Соре, я работаю только в групповых чатах.\n"
    "Держи яблочко 🍎"
)
MSG_dont_understand = (
    "Я глупый бот и не понимаю тебя.\n"
    "Я вообще ничего не понимаю, я уточка 🦆"
)


MSG_enable = (
    "Да будет башня!\n"
    "Я за вами слежу 🕵"
)
# see (1)
MSG_enable_but_disable = (
    "Вы меня выключили, а теперь включаете?\n"
    "Ждите следующей среды, я обижен и не включусь, дудки 🎺"
)
MSG_enable_already = (
    "Я уже слежу за вами, чуваки!\n"
    "Продолжайте строить башню 🏗️️"
)


MSG_disable = (
    "Всё с вами понятно, мои чуваки!\n"
    "Отключаюсь 🫥"
)
MSG_disable_not_enable = (
    "Но я же и так не слежу!\n"
    "Люди странные, их надо унич... Кхм-кхм, буп-бип-бип 🤖"
)
MSG_disable_already = (
    "Меня здесь уже выключали!\n"
    "Вы плохо проснулись, держите кофе: ☕"
)


MSG_wednesday_end = (
    # see (1)
    "Всё, чуваки, не среда!\n"
    "Отдыхайте ‍🍝"
)
MSG_day_end = (
    "Конец дня!\n"
    "Башни сброшены 🤿"
)


MSG_fall = (
    "Ну вот, башня упала 🪂\n"
    "В следующий раз старайтесь лучше!"
)
MSG_fall_edited = (
    "Кто-то отредактировал сообщение 🖊️\n"
    "В следующий раз старайтесь лучше!"
)
MSG_fall_deleted = (
    "Кто-то удалил букву ✂️️\n"
    "В следующий раз старайтесь лучше!"
)
MSG_fall_repetition = (
    "Один человек - одна буква, нельзя повторяться 👯‍♀️\n"
    "В следующий раз старайтесь лучше!"
)


MSG_tower_success = (
    "🏆🏆🏆 БАШНЯ СОБРАНА 🏆🏆🏆\n"
    "\n"
    f"<code>{Params.TOWER}</code>"
)


MSG_crashes = [
    (
        "Дуслар, ndaloni!\n"
        "თქვენ ইতিমধ্যে ehitatud タワー आज!\n"
        "Хм, что это со мной? 🤔\n"
        "Короче, башня уже была! 🚨"
    ),
    (
        "👾👾👾"
    ),
    (
        "В вашу башню незаметно прокрались баги, вот они:\n"
        "🪲🪲🪲🪲"
    ),
    (
        "💨"
    ),
    (
        f"Никакой не {_last_crash_chars} 😡"
    ),
]


__all__ = [name for name in locals().keys() if name.startswith("MSG_")]
