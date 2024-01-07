'''
Created on 2022年6月3日

@author: Administrator
'''
import os
import re

import jieba

from tool_env import has_chinese

ptn_digit = re.compile('\d+')

FPATH_STOP_WORDS = os.path.join(os.path.dirname(__file__), 'cn_stopwords.txt')


def get_stop_words():
    with open(FPATH_STOP_WORDS, 'r', encoding='utf8') as fp:
        return [x.strip() for x in fp.readlines()]


STOP_WORDS = get_stop_words()

def get_userdict_fpath(fname):
    return os.path.join(os.path.dirname(__file__), fname)

def get_words(txt):
    if txt:
        l = jieba.cut(txt)
        rtn = []
        for x in l:
            x = x.strip()
            if x and x not in STOP_WORDS:
                rtn.append(x)
        return rtn

def get_words_all(txt):
    for x in jieba.cut(txt or ''): 
        yield x 
    
def get_words_not_in_stopwords(txt):
    for x in get_words_all(txt):
        x = x.strip()
        if x and x not in STOP_WORDS:
            yield x

def get_words_not_in_stopwords_and_contains_chinese_or_digit(txt):
    for x in get_words_not_in_stopwords(txt):
        if has_chinese(x) or ptn_digit.search(x) is not None:
            yield x
            
def get_words_not_in_stopwords_and_contains_chinese_or_digit_and_at_least_2_characters(txt):
    for x in get_words_not_in_stopwords_and_contains_chinese_or_digit(txt):
        if len(x) >= 2:
            yield x              

        
def get_line_for_train(txt):
    if txt:
        return ' '.join(get_words(txt))
