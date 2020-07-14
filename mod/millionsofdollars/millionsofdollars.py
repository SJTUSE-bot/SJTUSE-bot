import json
import random
from functools import wraps
from math import floor
import re

from utils import Message, MessageQuickSend

commandStart = ['.', '']
onCommandTree = {}


def OnMessage(message):
    session = {"sender": message["sender"], "messageChain": message["messageChain"], "type": message["type"]}
    command_name = ""
    now_parsing = []
    argc = -1
    argv = []
    for elem in message["messageChain"]:
        if elem["type"] == "Source":
            session["message_id"] = elem["id"]
            session["time"] = elem["time"]
        elif elem["type"] == "Plain":
            for char in elem["text"]:
                if char == ' ':
                    argc += 1
                    if argc > 0 and len(now_parsing) != 0:
                        argv.append(now_parsing)
                    now_parsing = []
                    continue
                if argc == -1:
                    command_name += char
                else:
                    if len(now_parsing) == 0 or type(now_parsing[-1]) != str:
                        now_parsing.append(char)
                    else:
                        now_parsing[-1] += char
        else:
            now_parsing.append(elem)
    argv.append(now_parsing)
    session["argc"] = argc
    session["argv"] = argv

    r = f"[{'|'.join(commandStart)}]"
    for key in onCommandTree:
        if re.match(r + key, command_name) or \
                ('' in commandStart and re.match(key, command_name)):
            onCommandTree[key](session)


def on_command(name, aliases):
    def decorator(func):
        f = func
        onCommandTree[name] = f
        for alias in aliases:
            onCommandTree[alias] = f

        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    return decorator


class MDError(Exception):
    def __init__(self, message):
        self.message = message


class Loot:
    def __init__(self, role, ante, loot):
        self.role = role
        self.ante = ante
        self.loot = loot


class MDGlobal:
    bot = None
    group_map = {}
    player_map = {}
    loot_list = []
    card_name = ['', '告密者', '暴徒', '司机', '恶棍', '谋士']


