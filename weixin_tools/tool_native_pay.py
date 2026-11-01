"""
微信支付 API v2 Native 支付高层封装（基于 helper_native_pay 的原语）。

- create_native_order：统一下单，拿 code_url（顾客扫码）
- verify_notify_xml：支付结果回调验签

>>> import requests
>>> from unittest import mock
>>> _ok_xml = (
...     '<xml><return_code><![CDATA[SUCCESS]]></return_code>'
...     '<result_code><![CDATA[SUCCESS]]></result_code>'
...     '<code_url><![CDATA[weixin://wxpay/biz/test123]]></code_url></xml>')
>>> with mock.patch.object(requests, 'post', return_value=mock.Mock(content=_ok_xml.encode('utf-8'))):
...     r = create_native_order(appid='appid1', mch_id='mch1', apiv2_key='key1',
...                             notify_url='https://x/notify', body='金立方-服务',
...                             out_trade_no='T1', total_fee=100,
...                             spbill_create_ip='127.0.0.1', trade_type='NATIVE')
>>> r['code_url']
'weixin://wxpay/biz/test123'

>>> _fail_xml = (
...     '<xml><return_code><![CDATA[SUCCESS]]></return_code>'
...     '<result_code><![CDATA[FAIL]]></result_code>'
...     '<err_code_des><![CDATA[余额不足]]></err_code_des></xml>')
>>> with mock.patch.object(requests, 'post', return_value=mock.Mock(content=_fail_xml.encode('utf-8'))):
...     create_native_order(appid='a', mch_id='m', apiv2_key='k',
...                         notify_url='https://x', body='b', out_trade_no='o',
...                         total_fee=1, spbill_create_ip='127.0.0.1', trade_type='NATIVE')
Traceback (most recent call last):
...
ValueError: 微信下单失败: 余额不足

>>> _notify = {
...     'appid': 'appid1', 'mch_id': 'mch1', 'nonce_str': 'n1',
...     'return_code': 'SUCCESS', 'result_code': 'SUCCESS', 'openid': 'ox1', 'out_trade_no': 'T1',
...     'total_fee': '100', 'transaction_id': 'wx1',
... }
>>> _notify['sign'] = generate_wechat_pay_sign(_notify, 'key1')
>>> import weixin_tools.helper_native_pay as _h
>>> _notify_xml = _h.dict_to_xml(_notify)
>>> _r = verify_notify_xml(_notify_xml, 'key1')
>>> _r['out_trade_no'], _r['openid']
('T1', 'ox1')

>>> _notify['sign'] = 'BAD_SIGN'
>>> verify_notify_xml(_h.dict_to_xml(_notify), 'key1')
Traceback (most recent call last):
...
ValueError: 微信支付回调验签失败
"""

import random
import string
import time

import requests

from weixin_tools.helper_native_pay import (
    dict_to_xml,
    generate_wechat_pay_sign,
    xml_to_dict,
)

UNIFIEDORDER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"


def _nonce_str(length=32):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _check_response(data, action):
    """检查 v2 响应的 return_code / result_code，失败抛 ValueError。"""
    if not isinstance(data, dict) or data.get("status") == "fail":
        raise ValueError(f"微信{action}失败: 响应解析失败 {data}")
    if data.get("return_code") != "SUCCESS":
        raise ValueError(f"微信{action}失败: {data.get('return_msg', '')}")
    if data.get("result_code") != "SUCCESS":
        raise ValueError(f"微信{action}失败: {data.get('err_code_des', data.get('err_code', ''))}")
    return data


def create_native_order(*, appid, mch_id, apiv2_key, notify_url, body,
                        out_trade_no, total_fee, spbill_create_ip, trade_type="NATIVE"):
    """
    微信 Native 统一下单。返回响应字典（含 code_url）。
    失败抛 ValueError（消息来自微信响应）。
    """
    params = {
        "appid": appid,
        "mch_id": mch_id,
        "nonce_str": _nonce_str(),
        "body": body,
        "out_trade_no": out_trade_no,
        "total_fee": total_fee,
        "spbill_create_ip": spbill_create_ip,
        "notify_url": notify_url,
        "trade_type": trade_type,
    }
    params["sign"] = generate_wechat_pay_sign(params, apiv2_key)

    resp = requests.post(UNIFIEDORDER_URL, data=dict_to_xml(params).encode("utf-8"))
    data = xml_to_dict(resp.content)
    _check_response(data, "下单")
    return data


def verify_notify_xml(xml_bytes, apiv2_key):
    """
    校验微信支付结果回调的签名与状态。返回回调参数字典（含 out_trade_no/openid）。
    验签失败或支付未成功抛 ValueError。
    """
    data = xml_to_dict(xml_bytes)
    if not isinstance(data, dict) or data.get("status") == "fail":
        raise ValueError("微信支付回调验签失败: 响应解析失败")

    sign = data.get("sign")
    if not sign or generate_wechat_pay_sign(data, apiv2_key) != str(sign).upper():
        raise ValueError("微信支付回调验签失败")

    _check_response(data, "支付")
    return data


if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))
