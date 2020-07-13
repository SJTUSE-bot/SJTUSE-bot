import random
from nonebot import get_bot, on_command, CommandSession
from math import floor


def at(qq_id):
    return f"[CQ:at,qq={ qq_id }]"


class MDError(Exception):
    def __init__(self, message):
        self.message = message


class Loot:
    def __init__(self, role, ante, loot):
        self.role = role
        self.ante = ante
        self.loot = loot


class MDGlobal:
    bot = get_bot()
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

    async def remove_player(self, user_id):
        for i in range(len(self.players)):
            if self.players[i].qq_id == user_id:
                await MDGlobal.bot.send_group_msg(group_id=self.group_id, message=f"{ at(self.players[i].qq_id) }退出成功")
                self.players[i].destruct()
                del self.players[i]
                return
        await MDGlobal.bot.send_group_msg(group_id=self.group_id, message=f"未找到{at(user_id)}")

    def try_end_game(self):
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
            return f"游戏结束！玩家{ at(max_player.qq_id) }胜利！\n如果需要再次开始游戏，请输入.md start"
        return ""

    async def start_game(self):
        if not 4 <= len(self.players) <= 8:
            await MDGlobal.bot.send_group_msg(group_id=self.group_id, message=f"目前体验版只支持 4 到 8 人游玩。\n当前玩家人数为 { len(self.players) } 人，无法开始游戏")
            return
        self.status = Game.Status.Running
        await self.do_phrase()

    async def show_balance(self):
        msg_list = []
        for player in self.players:
            msg_list.append(f"{ at(player.qq_id) }：{player.balance}00万美金，威胁卡数量：{player.intimidation}")
        await MDGlobal.bot.send_group_msg(group_id=self.group_id, message="当前财产状况：\n" + '\n'.join(msg_list))

    async def do_phrase(self):
        if self.phrase == Game.Phrase.Planning:
            self.loot_players = {}
            self.loot = MDGlobal.loot_list[self.loot_index]
            self.loot_index += 1
            if self.loot.role != 0:
                msg = f"谋划阶段：第{ self.loot_index }轮\n当前银行战利品为{ self.loot.loot }00万美金，保证金{ self.loot.ante }00万美金，加成角色为{ MDGlobal.card_name[self.loot.role ]}\n"
            else:
                msg = f"谋划阶段：第{self.loot_index}轮\n当前银行战利品为{self.loot.loot}00万美金，保证金{self.loot.ante}00万美金\n"
            for player in self.players:
                player.role = Player.Role.TBD
                player.exit = False
                self.ante[player.qq_id] = player.minus_balance(self.loot.ante)
                msg += f'玩家{ at(player.qq_id) }已缴纳保证金{ self.ante[player.qq_id] }00万美金\n'
            await MDGlobal.bot.send_group_msg(group_id=self.group_id,
                                              message=msg + "\n请玩家私聊 bot 输入 .md [角色名] 决定本回合要扮演的角色")
        elif self.phrase == Game.Phrase.Negotiation:
            random.shuffle(self.players)
            msg = "谈判阶段：\n目前已知晓的玩家身份有："
            for i in range(1, len(self.players)):
                msg += f'{ MDGlobal.card_name[self.players[i].role] }、'
            await MDGlobal.bot.send_group_msg(group_id=self.group_id, message=msg[:-1])
        elif self.phrase == Game.Phrase.TheHeist:
            self.roles = [[], [], [], [], [], []]
            for player in self.players:
                if not player.exit:
                    self.roles[player.role].append(player)
            snitches = self.roles[1]
            if len(snitches) == 0:
                await MDGlobal.bot.send_group_msg(group_id=self.group_id, message="无告密者，继续下一阶段")
                await self.phrase3_continue(0)
            elif len(snitches) == 1:
                msg = f"告密者为{ at(snitches[0].qq_id) }，请告密者输入 .md rm [角色种类] 决定要移除的角色"
                self.loot_players[Player.Role.Snitch] = snitches[0]
                await MDGlobal.bot.send_group_msg(group_id=self.group_id, message=msg)
            else:
                msg = "告密者为"
                for player in snitches:
                    msg += at(player.qq_id) + "、"
                msg = msg[:-1] + '\n所有告密者将被淘汰，并无法取回保证金'
                await MDGlobal.bot.send_group_msg(group_id=self.group_id, message=msg)
                await self.phrase3_continue(0)

    async def phrase3_continue(self, role):
        if role != 0:
            flag = False
            for i in range(1, len(self.players)):
                if self.players[i].role == role:
                    flag = True
                    break
            if not flag:
                raise MDError("告密者只能选择场上出现过的角色")
        msg = ""
        for i in range(2, 6):
            arr = self.roles[i]
            arr_list = []
            for p in arr:
                arr_list.append(at(p.qq_id))
            arr_str = '、'.join(arr_list)
            if i == role:
                if i == Player.Role.Brute:
                    msg += f"暴徒已被告密者移除，但暴徒们（{ arr_str }）取回了自己的保证金\n"
                    for p in arr:
                        p.add_balance(self.ante[p.qq_id])
                else:
                    msg += f"{MDGlobal.card_name[i]}们（{ arr_str }）已被告密者移除\n"
                continue

            if len(arr) == 0:
                msg += f"无{MDGlobal.card_name[i]}\n"
                continue
            elif len(arr) == 1:
                msg += f"{MDGlobal.card_name[i]}人选已确定：{arr_str}\n"
                self.loot_players[i] = arr[0]
                continue
            else:
                if i == Player.Role.Brute:
                    msg += f"暴徒们（{arr_str}）因数量太多被移除了，但暴徒们取回了自己的保证金\n"
                    for p in arr:
                        p.add_balance(self.ante[p.qq_id])
                else:
                    msg += f"{MDGlobal.card_name[i]}们（{arr_str}）数量太多，被全部移除了\n"
                continue
        if len(self.loot_players) == 1 and Player.Role.Snitch in self.loot_players:
            msg += f"最后的队伍只剩下告密者。告密者亏损了300万美金！"
            self.loot_players[Player.Role.Snitch].minus_balance(3)
            await MDGlobal.bot.send_group_msg(group_id=self.group_id, message=msg)
        else:
            msg += f"共有{len(self.loot_players)}名玩家行动成功！\n"
            money = self.loot.loot
            if Player.Role.MasterMind in self.loot_players:
                money += 2
                msg += "因为队伍里存在谋士，因此战利品增加了200万美金！\n"
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
            msg += "最终收获如下：\n"
            msg_list = []
            for r in d:
                if self.loot.role == r:
                    d[r] += 1
                msg_list.append(f"{MDGlobal.card_name[r]}：{d[r]}00万美金" + ("、1张威胁卡" if r == Player.Role.Brute else ""))
                self.loot_players[r].add_balance(
                    d[r] + self.ante[self.loot_players[r].qq_id])
            msg += '\n'.join(msg_list)
            await MDGlobal.bot.send_group_msg(group_id=self.group_id, message=msg)
        await self.show_balance()
        msg = self.try_end_game()
        if msg == "":
            self.phrase = Game.Phrase.Planning
            await self.do_phrase()
        else:
            await MDGlobal.bot.send_group_msg(group_id=self.group_id, message=msg)

    async def try_next(self):
        for player in self.players:
            if player.role == 0:
                return
        self.phrase = Game.Phrase.Negotiation
        await self.do_phrase()


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