class Game:
    class Status:
        Running = 0
        Pending = 1

    class Phrase:
        Planning = 0
        Negotiation = 1
        TheHeist = 2
        SharingTheLoot = 3

    def __init__(self, group_id):
        self.group_id = group_id
        self.status = Game.Status.Pending
        self.loot = None
        self.loot_index = 0
        self.players = []
        self.ante = {}
        self.phrase = Game.Phrase.Planning
        self.roles = []
        self.loot_players = {}
        MDGlobal.group_map[group_id] = self

    def destruct(self):
        for player in self.players:
            player.destruct()
        del MDGlobal.group_map[self.group_id]

    def reset(self):
        self.status = Game.Status.Pending
        self.loot = None
        self.loot_index = 0
        self.ante = {}
        self.phrase = Game.Phrase.Planning
        self.roles = []
        self.loot_players = {}
        for player in self.players:
            player.reset()

    def add_player(self, user_id):
        if self.status == Game.Status.Pending:
            self.players.append(Player(self, user_id))
        else:
            raise MDError("游戏已经开始，加入失败")

    def remove_player(self, user_id):
        m = Message(group=self.group_id)
        for i in range(len(self.players)):
            if self.players[i].qq_id == user_id:
                m.appendAt(self.players[i].qq_id)
                m.appendPlain("退出成功")
                m.send()
                self.players[i].destruct()
                del self.players[i]
                return
        m.appendPlain("未找到")
        m.appendAt(user_id)
        m.send()

    def try_end_game(self):
        m = Message(group=self.group_id)
        max_player = None
        max_value = 0
        for player in self.players:
            if self.loot_index == 8 or player.balance >= 20:
                if player.balance > max_value:
                    max_player = player
                    max_value = max_value
        if max_player is not None:
            self.reset()
            self.status = Game.Status.Pending
            m.appendPlain("游戏结束！玩家")
            m.appendAt(max_player.qq_id)
            m.appendPlain("胜利！\n如果需要再次开始游戏，请输入.md start")
            m.send()
            return True
        return False

    def start_game(self):
        if not 4 <= len(self.players) <= 8:
            MessageQuickSend(group=self.group_id, msg=f"目前体验版只支持 4 到 8 人游玩。\n当前玩家人数为 {len(self.players)} 人，无法开始游戏")
            return
        self.status = Game.Status.Running
        self.do_phrase()

    def show_balance(self):
        m = Message(group=self.group_id)
        for player in self.players:
            m.appendAt(player.qq_id)
            m.appendPlain(f"：{player.balance}00万美金，威胁卡数量：{player.intimidation}\n")
        m.strip()
        m.send()

    def do_phrase(self):
        m = Message(group=self.group_id)
        if self.phrase == Game.Phrase.Planning:
            self.loot_players = {}
            self.loot = MDGlobal.loot_list[self.loot_index]
            self.loot_index += 1
            if self.loot.role != 0:
                m.appendPlain(
                    f"谋划阶段：第{self.loot_index}轮\n当前银行战利品为{self.loot.loot}00万美金，保证金{self.loot.ante}00万美金，加成角色为{MDGlobal.card_name[self.loot.role]}\n")
            else:
                m.appendPlain(f"谋划阶段：第{self.loot_index}轮\n当前银行战利品为{self.loot.loot}00万美金，保证金{self.loot.ante}00万美金\n")
            for player in self.players:
                player.role = Player.Role.TBD
                player.exit = False
                self.ante[player.qq_id] = player.minus_balance(self.loot.ante)
                m.appendPlain("玩家")
                m.appendAt(player.qq_id)
                m.appendPlain(f"已缴纳保证金{self.ante[player.qq_id]}00万美金\n")
            m.appendPlain("请玩家私聊 bot 输入 .md [角色名] 决定本回合要扮演的角色")
            m.send()
        elif self.phrase == Game.Phrase.Negotiation:
            random.shuffle(self.players)
            msg = "谈判阶段：\n目前已知晓的玩家身份有："
            for i in range(1, len(self.players)):
                msg += f'{MDGlobal.card_name[self.players[i].role]}、'
            MessageQuickSend(group=self.group_id, msg=msg.strip())
        elif self.phrase == Game.Phrase.TheHeist:
            self.roles = [[], [], [], [], [], []]
            for player in self.players:
                if not player.exit:
                    self.roles[player.role].append(player)
            snitches = self.roles[1]
            if len(snitches) == 0:
                MessageQuickSend(group=self.group_id, msg="无告密者，继续下一阶段")
                self.phrase3_continue(0)
            elif len(snitches) == 1:
                m = Message()
                m.appendPlain("告密者为")
                m.appendAt(snitches[0].qq_id)
                m.appendPlain("，请告密者输入 .md rm [角色种类] 决定要移除的角色")
                self.loot_players[Player.Role.Snitch] = snitches[0]
                m.send()
            else:
                m = Message()
                m.appendPlain("告密者为")
                for player in snitches:
                    m.appendAt(player.qq_id)
                    m.appendPlain("、")
                m.appendPlain('\n所有告密者将被淘汰，并无法取回保证金')
                m.send()
                self.phrase3_continue(0)

    def phrase3_continue(self, role):
        if role != 0:
            flag = False
            for i in range(1, len(self.players)):
                if self.players[i].role == role:
                    flag = True
                    break
            if not flag:
                raise MDError("告密者只能选择场上出现过的角色")
        m = Message()
        for i in range(2, 6):
            arr = self.roles[i]

            def appendRoleArr(msg: Message):
                for p in arr:
                    msg.appendAt(p.qq_id)
                    msg.appendPlain("、")
                del msg.chain[-1]

            if i == role:
                if i == Player.Role.Brute:
                    m.appendPlain("暴徒已被告密者移除，但暴徒们（")
                    appendRoleArr(m)
                    m.appendPlain("）取回了自己的保证金\n")
                    for p in arr:
                        p.add_balance(self.ante[p.qq_id])
                else:
                    m.appendPlain(f"{MDGlobal.card_name[i]}们（")
                    appendRoleArr(m)
                    m.appendPlain("已被告密者移除\n")
                continue

            if len(arr) == 0:
                m.appendPlain(f"无{MDGlobal.card_name[i]}\n")
                continue
            elif len(arr) == 1:
                m.appendPlain(f"{MDGlobal.card_name[i]}人选已确定：")
                appendRoleArr(m)
                m.appendPlain("\n")
                self.loot_players[i] = arr[0]
                continue
            else:
                if i == Player.Role.Brute:
                    m.appendPlain("暴徒们（")
                    appendRoleArr(m)
                    m.appendPlain("）因数量太多被移除了，但暴徒们取回了自己的保证金\n")
                    for p in arr:
                        p.add_balance(self.ante[p.qq_id])
                else:
                    m.appendPlain(f"{MDGlobal.card_name[i]}们（")
                    appendRoleArr(m)
                    m.appendPlain("）数量太多，被全部移除了\n")
                continue
        if len(self.loot_players) == 1 and Player.Role.Snitch in self.loot_players:
            m.appendPlain("最后的队伍只剩下告密者。告密者亏损了300万美金！")
            self.loot_players[Player.Role.Snitch].minus_balance(3)
            m.send()
        else:
            m.appendPlain(f"共有{len(self.loot_players)}名玩家行动成功！\n")
            money = self.loot.loot
            if Player.Role.MasterMind in self.loot_players:
                money += 2
                m.appendPlain("因为队伍里存在谋士，因此战利品增加了200万美金！\n")
            d = {}
            for key in self.loot_players:
                d[key] = floor(money / len(self.loot_players))
            if Player.Role.Brute in self.loot_players and Player.Role.Crook in self.loot_players:
                d[Player.Role.Brute] -= 2
                d[Player.Role.Crook] += 2
            if Player.Role.Driver in self.loot_players:
                for r in d:
                    if r != Player.Role.Driver:
                        d[Player.Role.Driver] += 1
                        d[r] -= 1
            if Player.Role.Brute in self.loot_players:
                self.loot_players[Player.Role.Brute].intimidation += 1
            m.appendPlain("最终收获如下：\n")
            msg_list = []
            for r in d:
                if self.loot.role == r:
                    d[r] += 1
                msg_list.append(
                    f"{MDGlobal.card_name[r]}：{d[r]}00万美金" + ("、1张威胁卡" if r == Player.Role.Brute else ""))
                self.loot_players[r].add_balance(
                    d[r] + self.ante[self.loot_players[r].qq_id])
            msg = '\n'.join(msg_list)
            m.appendPlain(msg)
            m.send()
        self.show_balance()
        if not self.try_end_game():
            self.phrase = Game.Phrase.Planning
            self.do_phrase()

    def try_next(self):
        for player in self.players:
            if player.role == 0:
                return
        self.phrase = Game.Phrase.Negotiation
        self.do_phrase()


