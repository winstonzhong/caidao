'''
Created on 2023年4月27日

@author: lenovo
'''

from pyquery.pyquery import PyQuery

from helper_net import rget, rpost, post_with_random_agent_simple
from tool_env import remain_chinese, split_by_not_chinese


url_trans = 'https://dict.youdao.com/result'

url_baidu = 'https://fanyi.baidu.com/v2transapi?from=zh&to=en'


# https://dict.youdao.com/suggest?num=1&ver=3.0&doctype=json&cache=false&le=en&q=manticore
url_trans_short = 'https://dict.youdao.com/suggest?num=1&ver=3.0&doctype=json&cache=false&le=en&q=%s'

def translate_short(en):
    url = 'https://dict.youdao.com/suggest?num=1&ver=3.0&doctype=json&cache=false&le=en&q=%s'
    r = rget(url % en)
    return r.json()

def translate_short_clean(en):
    j = translate_short(en)
    cn = j.get('data').get('entries',[{}])[0].get('explain','')
    return ' '.join(set(split_by_not_chinese(cn)))
    

def translate_q(text, lang='en'):
    payload = {
        "word": text[:14000],
        "lang":lang,
    }
     
    r = rget(url_trans, params=payload)
    
    html = r.content
    
    return PyQuery(html.decode('utf8'))

def translate_safe(text, lang='en'):
    d = translate_q(text, lang)
    return d('p.trans-content').text() or \
        d('div.trans-container ul.basic div.word-exp').text() or \
        PyQuery(d('div.trans-container ul.trans-list p')[0:1]).text() or \
        d('div.trans-container ul.basic span').text()
 

def translate(text, lang='en'):
    payload = {
        "word": text[:14000],
        "lang":lang,
    }
     
    r = rget(url_trans, params=payload)
    
    # print(r.status_code)
    
    html = r.content
    
    # with open('d:/temp/test.html', 'wb') as fp:
    #     fp.write(html)
    
    # print(html)
    
    # return html
    
    d = PyQuery(html.decode('utf8'))
    
    # return d
    
    return d('p.trans-content').text() or d('div.trans-container ul.basic div.word-exp').text()

