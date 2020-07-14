import requests
import json
import traceback
from decorator import decorator
import tempfile

baseURL = ''
sessionKey = ''
qqNumber = 0


def MessageQuickSend(message_type="GroupMessage", qq=0, group=0, msg=""):
    m = Message(message_type, qq, group)
    m.appendPlain(msg)
    return m.send()


class Message:
    def __init__(self, message_type="GroupMessage", qq=0, group=0):
        self.chain = []
        self.message_type = message_type
        self.qq = qq
        self.group = group

    def send(self):
        if self.message_type == "TempMessage":
            return TryPost('/sendTempMessage', {
                'qq': self.qq,
                'group': self.group,
                'messageChain': json.dumps(self.chain)
            })
        elif self.message_type == "FriendMessage":
            return TryPost('/sendFriendMessage', {
                'target': self.qq,
                'messageChain': json.dumps(self.chain)
            })
        else:
            return TryPost('/sendFriendMessage', {
                'target': self.group,
                'messageChain': json.dumps(self.chain)
            })

    def appendPlain(self, msg):
        self.chain.append({
            "type": "Plain",
            "text": msg,
        })

    def appendAt(self, id):
        self.chain.append({
            "type": "At",
            "target": id
        })

    def appendAtAll(self):
        self.chain.append({
            "type": "AtAll"
        })

    def appendFace(self, faceId=-1, name=""):
        if faceId == -1:
            self.chain.append({
                "type": "Face",
                "name": name,
            })
        else:
            self.chain.append({
                "type": "Face",
                "faceId": faceId
            })

    def strip(self):
        if len(self.chain) == 0:
            return
        if type(self.chain[0]) == str:
            self.chain[0] = self.chain[0].strip()
        if type(self.chain[-1]) == str:
            self.chain[-1] = self.chain[-1].strip()

    # other message type can refer there: https://github.com/project-mirai/mirai-api-http/blob/master/MessageType.md


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


@checkCode
def UploadURL(url, picType):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    r = r.content
    temp = tempfile.TemporaryFile()
    temp.write(r)
    temp.seek(0)
    files = {'img': temp}
    r = requests.post(baseURL + '/uploadImage', data={
        'sessionKey': sessionKey,
        'type': picType,
    }, files=files)
    if r.status_code != 200:
        return None
    r = json.loads(r.text)
    temp.close()
    return r


def SendGroupPlain(group, msg):
    return MessageQuickSend(message_type="GroupMessage", group=group, msg=msg)


@decorator
def CheckAt(func, msg, trigger='', *args, **kw):
    r = None
    if trigger == '':
        if msg['type'] == 'GroupMessage' and (2 <= len(msg['messageChain']) <= 3) and msg['messageChain'][1]['type'] == 'At' and msg['messageChain'][1]['target'] == qqNumber:
            if len(msg['messageChain']) == 2 or (len(msg['messageChain']) == 3 and msg['messageChain'][2]['type'] == 'Plain'and msg['messageChain'][2]['text'] == ' '):
                r = func(*args, **kw)
    else:
        if msg['type'] == 'GroupMessage' and len(msg['messageChain']) == 3 and msg['messageChain'][1]['type'] == 'At' and msg['messageChain'][1]['target'] == qqNumber:
            if msg['messageChain'][2]['type'] == 'Plain' and msg['messageChain'][2]['text'].lstrip() in trigger.split('|'):
                r = func(*args, **kw)
    return r
