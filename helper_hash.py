'''
Created on 2022年10月1日

@author: lenovo
'''
import datetime
import hashlib
import json

import numpy
import pandas


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            # print("MyEncoder-datetime.datetime:", obj, pandas.isnull(obj))
            return obj.strftime("%Y-%m-%d %H:%M:%S") if not pandas.isnull(obj) else None
        if isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        if isinstance(obj, int):
            return int(obj)
        
        if isinstance(obj, float):
            return float(obj)
        else:
            return super(MyEncoder, self).default(obj)

def get_hash_img(img):
    return hashlib.sha256(img.tobytes()).hexdigest()

def get_hash_df(df):
    return hashlib.sha256(json.dumps(df.to_dict('records'),cls=MyEncoder).encode('utf8')).hexdigest()
    # return hashlib.sha256(df.to_numpy().tobytes()).hexdigest() if df is not None else None


