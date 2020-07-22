import utils
import threading

history = {}
lock = threading.Lock()


def OnGroupMsg(msg, group, user):
    global history

    with lock:
        data = msg['messageChain'][1:]
        for i in range(len(data)):
            if data[i]['type'] == 'Image':
                data[i]['url'] = None
        if group not in history:
            history[group] = {}
            history[group]['msg'] = data
            history[group]['times'] = 0
        if history[group]['msg'] == data:
            history[group]['times'] += 1
        else:
            history[group]['msg'] = data
            history[group]['times'] = 1

        if history[group]['times'] == 3:
            msg = utils.Message(group=group)
            msg.appendCustom(data)
            msg.send()
            print('[repeater] send')
