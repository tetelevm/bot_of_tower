# Bot Of Tower

In short, it is a bot to control assembled towers.
If longer, here it is:

## Towers

In one [community](https://vas3k.club) (russian IT sect), there are many
different telegram chats by topic/interest/location, and there is a main general
chat room with no particular topic.
And this chat has a tradition of building towers of letters every Wednesday,
with the text being the same: `ITSWEDNESDAYMYDUDES!`.

Tower rules:
- one message - one letter
- one participant - one message (you can not write twice in one tower)
- messages sequentially must make up the text of the tower (no repeating two
  letters, no having messages with wrong letters/other text)
- it is forbidden to remove messages from the tower (e.g. if you write a
  misspelled letter, you may not just remove it)
- only one tower per day
- the tower is built only on Wednesdays

Because of the rules, the tower is often difficult to collect: someone writes
two letters at the same time, someone deliberately crashes the tower, sometimes
there are some independent things like messages from bots).
This bot is a simplification of tower control.

# Running

You can run it locally/on your server.
To do this, you need to execute commands (linux):
```shell
git clone https://github.com/tetelevm/bot_of_tower
cd bot_of_tower
python3.8 -m venv env
. ./env/bin/activate
pip3 install -r requirements.txt
```

Then you need to:
- create a telegram bot
- create a file `.envs` following the example of `.envs_example`
- configure the configuration in `config.py` (more about that below)
- add bot to the chat you're going to monitor (you can do it later, you can add
  it to several)
- give the bot permission to read and write messages
- run the bot (`python3 bot.py`)

The bot is written in `Python`, expects version `Python3.8+`.
Bot is focused on the Russian language, if you need another, then change the
messages bot in the `messages.py` file.

You only need to change `config.py` if you want to change the bot rules anyhow.
Parameters that can be changed:
- `TOWER` - the tower text itself
- `CRASH_LENS` - the length of the letters when the bot automatically crashes 
  towers ( to make it impossible to collect the second tower in a day). The size
  of the list should be no smaller than the size of `messages.py -> MSG_crashes`.
- `MINIMAL_CHECK_LEN` - minimum height of tower, at which bot starts to write
  something when it falls.
- `WEDNESDAY_MODE` - enables _only on Wednesdays_ mode. If off, it just resets
  building at 00:00, but you can build on any day.

# Help and questions

If you want to ask a question or suggest a genius idea, write to `Issues`.
If you want to help in any way, a list of problems that I am unlikely to fix
myself:
- configure startup in Docker
- translate into other languages (at least into English)

If there are any ready-made PRs as well, you're always welcome!
