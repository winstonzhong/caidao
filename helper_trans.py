'''
Created on 2023年4月27日

@author: lenovo
'''

from pyquery.pyquery import PyQuery

from helper_net import rget

url_trans = 'https://dict.youdao.com/result'

def translate(text, lang='en'):
    payload = {
        "word": text[:14000],
        "lang":lang,
    }
     
    r = rget(url_trans, params=payload)
    
    # print(r.status_code)
    
    html = r.content
    
    # return html
    
    d = PyQuery(html.decode('utf8'))
    
    # return d
    
    return d('p.trans-content').text() or d('div.trans-container ul.basic div.word-exp').text()