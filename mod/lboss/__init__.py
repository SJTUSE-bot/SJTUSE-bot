import bot
from . import main

config = {
    'name': 'lboss',
    'enable': True,
    'entry': main.Entry,
    'onGroupMsg': None,
    'onUserMsg': None,
}
bot.RegisterMod(config)