@on_command('million_dollars', aliases=['md', '00万美金'], only_to_me=False)
async def million_dollars(session: CommandSession):
    args = session.state['args']
    user_id = session.ctx['sender']['user_id']
    if 'group_id' in session.ctx:
        group_id = session.ctx['group_id']
    else:
        group_id = 0
    if args[0] == "new" and group_id != 0:
        Game(group_id)
        await session.send(f"群{group_id}的游戏已创建")
        return
    game = (None if group_id not in MDGlobal.group_map else MDGlobal.group_map[group_id]) or \
           (None if user_id not in MDGlobal.player_map else MDGlobal.player_map[user_id].game)
    if game is None:
        await session.send("本群还未创建游戏，请输入 .md new 创建")
        return

    if args[0] == "dismiss":
        game.destruct()
        await session.send("游戏已解散")
        return
    if args[0] == "join":
        game.add_player(user_id)
        await session.send(f"{at(user_id)}已加入")
        return
    if args[0] == "leave":
        await game.remove_player(user_id)
        return
    if args[0] == "start":
        await game.start_game()
        # await session.send("游戏开始")
        return

    if game.status == Game.Status.Pending:
        await session.send("游戏未开始。若准备完毕，请使用 .md start 开始")
        return

    if args[0] in ["告密者", "暴徒", "恶棍", "司机", "谋士"]:
        if game.phrase == Game.Phrase.Planning and MDGlobal.player_map[user_id].role == 0:
            MDGlobal.player_map[user_id].role = MDGlobal.card_name.index(args[0])
        await session.send(f"你已选择{args[0]}角色")
        await game.try_next()
        return

    if args[0] == "st":
        await game.show_balance()
        return
    if args[0] == "see" and game.phrase == Game.Phrase.Negotiation and MDGlobal.player_map[user_id].intimidation > 0:
        r_id = int(args[1][10:-1])
        pl2 = MDGlobal.player_map[r_id]
        MDGlobal.player_map[user_id].intimidation -= 1
        await MDGlobal.bot.send_private_msg(user_id=user_id, message=f"{ r_id }的身份是{ MDGlobal.card_name[pl2.role]}")
    if args[0] == "exit" and game.phrase == Game.Phrase.Negotiation:
        MDGlobal.player_map[user_id].exit = True
        MDGlobal.player_map[user_id].add_balance(game.ante[user_id])
        await session.send(f"{ at(user_id)}已退出")
    if args[0] == "en" and game.phrase == Game.Phrase.Negotiation:
        game.phrase = Game.Phrase.TheHeist
        await game.do_phrase()
    if args[0] == "rm" and game.phrase == Game.Phrase.TheHeist and game.roles[1][0] == MDGlobal.player_map[user_id]:
        try:
            await game.phrase3_continue(MDGlobal.card_name.index(args[1]))
        except MDError as e:
            await session.send(e.message)
    if args[0] == "pay":
        pl1 = MDGlobal.player_map[user_id]
        r_id = int(args[1][10:-1])
        pl2 = MDGlobal.player_map[r_id]
        amount = int(args[2])
        pay_value = pl1.minus_balance(amount)
        pl2.add_balance(pay_value)
        await session.send(f"{ at(user_id) }向{ at(r_id) }汇款{ pay_value }00万美金")


@million_dollars.args_parser
async def _(session: CommandSession):
    arr = session.current_arg.strip().split(' ')
    session.state['args'] = arr
