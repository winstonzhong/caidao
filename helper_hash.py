'''
Created on 2022年10月1日

@author: lenovo
'''
import datetime
import hashlib
import json

import pandas

from tool_env import is_number


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            # print("MyEncoder-datetime.datetime:", obj, pandas.isnull(obj))
            return obj.strftime("%Y-%m-%d %H:%M:%S") if not pandas.isnull(obj) else None
        if isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        if isinstance(obj, float):
            return float(obj)
        if is_number(obj):
            return int(obj)
        else:
            return super(MyEncoder, self).default(obj)

def get_hash_bytes(b):
    return hashlib.sha256(b).hexdigest()

def get_hash(txt):
    return get_hash_bytes(txt.encode())
    # return hashlib.sha256(txt.encode()).hexdigest()

def get_hash_img(img):
    return hashlib.sha256(img.tobytes()).hexdigest()

def get_hash_df(df):
    return get_hash_jsonable(df.to_dict('records'))

def get_hash_dict(d, exclude_filter=None):
    keys = d.keys() if exclude_filter is None else filter(exclude_filter, d.keys()) 
    keys = list(keys)
    keys.sort()
    txt = ' '.join([f'{k}={d.get(k)}' for k in keys])
    # print(txt)
    return get_hash(txt)

def get_hash_jsonable(l):
    return hashlib.sha256(json.dumps(l,cls=MyEncoder).encode('utf8')).hexdigest() if l else None
