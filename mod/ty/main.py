import utils
import re
import threading

lock = threading.Lock()
cnt = 0


def OnGroupMsg(msg, group, user):
    global cnt

    with lock:
        if group == 666041783:
            if len(msg['messageChain']) == 2 and msg['messageChain'][1]['type'] == 'Plain':
                text = msg['messageChain'][1]['text']
                if re.search('\bty\b', text) != None:
                    cnt += 1
                else:
                    if re.search('\bnpy\b', text) != None:
                        cnt += 1
                    else:
                        cnt = 0

                if cnt == 2:
                    utils.SendGroupPlain(666041783, '大家不要迫害ty～')
                    print('[ty] send')
            else:
                cnt = 0
