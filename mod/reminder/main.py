import utils
import time

plan = []


def Entry():
    global plan
    with open('./mod/reminder/plan.txt', "r") as f:
        s = f.read().splitlines()
        for i in s:
            tmp = i.split()
            plan.append([int(tmp[0]), int(tmp[1]), tmp[2]])
    while(True):
        tm = int(time.time())
        for i in plan:
            if i[0] < tm:
                msg = utils.Message(group=i[1])
                msg.appendAtAll()
                msg.appendPlain(i[2])
                msg.send()
                print('[reminder] send')
                plan.remove(i)
                with open('./mod/reminder/plan.txt', "w") as f:
                    for j in plan:
                        f.write(j[0] + ' ' + j[1] + ' ' + j[2] + '\n')
        time.sleep(30)


@utils.TriggerAdmin
@utils.TriggerAt(trigger=['remind '])
def OnGroupMsg(msg, group, user):
    text = msg['messageChain'][2]['text'].lstrip().split(' ', 2)
    message = text[1]
    tm = int(time.mktime(time.strptime(text[2], "%Y.%m.%d %H.%M")))
    plan.append([tm, group, message])
    with open('./mod/reminder/plan.txt', "w") as f:
        for i in plan:
            f.write(str(i[0]) + ' ' + str(i[1]) + ' ' + i[2] + '\n')

    msg = utils.Message(group=group)
    msg.appendAt(user)
    msg.appendPlain('闹钟已添加')
    msg.send()
