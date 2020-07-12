import requests
import json
import time
import os
from decorator import decorator

baseURL = "http://localhost:8080"
session = ''


@decorator
def checkCode(func, *args, **kw):
    r = func(*args, **kw)
    if r['code'] != 0:
        print(r)
    return r


@checkCode
def Get(url):
    return json.loads(requests.get(baseURL + url).text)


@checkCode
def Post(url, data):
    return json.loads(requests.post(baseURL + url, json=data).text)


def Auth():
    global session

    r = Post('/auth', {
        'authKey': 'sjtusebot1234',
    })
    session = r['session']
    print('Auth success, key:', session)

    r = Post('/verify', {
        'sessionKey': session,
        'qq': os.environ['qq'],
    })
    print('Verify success, qq:', os.environ['qq'])


if __name__ == "__main__":
    r = Get('/about')
    print("Mirai HTTP version:", r['data']['version'])
    Auth()
    Post('/sendGroupMessage', {
        'sessionKey': session,
        'target': 666041783,
        'messageChain': [
            {'type': 'Plain', 'text': '大家好我是SJTUSE-Bot，目前只有一个功能每天早上8点提醒LBOSS女装，后面可能会加其他功能:)'},
        ]
    })

    while True:
        tm = time.localtime(time.time())
        if tm.tm_hour == 8 and tm.tm_min == 0:
            Post('/sendGroupMessage', {
                'sessionKey': session,
                'target': 666041783,
                'messageChain': [
                    # {"type": "At", "target": },
                    {'type': 'Plain', 'text': 'LBOSS今天女装了🐴'},
                ]
            })
            print("sended")
            time.sleep(86340)   # 24h-60s
        time.sleep(1)
