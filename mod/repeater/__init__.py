import bot
import mod.repeater.main as main

config = {
    'name': 'repeater',
    'enable': True,
    'entry': None,
    'onGroupMsg': main.OnGroupMsg,
    'onUserMsg': None,
}
bot.RegisterMod(config)
