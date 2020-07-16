# SJTUSE-bot
这原本是一个提醒LBOSS女装的QQ机器人。

## 部署环境
仅支持Linux，Windows请自行部署，网络问题自行处理

- Python>3.4
- java-8-openjdk（非必须）

```
pip3 install -r requirements.txt
```

插件依赖自行安装

## 部署
修改配置文件 `Mirai/plugins/MiraiAPIHTTP/setting.yml`

```
make
```

等待下载安装完成，自动启动Mirai(后续启动运行 `Mirai/miraiOK` )

```
login [qqnumber] [password]
```

新终端运行

```
python3 main.py [qqnumber]
```

出现 `Bot started` 即为运行成功

## 使用方法
```
Usage: bot.py [OPTIONS] QQ

Options:
  --news            Show news
  --host TEXT       Mirai HTTP host  [default: http://localhost:9500]
  --key TEXT        Mirai HTTP key  [default: sjtusebot1234]
  --target INTEGER  Target group by default, 0 for all  [default: 0]
  -h, --help        Show this message and exit.
```

## Mod 开发
### 目录格式

```
- mod
    - [modname]（插件目录）
        - __init__.py
        - main.py
```

### 引入新插件
在 `mod/__init__.py` 末尾添加

    import mod.[modname]

### 插件调用协定
**所有接口**均满足如下条件：

- **所有接口（伪）多线程执行，不保证任何调用顺序，不保证消息到达顺序，仅保证GIL锁，有状态服务请自行保证内部同步锁**
- 无接口调用超时时间，可以sleep
- 不同插件隔离，不支持相互通信（可自行实现，不建议）

### 插件接口
插件目录下 `__init__.py` 需满足如下格式

```
import bot
from . import main

config = {
    'name': 'modname',              # 模块名
    'enable': True,                 # 是否启用
    'entry': main.Entry,            # 入口函数，None为不处理
    'onGroupMsg': main.OnGroupMsg,  # 群聊消息处理函数，None为不处理
    'onUserMsg': None,              # 用户消息处理函数，None为不处理
}
bot.RegisterMod(config)

...(Your code)
```

其中 `entry` 函数将在bot上线后执行一次，`onGroupMsg` 将在收到任意群消息后触发一次，`onUserMsg` 将在收到任意用户消息后触发一次，如需进一步限制，请参考下文触发装饰器。

### 接口函数签名
```
def Entry():
def OnGroupMsg(msg, group, user):
def onUserMsg(msg, user):
```

### 触发装饰器
目前提供了如下几个装饰器，使用方法请阅读 `utils.py` 注释：

- `TriggerCmd`：指定文本前缀触发
- `TriggerAt`：指定 `@机器人` 前缀触发
- `TriggerAdmin`：管理员或群主发送消息触发

如有其他需要欢迎提交issue/PR

### 机器人操作API
请阅读 https://github.com/project-mirai/mirai-api-http

底层操作已经封装，`isSession` 为 `True` 时无需传入 `sessionKey` 参数，请求时会自动添加

- `utils.TryGet` / `utils.TryPost`：返回值错误时打印调试信息
- `utils.MustGet` / `utils.MustPost`：返回值错误时打印调试信息并退出当前线程

发送消息封装部分，请参考 `utils.Message`

### 其他封装函数
参考 `utils.py` 
