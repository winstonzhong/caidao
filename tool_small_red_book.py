'''
Created on 2023年11月2日

@author: lenovo
'''
import json
import os

from pyquery.pyquery import PyQuery

from helper_net import get_with_random_agent


def get_all_dict(x):
    t = type(x)
    if t == dict:
        yield x
        for i in x.values():
            for j in get_all_dict(i):
                yield j
    elif t == list:
        for i in x:
            for j in get_all_dict(i):
                yield j


def get_dict_images(d):
    for x in get_all_dict(d):
        if x.get('imageScene') == 'CRD_WM_JPG':
            yield x

def get_dict_info(d):
    for x in get_all_dict(d):
        if x.get('type') and x.get('noteId') and x.get('time'):
            yield x
    

def get_note_json(url='https://www.xiaohongshu.com/explore/64c5ec88000000000b028d78'):
    r = get_with_random_agent(url)
    d = PyQuery(r.content)
    txt = d('script')[-1].text
    return eval(txt[len('window.__INITIAL_STATE__='):].replace('true','True').replace('false','False').replace('undefined','None').replace('null','None'))


def get_note_images(url='https://www.xiaohongshu.com/explore/64c5ec88000000000b028d78'):
    d = get_note_json(url)
    info = list(get_dict_info(d))[0]
    remark = json.dumps(info.get('tagList'), indent=3)
    for x in get_dict_images(info):
        file_id_redbook = os.path.basename(x.get('url')).rsplit('!',1)[0]
        suffix = x.pop('imageScene').rsplit('_', 1)[-1].lower()
        fname = '%s.%s' % (file_id_redbook, suffix)
        x.update({'note_id_redbook':info.get('noteId'), 
                  'title_note_redbook':info.get('title'),
                  'note_card_type':info.get('type'),
                  'file_id_redbook':file_id_redbook,
                  'fname':fname,
                  'remark':remark,
                  })
        yield x