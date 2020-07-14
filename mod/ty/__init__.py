import bot
import mod.ty.main as main

config = {
    'name': 'ty',
    'enable': True,
    'entry': None,
    'onGroupMsg': main.OnGroupMsg,
    'onUserMsg': None,
}
bot.RegisterMod(config)
