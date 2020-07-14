import utils
import requests
import json


@CheckAt
def OnMessage(msg):
    try:
        group = msg['sender']['group']['id']
        user = msg['sender']['id']
        r = requests.get(
            'https://api.lolicon.app/setu/', params={
                'apikey': '522605455f0c66a4a242d8',
                'size1200': 'true',
                'r18': 0
            }, timeout=5)
        if r.status_code == 200:
            r = json.loads(r.text)
            if r['code'] == 0:
                url = r['data'][0]['url']
                r = utils.UploadURL(url, 'group', 10)
                if r != None:
                    utils.TryPost('/sendGroupMessage', {
                        'target': group,
                        'messageChain': [
                            {'type': 'At', 'target': user},
                            {'type': 'Plain', 'text': '你要的涩图：' + url},
                            {'type': 'Image', 'imageId': r['imageId']},
                        ]
                    })
                    print('[pixiv] send')
                    return
    except requests.exceptions.RequestException:
        pass
    utils.SendGroupPlain(group, '涩图暂不可用，多运动少冲！')
    print('[pixiv] send fail')
