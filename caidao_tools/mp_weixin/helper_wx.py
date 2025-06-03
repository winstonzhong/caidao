import requests


def get_login_info(js_code, app_id, app_secret):
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    params = {'appid': app_id, 'secret': app_secret, 'js_code': js_code, 'grant_type': 'authorization_code'}
    r = requests.get(url=url, params=params)
    r = r.json()
    print('r', r)
    return r