class Player:
    class Role:
        TBD = 0
        Snitch = 1
        Brute = 2
        Driver = 3
        Crook = 4
        MasterMind = 5

    def __init__(self, game, qq_id):
        self.game = game
        self.qq_id = qq_id
        self.balance = 5
        self.role = Player.Role.TBD
        self.exit = False
        self.intimidation = 0
        MDGlobal.player_map[qq_id] = self

    def destruct(self):
        del MDGlobal.player_map[self.qq_id]

    def reset(self):
        self.balance = 5
        self.role = Player.Role.TBD
        self.exit = False
        self.intimidation = 0

    def add_balance(self, money):
        if money < 0:
            self.minus_balance(-money)
            return
        self.balance += money

    def minus_balance(self, money):
        if self.balance >= money:
            self.balance -= money
            return money
        else:
            t = self.balance
            self.balance = 0
            return t


MDGlobal.loot_list.append(Loot(Player.Role.Snitch, 1, 8))
MDGlobal.loot_list.append(Loot(Player.Role.Brute, 1, 8))
MDGlobal.loot_list.append(Loot(Player.Role.Driver, 1, 8))
MDGlobal.loot_list.append(Loot(Player.Role.Crook, 1, 8))
MDGlobal.loot_list.append(Loot(Player.Role.MasterMind, 1, 8))
MDGlobal.loot_list.append(Loot(Player.Role.TBD, 2, 10))
MDGlobal.loot_list.append(Loot(Player.Role.TBD, 2, 12))
MDGlobal.loot_list.append(Loot(Player.Role.TBD, 1, 9))
random.shuffle(MDGlobal.loot_list)


