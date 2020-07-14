import bot
from . import main

config = {
    'name': 'repeater',
    'enable': True,
    'entry': None,
    'onGroupMsg': main.OnGroupMsg,
    'onUserMsg': None,
}
bot.RegisterMod(config)
