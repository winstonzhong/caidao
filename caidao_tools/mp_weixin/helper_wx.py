import base64
import json

from Crypto.Cipher import AES
import requests


def get_login_info(js_code, app_id, app_secret):
    """返回数据结构: {'session_key': 'xxx', 'openid': 'xxx'}"""
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    params = {'appid': app_id, 'secret': app_secret, 'js_code': js_code, 'grant_type': 'authorization_code'}
    r = requests.get(url=url, params=params)
    r = r.json()
    # print('r', r)
    return r


def decrypt_callback(resource, api_v3_key):
    """微信回调信息解密

    原信息
    callback_data = {
        'id': '0587679c-5648-5e15-a622-07382a2cf195',
        'create_time': '2025-10-20T11:23:21+08:00',
        'resource_type': 'encrypt-resource',
        'event_type': 'TRANSACTION.SUCCESS',
        'summary': '支付成功',
        'resource': {
            'original_type': 'transaction',
            'algorithm': 'AEAD_AES_256_GCM',
            'ciphertext': 'dzc0KWF0iRvuTMaAQ80MWlVc3qdm2yXnPjWkkwbCNCa6TvyNgPbl6HAlZEuHZ0/BQznwH5ck4jq6Z+7I5tzg1DHa1YK4qE0PQsY+ZWn3NK0mjNYY709vlIyjaItLWEXl+AfAwyR0UYxS7NKARZJxaktAZlNk0TF9Yb5IPJEWNcOqdJOFT4FKnEXv3IhmlzH+ty/KwVBsCY7fcSYyPqQSTGcBIYckX5L1AdxdUWMITVgHXsBpSPp1wtjvUnXuge1tU45QOf3tijpMWeiY5ShZgxKbq4jNOeTxy96vAQdyEOxXcmqUDOVh2o6tdHsNy4aP8eEctwoQYOxTjKp2ORFm29u31wBWYeaZAN8hddpx24C2I7lqwuM0K9SwfkARFochZ+vG+RYa9vHVyCR25HAxyWmlXxpx1xCCsGO5OisIrsj56JT9Du6yfgwuSha9NXIbiN5aNXMBN4kZm3Wd9Z1vYrIJc+nONGRYhRJ7d1QW0Y/aZ/k0LVwUIje9M+wk1l8iva7Aw/Fd1DYqwBHluR5Pvs2cEoGUNZFNPt21eh357YYj1cibRrzaXu9nFSJEsEnueUO9sCrfW2K44QByiinR',
            'associated_data': 'transaction',
            'nonce': '5BMq7e2YHc4o'
        }
    }

    解密后信息:
    {
      "mchid": "1639127792",
      "appid": "wx074ce80c1ccb866d",
      "out_trade_no": "82819943493218851122763219198173",
      "transaction_id": "4200002894202510204855371005",
      "trade_type": "JSAPI",
      "trade_state": "SUCCESS",
      "trade_state_desc": "支付成功",
      "bank_type": "OTHERS",
      "attach": "",
      "success_time": "2025-10-20T11:23:21+08:00",
      "payer": {
        "openid": "orRSd56HefLUut_ia-xwXGlmCH68"
      },
      "amount": {
        "total": 1,
        "payer_total": 1,
        "currency": "CNY",
        "payer_currency": "CNY"
      }
    }

    """
    # 提取参数
    print('resource', [resource])
    ciphertext = resource['ciphertext']
    nonce = resource['nonce']
    associated_data = resource['associated_data']

    # 转换为字节
    key = api_v3_key.encode('utf-8')
    nonce_bytes = nonce.encode('utf-8')
    associated_data_bytes = associated_data.encode('utf-8')

    # 1. Base64解码 ciphertext，得到 密文+标签 的字节流
    ciphertext_bytes = base64.b64decode(ciphertext)

    # 2. 分离密文和标签（AES-GCM 标签固定为16字节）
    tag = ciphertext_bytes[-16:]  # 最后16字节是标签
    ciphertext_only = ciphertext_bytes[:-16]  # 前面的是实际密文

    # 3. AES-GCM解密（需传入标签验证）
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce_bytes)
    cipher.update(associated_data_bytes)  # 关联数据
    plaintext = cipher.decrypt_and_verify(ciphertext_only, tag)  # 同时解密和验证标签

    # 转换为JSON字典
    return json.loads(plaintext.decode('utf-8'))


