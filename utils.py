import requests
import json
import traceback
from decorator import decorator
import tempfile

baseURL = ''
sessionKey = ''
qqNumber = 0
target = ''


@decorator
def checkCode(func, *args, **kw):
    r = func(*args, **kw)
    if r['code'] != 0:
        print(r)
        traceback.print_stack()
    return r


@decorator
def mustCode(func, *args, **kw):
    r = func(*args, **kw)
    if r['code'] != 0:
        print(r)
        traceback.print_stack()
        exit(r['code'])
    return r


def Get(url, params=None, isSession=True):
    if isSession:
        if params == None:
            params = {}
        params['sessionKey'] = sessionKey
    return json.loads(requests.get(baseURL + url, params=params).text)


@mustCode
def MustGet(url, params=None, isSession=True):
    return Get(url, params, isSession)


@checkCode
def TryGet(url, params=None, isSession=True):
    return Get(url, params, isSession)


def Post(url, data, isSession=True):
    if isSession:
        if data == None:
            data = {}
        data['sessionKey'] = sessionKey
    return json.loads(requests.post(baseURL + url, json=data).text)


@mustCode
def MustPost(url, data, isSession=True):
    return Post(url, data, isSession)


@checkCode
def TryPost(url, data, isSession=True):
    return Post(url, data, isSession)


def UploadURL(url, picType, ttl):
    r = requests.get(url, timeout=ttl)
    if r.status_code != 200:
        return None
    r = r.content
    temp = tempfile.TemporaryFile()
    temp.write(r)
    temp.seek(0)
    files = {'img': temp}
    r = json.loads(requests.post(baseURL + '/uploadImage', data={
        'sessionKey': sessionKey,
        'type': picType,
    }, files=files).text)
    temp.close()
    return r


def SendGroupPlain(group, msg):
    return TryPost('/sendGroupMessage', {
        'target': group,
        'messageChain': [
            {'type': 'Plain', 'text': msg},
        ]
    })


@decorator
def CheckAt(func, msg=0, trigger='', *args, **kw):
    r = None
    msg = args[msg]
    if trigger == '':
        if msg['type'] == 'GroupMessage' and (2 <= len(msg['messageChain']) <= 3) and msg['messageChain'][1]['type'] == 'At' and msg['messageChain'][1]['target'] == qqNumber:
            if len(msg['messageChain']) == 2 or (len(msg['messageChain']) == 3 and msg['messageChain'][2]['type'] == 'Plain'and msg['messageChain'][2]['text'] == ' '):
                r = func(*args, **kw)
    else:
        if msg['type'] == 'GroupMessage' and len(msg['messageChain']) == 3 and msg['messageChain'][1]['type'] == 'At' and msg['messageChain'][1]['target'] == qqNumber:
            if msg['messageChain'][2]['type'] == 'Plain' and msg['messageChain'][2]['text'].lstrip() in trigger.split('|'):
                r = func(*args, **kw)
    return r
