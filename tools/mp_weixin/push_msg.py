import datetime
import requests
import json


def fetch_mp_weixin_access_token(app_id, secret):
    """获取小程序access_token"""
    url = 'https://api.weixin.qq.com/cgi-bin/stable_token'
    data = {
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": secret
    }
    return requests.post(url, json=data).json()['access_token']


def send_subscribe_message(access_token, data):
    '''
    发送订阅消息(小程序)
    :param data:  消息体。字典类型
    :param accessToken:  接入token
    :return:
    '''
    url = 'https://api.weixin.qq.com/cgi-bin/message/subscribe/send'
    data = json.dumps(data)
    params = {'access_token': access_token}
    r = requests.post(url, data=data, params=params)
    return r.json()


def push(app_id, secret, open_id):
    """推送订阅消息示例"""
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    now = now.strftime('%Y-%m-%d %H:%M:%S')
    access_token = fetch_mp_weixin_access_token(app_id, secret)
    data = {
        'touser': open_id,
        'template_id': 'OBb2mcqltiwq1f_LDGTmaN_jpEKozQlbWxx4LOg6OhY',
        'page': '/pages/user/index-mp-weixin',
        'data': {'thing1': {'value': '图片制作完成'}, 'thing3': {'value': '点击查看结果'}, 'time4': {'value': now}},
        'miniprogram_state': "trial"
    }
    send_subscribe_message(access_token, data)

