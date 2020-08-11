import _thread
import time
import utils
from dateutil import rrule
import datetime


def Entry():
    while True:
        tm = time.localtime(time.time())
        if tm.tm_hour == 8 and tm.tm_min == 0:
            last = datetime.date(2020, 8, 11)
            delta = rrule.rrule(rrule.DAILY, dtstart=last,
                                until=datetime.datetime.now()).count()
            utils.SendGroupPlain(
                666041783, '今天又是摸鱼的一天，LBOSS上一次女装是在{}天前'.format(delta - 1))
            print("[lboss] send")
            time.sleep(86340)   # 24h-60s
        time.sleep(10)
