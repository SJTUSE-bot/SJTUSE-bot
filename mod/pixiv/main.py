import utils
import requests
import json


def OnMessage(msg):
    if msg['type'] == 'GroupMessage' and (2 <= len(msg['messageChain']) <= 3) and msg['messageChain'][1]['type'] == 'At' and msg['messageChain'][1]['target'] == utils.qqNumber:
        if len(msg['messageChain']) == 2 or (len(msg['messageChain']) == 3 and msg['messageChain'][2]['type'] == 'Plain'and msg['messageChain'][2]['text'] == ' '):
            group = msg['sender']['group']['id']
            r = json.loads(requests.get(
                'https://api.lolicon.app/setu/', params={
                    'apikey': '522605455f0c66a4a242d8',
                    'size1200': 'true',
                    'r18': 0,
                }).text)
            if r['code'] != 0:
                utils.Post('/sendImageMessage', {
                    'group': group,
                    "urls": [
                        r['data'][0]['url'],
                    ]
                })
                print('[pixiv] send')