@on_command('million_dollars', aliases=['md', '百万美金'])
def million_dollars(session):
    args = session['argv']
    user_id = session['sender']['id']
    if 'group' in session['sender']:
        group_id = session['sender']['group']['id']
    else:
        group_id = 0
    if args[0] == "new" and group_id != 0:
        Game(group_id)
        MessageQuickSend(msg=f"群{group_id}的游戏已创建", group=group_id)
        return
    game = (None if group_id not in MDGlobal.group_map else MDGlobal.group_map[group_id]) or \
           (None if user_id not in MDGlobal.player_map else MDGlobal.player_map[user_id].game)
    if game is None:
        MessageQuickSend(msg="本群还未创建游戏，请输入 .md new 创建", group=group_id)
        return

    if args[0] == "dismiss":
        game.destruct()
        session.send("游戏已解散")
        return
    if args[0] == "join":
        game.add_player(user_id)
        m = Message()
        m.appendAt(user_id)
        m.appendPlain("已加入")
        m.send()
        return
    if args[0] == "leave":
        game.remove_player(user_id)
        m = Message()
        m.appendAt(user_id)
        m.appendPlain("已退出")
        m.send()
        return
    if args[0] == "start":
        game.start_game()
        # session.send("游戏开始")
        return

    if game.status == Game.Status.Pending:
        MessageQuickSend(msg="游戏未开始。若准备完毕，请使用 .md start 开始", group=group_id)
        return

    if args[0] in ["告密者", "暴徒", "恶棍", "司机", "谋士"]:
        if game.phrase == Game.Phrase.Planning and MDGlobal.player_map[user_id].role == 0:
            MDGlobal.player_map[user_id].role = MDGlobal.card_name.index(
                args[0])
        MessageQuickSend(message_type=session["type"], group=group_id, qq=user_id, msg=f"你已选择{args[0]}角色")
        game.try_next()
        return

    if args[0] == "st":
        game.show_balance()
        return
    if args[0] == "see" and game.phrase == Game.Phrase.Negotiation and MDGlobal.player_map[user_id].intimidation > 0:
        r_id = args[1]["target"]
        pl2 = MDGlobal.player_map[r_id]
        MDGlobal.player_map[user_id].intimidation -= 1
        MessageQuickSend(message_type="TempMessage", qq=user_id, group=group_id, msg=f"{r_id}的身份是{MDGlobal.card_name[pl2.role]}")
    if args[0] == "exit" and game.phrase == Game.Phrase.Negotiation:
        MDGlobal.player_map[user_id].exit = True
        MDGlobal.player_map[user_id].add_balance(game.ante[user_id])
        game.add_player(user_id)
        m = Message()
        m.appendAt(user_id)
        m.appendPlain("已放弃本轮行动")
        m.send()
    if args[0] == "en" and game.phrase == Game.Phrase.Negotiation:
        game.phrase = Game.Phrase.TheHeist
        game.do_phrase()
    if args[0] == "rm" and game.phrase == Game.Phrase.TheHeist and game.roles[1][0] == MDGlobal.player_map[user_id]:
        try:
            game.phrase3_continue(MDGlobal.card_name.index(args[1]))
        except MDError as e:
            session.send(e.message)
    if args[0] == "pay":
        pl1 = MDGlobal.player_map[user_id]
        r_id = args[1]["target"]
        pl2 = MDGlobal.player_map[r_id]
        amount = int(args[2])
        pay_value = pl1.minus_balance(amount)
        pl2.add_balance(pay_value)
        m = Message()
        m.appendAt(user_id)
        m.appendPlain("向")
        m.appendAt(r_id)
        m.appendPlain("汇款{pay_value}00万美金")
        m.send()