import os
import click
import utils
import json
import websocket
from mod.lboss import main as lboss
from mod.repeater import main as repeater
from mod.pixiv import main as pixiv
from mod.ty import main as ty

groupTarget = 0


def Auth(key):
    r = utils.MustPost('/auth', {
        'authKey': key,
    }, isSession=False)
    utils.sessionKey = r['session']
    print('Auth success, key:', utils.sessionKey)

    utils.MustPost('/verify', {
        'qq': utils.qqNumber,
    })
    print('Verify success, qq:', utils.qqNumber)


def onMessage(ws, message):
    message = json.loads(message)

    target = utils.ParseMsgGroup(message)
    if groupTarget != 0 and target != groupTarget:
        return

    pixiv.OnMessage(message)
    repeater.OnMessage(message)
    ty.OnMessage(message)


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--news', help="Show news", type=bool, default=False, show_default=True)
@click.option('--host', help="Mirai HTTP host", type=str, default="http://localhost:9500", show_default=True)
@click.option('--key', help="Mirai HTTP key", type=str, default="sjtusebot1234", show_default=True)
@click.option('--target', help="Target group by default, 0 for all", type=int, default=0, show_default=True)
@click.argument('qq', type=int, required=True, nargs=1)
def cli(news, host, key, target, qq):
    global groupTarget

    with open('VERSION', 'r') as f:
        version = f.read()
        print('SJTUSE-bot v' + version)
    groupTarget = target
    utils.baseURL = host
    utils.qqNumber = qq
    print("Mirai host is set to", utils.baseURL)
    print("Bot target is set to", groupTarget)
    print("QQ number is set to", utils.qqNumber)

    r = utils.MustGet('/about', isSession=False)
    print("Mirai HTTP version:", r['data']['version'])
    Auth(key)

    if news:
        r = utils.Get('/groupList')
        with open('NEWS', 'r') as f:
            news = f.read()
            # support broadcast mode and single target mode
            if groupTarget == 0:
                for i in r:
                    utils.SendGroupPlain(i['id'], news)
            else:
                utils.SendGroupPlain(groupTarget, news)
    lboss.Entry()

    wsURL = "ws://" + utils.baseURL.split("://", 2)[1]
    ws = websocket.WebSocketApp(wsURL + "/message?sessionKey=" +
                                utils.sessionKey, on_message=onMessage)
    ws.run_forever()


if __name__ == "__main__":
    cli()
