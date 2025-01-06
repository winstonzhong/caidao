'''
Created on 2024年12月2日

@author: lenovo
'''

import requests

from tool_static import 链接到相对路径


URL_API = 'http://192.168.0.100:8000/ocr/'

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
    
def url_2_ocr_json(url):
    return requests.post(URL_API, 
                  json={
                      'url': 链接到相对路径(url)
                      }).json()