'''
Created on 2023年3月3日

@author: lenovo
'''


import os

from pathlib import Path

import sys

import pandas



BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / 'data'

if not os.path.lexists(DATA_DIR):
    os.mkdir(DATA_DIR)
    
FPATH_BIG_DATA = DATA_DIR / 'bigdata.csv'

FPATH_PL = DATA_DIR / 'pl_0303.csv'


pl_info = {
    'td':'2021-11-01',
}


def split_train_test(df):
    tmp = df[df.trade_date != pl_info.get('last_td')]
    df_train = tmp[tmp.trade_date <= pl_info.get('td')]
    df_test = tmp[tmp.trade_date > pl_info.get('td')]
    return df_train, df_test

def load_pl():
    df = pandas.read_csv(FPATH_PL, index_col='test_index')
    df.pl = df.pl.fillna(-0.1)

    pl_info['last_td'] = df.trade_date.drop_duplicates().sort_values().iloc[-1]
    
    pl_info['df'] = df
    
    df_train, df_test = split_train_test(df)
    
    pl_info['total_train'] = len(df_train.trade_date.drop_duplicates())
    pl_info['total_test'] = len(df_test.trade_date.drop_duplicates())
    

def get_pl_df():
    if pl_info.get('df') is None:
        load_pl()
    return pl_info.get('df')

def get_result(df, tag='train'):
    d = {}
    d['pl_%s' % tag] = df.pl.mean()
    d['atte_%s' % tag] = len(df) / pl_info.get("total_%s" % tag)
    return d

def compute(i):
    df = pl_info.get('df')
    
    df = df.loc[i]
    
    df = df[df.ting == 0]
    
    df = df.groupby('trade_date').first()
    
    df_train, df_test = split_train_test(df)
    
    d = get_result(df_train,'train')
    
    d.update(get_result(df_test,'test'))

    return d
