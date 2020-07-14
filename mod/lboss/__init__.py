import bot
import mod.lboss.main as main

config = {
    'name': 'lboss',
    'enable': True,
    'entry': main.Entry,
    'onGroupMsg': None,
    'onUserMsg': None,
}
bot.RegisterMod(config)
