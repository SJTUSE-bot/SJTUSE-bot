import os
import click
import utils
import mod.lboss.main


def Auth():
    r = utils.MustPost('/auth', {
        'authKey': 'sjtusebot1234',
    }, isSession=False)
    utils.session = r['session']
    print('Auth success, key:', utils.session)

    utils.MustPost('/verify', {
        'qq': utils.qqNumber,
    })
    print('Verify success, qq:', utils.qqNumber)


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--host', help="Mirai HTTP host", type=str, default="http://localhost:9500", show_default=True)
@click.argument('qq', type=int, required=True, nargs=1)
def cli(host, qq):
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
                utils.TryPost('/sendGroupMessage', {
                    'target': i['id'],
                    'messageChain': [
                        {'type': 'Plain', 'text': news},
                    ]
                })

    mod.lboss.main.Entry()
    while(1):
        pass


if __name__ == "__main__":
    cli()
