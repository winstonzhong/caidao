'''
Created on 2022年3月20日

@author: Administrator
'''
# import ssl
import random
import sys
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from agent import pick_one_agent



disable_warnings(InsecureRequestWarning)
cookies = []

# ssl._create_default_https_context = ssl._create_unverified_context


class UrlOpenError(Exception):
    pass


def retry(attempt, fix_short_timeout=False):
    def decorator(func):
        def retryit(att, e):
            print("timeout, retrying %s..." % func.__name__, att)
            att += 1
            if att >= attempt:
                raise e.with_traceback(sys.exc_info()[2])
            if not fix_short_timeout:
                time.sleep(random.randint(1, 3) + att)
            else:
                time.sleep(0.1)
            return att

        def wrapper(*args, **kw):
            att = 0
            while att < attempt:
                try:
                    return func(*args, **kw)
#                 except HTTPError as e:
                except Exception as e:
                    # except UrlOpenError as e:
                    att = retryit(att, e)

        return wrapper
    return decorator

@retry(3, True)
def rget(*a, **k):
    return requests.get(*a, **k)

@retry(3, True)
def rpost(*a, **k):
    r = requests.post(*a, **k)
    if r.status_code == 200:
        return r
    raise ValueError(r.content)

def with_random_agent_simple(*args, **kw):
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=10))
    s.mount('https://', HTTPAdapter(max_retries=10))

    headers = {'user-agent': pick_one_agent()}

    if kw.get('cookie') is not None:
        headers['cookie'] = kw.pop('cookie')

    kw.setdefault('headers', {}).update(headers)
    kw['timeout'] = (20, 20) if 'timeout' not in kw else kw['timeout']

    kw['verify'] = False
    return s, args, kw

def post_with_random_agent_simple(*args, **kw):
    s, args, kw = with_random_agent_simple(*args, **kw)
    return s.post(*args, **kw)

def get_with_random_agent_simple(*args, **kw):
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=10))
    s.mount('https://', HTTPAdapter(max_retries=10))

    headers = {'user-agent': pick_one_agent()}

    if kw.get('cookie') is not None:
        headers['cookie'] = kw.pop('cookie')

    kw.setdefault('headers', {}).update(headers)
    kw['timeout'] = (20, 20) if 'timeout' not in kw else kw['timeout']

    kw['verify'] = False

    return s.get(*args, **kw)


def get_cookies(*args, **kw):
    r = get_with_random_agent_simple(*args, **kw)
    if r.status_code == 200 and r.cookies:
        return ';'.join([k + '=' + v for k, v in r.cookies.items()])


@retry(5)
def get_with_random_agent(*args, **kw):
    if kw.get('empty_not_allowed'):
        empty_not_allowed = True
        kw.pop('empty_not_allowed')
    else:
        empty_not_allowed = False

    r = get_with_random_agent_simple(*args, **kw)

    if r.status_code == 200:
        if not empty_not_allowed or r.content:
            return r

    raise UrlOpenError("HTTP ERROR:%s, %s" % (r.status_code, args[0]))


