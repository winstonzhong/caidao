import requests


APP_ID = '11'
SECRET = '22'


def fetch_mp_weixin_access_token(app_id, secret):
    """获取小程序access token"""
    url = 'https://api.weixin.qq.com/cgi-bin/stable_token'
    data = {
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": secret
    }
    return requests.post(url, json=data).json()['access_token']


def send_msg(to_user_open_id, content):
    access_token = fetch_mp_weixin_access_token(APP_ID, SECRET)
    print('access_token', access_token)

    data = {
        'touser': to_user_open_id,
        'msgtype': 'text',
        'text': {
            'content': content
        }

    }
    url = f'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}'
    respdata = requests.post(url, json=data).json()
    print('respdata', respdata)


if __name__ == '__main__':
    open_id = 'o-THh5De90Rdk0YNg_FLvg_KR-6U'
    content = 'text'
    send_msg(open_id, content)