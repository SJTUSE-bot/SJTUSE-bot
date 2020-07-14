import os
import click
import utils
import json
import websocket
import mod
import _thread

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


def RegisterMod(config):
    mod.modConfig.append(config)


def onMessage(ws, message):
    msg = json.loads(message)

    user = utils.ParseMsgUser(msg)
    if msg['type'] == 'GroupMessage':
        group = utils.ParseMsgGroup(msg)
        if groupTarget != 0 and group != groupTarget:
            return
        for i in mod.modConfig:
            if i['onGroupMsg'] and i['enable']:
                _thread.start_new_thread(i['onGroupMsg'], (msg, group, user,))
    else:
        for i in mod.modConfig:
            if i['onUserMsg'] and i['enable']:
                _thread.start_new_thread(i['onUserMsg'], (msg, user,))


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--news', help='Show news', type=bool, default=False, show_default=True)
@click.option('--host', help='Mirai HTTP host', type=str, default='http://localhost:9500', show_default=True)
@click.option('--key', help='Mirai HTTP key', type=str, default='sjtusebot1234', show_default=True)
@click.option('--target', help='Target group by default, 0 for all', type=int, default=0, show_default=True)
@click.argument('qq', type=int, required=True, nargs=1)
def cli(news, host, key, target, qq):
    global groupTarget

    with open('VERSION', 'r') as f:
        version = f.read()
        print('SJTUSE-bot v' + version)
    groupTarget = target
    utils.baseURL = host
    utils.qqNumber = qq
    print('Mirai host is set to', utils.baseURL)
    print('Bot target is set to', groupTarget)
    print('QQ number is set to', utils.qqNumber)

    print('Mod:')
    for i in mod.modConfig:
        print(i['name'], end=': ')
        if i['enable']:
            click.secho('Enabled', fg='green')
        else:
            click.secho('Disabled', fg='red')
    print('')

    r = utils.MustGet('/about', isSession=False)
    print('Mirai HTTP version:', r['data']['version'])
    Auth(key)
    print('Bot started')

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

    for i in mod.modConfig:
        if i['entry'] and i['enable']:
            _thread.start_new_thread(i['entry'], ())

    wsURL = 'ws://' + utils.baseURL.split('://', 2)[1]
    ws = websocket.WebSocketApp(wsURL + '/message?sessionKey=' +
                                utils.sessionKey, on_message=onMessage)
    ws.run_forever()


if __name__ == '__main__':
    cli()
