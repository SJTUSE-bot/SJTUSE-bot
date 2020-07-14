import os
import click
import utils
import json
import websocket
from mod.lboss import main as lboss
from mod.repeater import main as repeater
from mod.pixiv import main as pixiv
from mod.ty import main as ty


def Auth():
    r = utils.MustPost('/auth', {
        'authKey': 'sjtusebot1234',
    }, isSession=False)
    utils.sessionKey = r['session']
    print('Auth success, key:', utils.sessionKey)

    utils.MustPost('/verify', {
        'qq': utils.qqNumber,
    })
    print('Verify success, qq:', utils.qqNumber)


def onMessage(ws, message):
    message = json.loads(message)

    pixiv.OnMessage(message)
    repeater.OnMessage(message)
    ty.OnMessage(message)


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--host', help="Mirai HTTP host", type=str, default="http://localhost:9500", show_default=True)
@click.argument('qq', type=int, required=True, nargs=1)
def cli(host, qq):
    with open('VERSION', 'r') as f:
        version = f.read()
        print('SJTUSE-bot v' + version)

    utils.baseURL = host
    utils.qqNumber = qq
    print("Mirai host is set to", utils.baseURL)
    print("QQ number is set to", utils.qqNumber)

    r = utils.MustGet('/about', isSession=False)
    print("Mirai HTTP version:", r['data']['version'])
    Auth()

    if not os.path.exists(".new"):
        open('.new', 'w').close()
        r = utils.Get('/groupList')
        with open('News', 'r') as f:
            news = f.read()
            for i in r:
                utils.SendGroupPlain(i['id'], news)

    lboss.Entry()

    wsURL = "ws://" + utils.baseURL.split("://", 2)[1]
    ws = websocket.WebSocketApp(wsURL + "/message?sessionKey=" +
                                utils.sessionKey, on_message=onMessage)
    ws.run_forever()


if __name__ == "__main__":
    cli()
