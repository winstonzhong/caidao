'''
Created on 2023年11月2日

@author: lenovo
'''
import json
import os
import re

from pyquery.pyquery import PyQuery

from center_base.models.base_sd import AbstractMedia
from helper_net import get_with_random_agent
from tool_file import get_tpl_fpath, download_file


ptn_topic = re.compile('\#[^\#]+\[话题\]\#', re.M)


def remove_topics(txt):
    '''
    >>> remove_topics('截图保存后，加点锐化和颗粒更有胶片氛围哦 #滤镜调色教程[话题]# #大头照[话题]# #来拍照了[话题]# #胶片[话题]#')
    '''
    return ptn_topic.sub('', txt).strip()



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

def get_dict_videos(d):
    for x in get_all_dict(d):
        if x.get('masterUrl') and x.get('fps'):
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

def get_note_title_description_tags(url='https://www.xiaohongshu.com/explore/64c5ec88000000000b028d78'):
    d = get_note_json(url)
    info = list(get_dict_info(d))[0]
    tags = ','.join(map(lambda x:x.get('name'), info.get('tagList')))
    return '\r\n'.join((info.get('title'), info.get('desc'), tags))


def get_note_images(url='https://www.xiaohongshu.com/explore/64c5ec88000000000b028d78'):
    d = get_note_json(url)
    info = list(get_dict_info(d))[0]
    # remark = json.dumps(info.get('tagList'), indent=3)
    tags = ','.join(map(lambda x:x.get('name'), info.get('tagList')))
    remark = '\r\n'.join((info.get('title'), info.get('desc'), tags))
    
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

def get_note_medias(url):
    d = get_note_json(url)
    info = list(get_dict_info(d))[0]
    tags = ','.join(map(lambda x:x.get('name'), info.get('tagList')))
    remark = '\r\n'.join((info.get('title'), info.get('desc'), tags))
    
    for x in get_dict_images(info):
        file_id_redbook = os.path.basename(x.get('url')).rsplit('!',1)[0]
        suffix = x.pop('imageScene').rsplit('_', 1)[-1].lower()
        fname = '%s.%s' % (file_id_redbook, suffix)
        
        yield {
            'url_from': x.get('url'),
            'type_media': AbstractMedia.TYPE_IMG, 
            'status': 0,
            'meta': remark,
            'fpath': download_file(x.get('url'), get_tpl_fpath(fname)),
            }

    for x in get_dict_videos(info):
        fname = os.path.basename(x.get('masterUrl')).rsplit('!',1)[0]
        yield {
            'url_from': x.get('masterUrl'),
            'type_media': AbstractMedia.TYPE_VIDEO,
            'status': 0,
            'meta': remark,
            'fpath': download_file(x.get('masterUrl'), get_tpl_fpath(fname)),
            }

    
if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
