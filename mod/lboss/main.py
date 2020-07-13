import _thread
import time
import utils


def remainder():
    while True:
        tm = time.localtime(time.time())
        if tm.tm_hour == 8 and tm.tm_min == 0:
            utils.TryPost('/sendGroupMessage', {
                'target': 666041783,
                'messageChain': [
                    {'type': 'Plain', 'text': 'LBOSS今天女装了🐴'},
                ]
            })
            print("[lboss] send")
            time.sleep(86340)   # 24h-60s
        time.sleep(1)


def Entry():
    _thread.start_new_thread(remainder, ())
