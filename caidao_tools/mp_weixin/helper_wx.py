import requests
from wechatpy import WeChatPay


def get_login_info(js_code, app_id, app_secret):
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    params = {'appid': app_id, 'secret': app_secret, 'js_code': js_code, 'grant_type': 'authorization_code'}
    r = requests.get(url=url, params=params)
    r = r.json()
    print('r', r)
    return r


def wx_prepay(open_id, price, out_trade_no, prepay_info, app_id, api_key, mch_id, notify_url):
    pay = WeChatPay(appid=app_id, api_key=api_key, mch_id=mch_id)
    order = pay.order.create(
        trade_type='JSAPI',
        user_id=open_id,
        notify_url=notify_url,
        total_fee=price,
        body=prepay_info,
        out_trade_no=out_trade_no
    )
    print(order)