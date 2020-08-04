import _thread
import time
import utils


def Entry():
    while True:
        tm = time.localtime(time.time())
        if tm.tm_hour == 8 and tm.tm_min == 0:
            utils.SendGroupPlain(666041783, '据说LBOSS今天女装！')
            print("[lboss] send")
            time.sleep(86340)   # 24h-60s
        time.sleep(10)
