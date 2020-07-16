import bot
from . import main

config = {
    'name': 'reminder',
    'enable': True,
    'entry': main.Entry,
    'onGroupMsg': main.OnGroupMsg,
    'onUserMsg': None,
}
bot.RegisterMod(config)
