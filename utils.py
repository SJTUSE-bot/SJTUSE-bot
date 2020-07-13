import requests
import json
import traceback
from decorator import decorator
import tempfile

baseURL = ''
sessionKey = ''
qqNumber = 0


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


def UploadURL(url, picType):
    r = requests.get(url)
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
