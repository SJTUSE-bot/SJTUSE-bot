import bot
import mod.pixiv.main as main

config = {
    'name': 'pixiv',
    'enable': True,
    'entry': None,
    'onGroupMsg': main.OnGroupMsg,
    'onUserMsg': None,
}
bot.RegisterMod(config)
