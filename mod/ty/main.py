import utils
import re

cnt = 0


def OnMessage(msg):
    global cnt

    if msg['type'] == 'GroupMessage' and msg['sender']['group']['id'] == 666041783:
        if len(msg['messageChain']) == 2 and msg['messageChain'][1]['type'] == 'Plain':
            text = msg['messageChain'][1]['text']
            if re.search('[^a-zA-Z]?ty[^a-zA-Z]?', text) != None:
                cnt += 1
            else:
                cnt = 0

            if cnt == 2:
                utils.SendGroupPlain(666041783, '大家不要迫害ty～')
                print('[ty] send')