cookie = '''BIDUPSID=CF0BC2907443106ED99F834F82DCFD7B; PSTM=1678066256; BAIDUID=CF0BC2907443106E02C641D1F4B8DDE3:FG=1; BAIDUID_BFESS=CF0BC2907443106E02C641D1F4B8DDE3:FG=1; ZFY=CRkiKCnqKKqGDgCkA6o3rXM0j1NyPNPNRT0mstyN6q4:C; __bid_n=18798aed8d1e9c77a14207; newlogin=1; BDUSS=dtN0gwMjNhazBsWGxDMH5nR340ZUpGTldsd0Z3WVU1eDZ3c2ZCa210TUtUSHRrSUFBQUFBJCQAAAAAAAAAAAEAAAB2ZbsLofS98LDxxvDD-834ofQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAq~U2QKv1NkNG; BDUSS_BFESS=dtN0gwMjNhazBsWGxDMH5nR340ZUpGTldsd0Z3WVU1eDZ3c2ZCa210TUtUSHRrSUFBQUFBJCQAAAAAAAAAAAEAAAB2ZbsLofS98LDxxvDD-834ofQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAq~U2QKv1NkNG; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221695496292%22%2C%22first_id%22%3A%22187e722c36f4ac-09823df4d72cb5-26021a51-2073600-187e722c3702be%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%22187e722c36f4ac-09823df4d72cb5-26021a51-2073600-187e722c3702be%22%7D; ZD_ENTRY=bing; FPTOKEN=AnK6pqP/KxJY7EWiDzY0c62/3u5zzsFrcbdzGdwYDkGkRvDg87EKUScSbY7pt4J2oGUXV2YYHKEQ4PRUuYeXt3vnz8PS8SK7MLAuqdnkDAYrW71OzDWkyVG4Iv++C+q9rhwUxsUAiz+fl+CQdRMS6lx7vh1fPmC8QBVIykZ4QNswREa/Y6+HrY+PWgM+/brHs+5wykIMTHYv+VDVWkzSvHOc5dJR5W8C7oAnvO4JkYBChIJPTFdy/Pw1f4rIYLZX/U7rNYpUeaqmqM86saOBWb7FNKSCdO8q2IEx03uFMFSkpceCzcunUHjOMp2ij3LPXJlRQf6Re1UGpjj1y7McRcAA62AOqFRxfJUI4j7nRxcPShG84TImHQyTbZa5WH0XF0V/80da0K3vBq3xrZwLzA==|k+fSc5SJaXw5atRjOeKu3wOkA9JhgjR3Ku/mwm+D9qI=|10|bfbaa5639e7492a972d0272381b0d7dc; BCLID=7390148840133701608; BCLID_BFESS=7390148840133701608; BDSFRCVID=mnAOJeCAa7eBi-RfomF5-hKJ2gKK0gOTH6Hh_z2uPO2iCZIVt1y4EG0Pqf8g0KubbSsPogKKXgOTHw0F_2uxOjjg8UtVJeC6EG0Ptf8g0M5; BDSFRCVID_BFESS=mnAOJeCAa7eBi-RfomF5-hKJ2gKK0gOTH6Hh_z2uPO2iCZIVt1y4EG0Pqf8g0KubbSsPogKKXgOTHw0F_2uxOjjg8UtVJeC6EG0Ptf8g0M5; H_BDCLCKID_SF=tbueoCtaJI-3fP36qRQEM-_HbU7taRc0aDkX3b7EfMcR_p7_bf--Dx_8XUnA2-5yQj7CsRncWDomHq7e0h5xy5KmhxTCq6FqMg7DKxJtJhvahCQHQT3mM-5bbN3i34jmKm3fWb3cWMnJ8UbS5T3PBTD02-nBat-OQ6npaJ5nJq5nhMJmb67JD-50eG-qt5FjJbKOV-35b5ubhbcPq4bohjPh3-j9BtQmJJrOKDTa-JOtDUQHMKcsyUTXbUbW0boXQg-qMbra5Rvj8ncyLPPB-tIw3tLL0x-jLNTPVn0MW-5YqJo33-nJyUPRbPnnBn-j3H8HL4nv2JcJbM5m3x6qLTKkQN3T-PKO5bRh_CF-JILBMDLwDjR0M-FO-fPX5to05TIX3b7Efb6_Eq7_bfbN-j-8LxuLQt5yamFtsRncWDoJOpkxbUnxy5KnMbnEJJQTBbr05McYQt-aJDbHQT3mKt5bbN3i-4jaL57TWb3cWMnJ8UbS5T3PBTD02-nBat-OQ6npaJ5nJq5nhMJmb67JDMr0exbH55uHfnFHof5; H_BDCLCKID_SF_BFESS=tbueoCtaJI-3fP36qRQEM-_HbU7taRc0aDkX3b7EfMcR_p7_bf--Dx_8XUnA2-5yQj7CsRncWDomHq7e0h5xy5KmhxTCq6FqMg7DKxJtJhvahCQHQT3mM-5bbN3i34jmKm3fWb3cWMnJ8UbS5T3PBTD02-nBat-OQ6npaJ5nJq5nhMJmb67JD-50eG-qt5FjJbKOV-35b5ubhbcPq4bohjPh3-j9BtQmJJrOKDTa-JOtDUQHMKcsyUTXbUbW0boXQg-qMbra5Rvj8ncyLPPB-tIw3tLL0x-jLNTPVn0MW-5YqJo33-nJyUPRbPnnBn-j3H8HL4nv2JcJbM5m3x6qLTKkQN3T-PKO5bRh_CF-JILBMDLwDjR0M-FO-fPX5to05TIX3b7Efb6_Eq7_bfbN-j-8LxuLQt5yamFtsRncWDoJOpkxbUnxy5KnMbnEJJQTBbr05McYQt-aJDbHQT3mKt5bbN3i-4jaL57TWb3cWMnJ8UbS5T3PBTD02-nBat-OQ6npaJ5nJq5nhMJmb67JDMr0exbH55uHfnFHof5; H_PS_PSSID=38516_36561_38529_38469_38468_38591_38597_38577_38414_26350_38568_38545; BA_HECTOR=058l8gag0ha405200ga42k2s1i5scmb1m; Hm_lvt_64ecd82404c51e03dc91cb9e8c025574=1683894993; APPGUIDE_10_0_2=1; REALTIME_TRANS_SWITCH=1; FANYI_WORD_SWITCH=1; HISTORY_SWITCH=1; SOUND_SPD_SWITCH=1; SOUND_PREFER_SWITCH=1; Hm_lpvt_64ecd82404c51e03dc91cb9e8c025574=1683895331; ab_sr=1.0.1_MzE5YjM3NDY4NzAyZWUyNmJhNDg1YTNjMTViNGE0YzEzYTdlOTNmNzc0YzBkNDU4ODMyNWE2MjI2ZjIwODY3ZGUxM2YxNTMwZjZkYTM5NTZmYzE4ZDQ1MDRlODQ0MmRhOWJmY2I3YjdjNGU4NWUzNWUxNTA2ZjlkZDhlZTJmNzk3OWYwOGY1NDczNjA0NzM5OTI3YzE3NDViZDhhOTg4YTYwODFiNGExMjEzMWVjYjE4NDVkMzY3NGRkOTZkMTMx'''

def translate_baidu(text):
    payload = {
        'query': text,
        'token': '03a2509f883bedfbe3de1fbf8e6a700b',
        }
    
    return post_with_random_agent_simple(url_baidu, json=payload, cookie=cookie)