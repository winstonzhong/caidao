'''
Created on 2024年12月2日

@author: lenovo
'''
import json

import requests


def testit_ocr_url(file_url=r'000/test/00001.JPG'):
    url = 'http://192.168.0.100:8000/ocr/'
    data = {
        'url': file_url
        }
    # 发送 POST 请求
    response = requests.post(url, json=data)
    return response
    # 打印返回的数据
    d = response.json()
    return d
    # print(json.dumps(d, indent=3))