import utils
import threading

history = {}
lock = threading.Lock()


def OnGroupMsg(msg, group, user):
    global history

    with lock:
        if len(msg['messageChain']) == 2 and msg['messageChain'][1]['type'] == 'Plain':
            text = msg['messageChain'][1]['text']
            if group not in history:
                history[group] = {}
                history[group]['msg'] = text
                history[group]['times'] = 0
            if history[group]['msg'] == text:
                history[group]['times'] += 1
            else:
                history[group]['msg'] = text
                history[group]['times'] = 1

            if history[group]['times'] == 3:
                utils.SendGroupPlain(group, text)
                print('[repeater] send')
        else:
            if group not in history:
                history[group] = {}
            history[group]['msg'] = ''
            history[group]['times'] = 0
