import bot
from . import main

config = {
    'name': 'pixiv',
    'enable': True,
    'entry': None,
    'onGroupMsg': main.OnGroupMsg,
    'onUserMsg': None,
}
bot.RegisterMod(config)
