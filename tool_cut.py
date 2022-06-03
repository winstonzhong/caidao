'''
Created on 2022年6月3日

@author: Administrator
'''
import os

import jieba


FPATH_STOP_WORDS = os.path.join(os.path.dirname(__file__), 'cn_stopwords.txt')


def get_stop_words():
    with open(FPATH_STOP_WORDS, 'r', encoding='utf8') as fp:
        return [x.strip() for x in fp.readlines()]


STOP_WORDS = get_stop_words()

def get_words(txt):
    if txt:
        l = jieba.cut(txt)
        rtn = []
        for x in l:
            x = x.strip()
            if x and x not in STOP_WORDS:
                rtn.append(x)
        return rtn
        # return [x.strip() for x in l if x.strip() not in STOP_WORDS]
        # return filter(lambda x: x.strip() and x not in STOP_WORDS, l)
        
def get_line_for_train(txt):
    if txt:
        return ' '.join(get_words(txt))
