import requests
import json
import traceback
from decorator import decorator
import tempfile
from enum import IntEnum, auto

baseURL = ''
sessionKey = ''
qqNumber = 0


class MessageType(IntEnum):
    GROUP = 1
    FRIEND = 2
    TEMP = 3


class Message:
    '''Warp of send message

    See more: https://github.com/project-mirai/mirai-api-http/blob/master/MessageType.md
    '''

    def __init__(self, msgType=MessageType.GROUP, qq=0, group=0):
        self.chain = []
        self.msgType = msgType
        self.qq = qq
        self.group = group

    def send(self):
        if self.msgType == MessageType.TEMP:
            return TryPost('/sendTempMessage', {
                'qq': self.qq,
                'group': self.group,
                'messageChain': self.chain
            })
        elif self.msgType == MessageType.FRIEND:
            return TryPost('/sendFriendMessage', {
                'target': self.qq,
                'messageChain': self.chain
            })
        elif self.msgType == MessageType.GROUP:
            return TryPost('/sendGroupMessage', {
                'target': self.group,
                'messageChain': self.chain
            })
        else:
            assert 0

    def appendPlain(self, msg):
        self.chain.append({
            "type": "Plain",
            "text": msg,
        })

    def appendImage(self, imageId=None, url=None, path=None):
        tmp = {"type": "Image"}
        if imageId:
            tmp['imageId'] = imageId
        if url:
            tmp['url'] = url
        if path:
            tmp['path'] = path
        assert len(tmp) != 0
        self.chain.append(tmp)

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


'''
Send function wrapped
'''


def SendPlain(msgType=MessageType.GROUP, qq=0, group=0, msg=""):
    m = Message(msgType, qq, group)
    m.appendPlain(msg)
    return m.send()


def SendGroupPlain(group, msg):
    return SendPlain(msgType=MessageType.GROUP, group=group, msg=msg)


@decorator
def checkCode(func, *args, **kw):
    '''Check return code == 0, otherwise print call stack
    '''
    r = func(*args, **kw)
    if 'code' not in r or r['code'] != 0:
        print(r)
        traceback.print_stack()
    return r


@decorator
def mustCode(func, *args, **kw):
    '''Check return code == 0, otherwise print call stack and exit
    '''
    r = func(*args, **kw)
    if 'code' not in r or r['code'] != 0:
        print(r)
        traceback.print_stack()
        exit(-1)
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
    '''Only use this function when url can't parse automatically!
    '''
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


@decorator
def TriggerCmd(func, trigger=[], *args, **kw):
    '''Trigger cmd message on condition.

    :param trigger: required, trigger the function when the text start with one of the trigger and a space.

    e.g. @TriggerCmd(trigger=['.bot1','.bot2']) will trigger when text is '.bot1 xxx' '.bot2 ' but not '.bot1'(without space)
    '''
    assert len(trigger) > 0
    msg = args[0]
    for i in trigger:
        if len(msg['messageChain']) == 2 and msg['messageChain'][1]['type'] == 'Plain':
            if msg['messageChain'][1]['text'].startswith(i + ' '):
                return func(*args, **kw)
    return None


@decorator
def TriggerAt(func, trigger=[], *args, **kw):
    '''Trigger @ message on condition.

    :param trigger: trigger the function when the text equals one of the trigger.

    e.g. @TriggerAt will trigger when message is '@bot' and '@bot '(trimmed right space when no other text)

    e.g. @TriggerAt(trigger=['bot1','bot2']) will trigger when message is '@bot bot1' but not '@bot bot2 '(space not trim)
    '''
    r = None
    msg = args[0]
    group = args[1]
    if len(trigger) == 0:  # sometimes @ will add space after name, treat it equal
        if (2 <= len(msg['messageChain']) <= 3) and msg['messageChain'][1]['type'] == 'At' and msg['messageChain'][1]['target'] == qqNumber:
            if len(msg['messageChain']) == 2 or (len(msg['messageChain']) == 3 and msg['messageChain'][2]['type'] == 'Plain' and msg['messageChain'][2]['text'] == ' '):
                r = func(*args, **kw)
    else:
        if len(msg['messageChain']) == 3 and msg['messageChain'][1]['type'] == 'At' and msg['messageChain'][1]['target'] == qqNumber:
            if msg['messageChain'][2]['type'] == 'Plain' and msg['messageChain'][2]['text'].lstrip() in trigger:
                r = func(*args, **kw)
    return r


def ParseMsgGroup(msg):
    '''Parse message group number.

    :return: None for not group, otherwise group number.
    '''
    if 'sender' in msg and 'group' in msg['sender']:
        return msg['sender']['group']['id']
    return None


def ParseMsgUser(msg):
    '''Parse message user number, all kinds of msg capable.

    :return: None for error, otherwise user number.
    '''
    if 'sender' in msg:
        return msg['sender']['id']
    return None
