'''
Created on 2022年6月23日

@author: winston
'''
import glob
import hashlib
import os
from pathlib import Path
import shutil

import cv2
import ffmpeg
import pandas

from helper_cmd import CmdProgress
from helper_net import get_with_random_agent
from tool_env import OS_WIN


suffix_mv = ('mp4', 'mkv', 'rmvb')


def get_dir_key(fname):
    return hashlib.sha256(fname.encode()).hexdigest()[:4]


def has_file(fpath):
    return os.path.lexists(str(fpath)) and os.path.getsize(fpath) > 0

def copy_dir(fdir_src, fdir_dst):
    src = Path(fdir_src)
    dst = Path(fdir_dst)
    i = 1
    for x in src.rglob('*.*'):
        if not os.path.isdir(str(x)):
            p = dst / x.relative_to(src)
            bp = has_file(p)
            print(i, x, bp)
            if not bp:
                if not os.path.lexists(p.parent):
                    os.makedirs(p.parent)
                shutil.copy(x, p)
        i += 1

def copy_dir_hashed(fdir_src, fdir_dst):
    src = Path(fdir_src)
    dst = Path(fdir_dst)
    i = 1
    for x in src.rglob('*.*'):
        if not os.path.isdir(str(x)):
            p = dst / x.relative_to(src)
            p = p.parent / get_dir_key(p.name) / p.name 
            bp = has_file(p)
            print(i, x, bp)
            if not bp:
                if not os.path.lexists(p.parent):
                    os.makedirs(p.parent)
                shutil.copy(x, p)
        i += 1



def get_all_files(fpath, suffixs):

    l = glob.glob(os.path.join(fpath, '**', '*'), recursive=True)

    l = (list(filter(lambda x: not os.path.isdir(x), l)))

    df = pandas.DataFrame(l, columns=['fpath'])

    df['suffix'] = df.fpath.str.split('.').apply(lambda x: x[-1].lower())

    df = df[df.suffix.isin(suffixs)]

    return df


def get_all_movie_files(root='/large', suffixs=('mp4', 'mkv', 'rmvb')):
    fpath = os.path.join(root, 'movie')
    df = get_all_files(fpath, suffixs)
    s = df.fpath.str.rsplit('.', n=1).apply(lambda x: x[0] + '.srt')
    df['has_srt'] = s.apply(lambda x: os.path.lexists(x)
                            and os.stat(fpath).st_size > 0)
    return df


def get_root():
    if OS_WIN:
        root = 'z:/'
    elif os.path.lexists('/home/zyc'):
        root = '/media/zyc/Data56T'
    else:
        root = '/large'
    return root


def get_all_movie_files_auto_root():
    return get_all_movie_files(get_root())


def get_all_srt():
    return get_all_movie_files(get_root(), ('srt',))


def extract_sub(fpath):
    stream = ffmpeg.input(fpath)
    fpath = fpath.rsplit('.', maxsplit=1)[0] + '.srt'
    stream = ffmpeg.output(stream, fpath)
    ffmpeg.run(stream, quiet=True)


def extract_sub_all():
    df = get_all_movie_files_auto_root()
    cp = CmdProgress(len(df))
    for x in df.to_dict('records'):
        try:
            extract_sub(x.get('fpath'))
        except:
            pass
        cp.update()

def is_valid_img(fpath, safe=False):
    if not fpath or not os.path.lexists(fpath):
        return False

    if os.path.getsize(fpath) <=0:
        return False

    if not safe:
        return True
    
    try:
        cv2.imread(fpath).shape
        return True
    except:
        pass
    return False


def download_img(url, fpath, safe=False):
    if not is_valid_img(fpath, safe):
        print('downloading:', url)
        with open(fpath, 'wb') as fp:
            fp.write(get_with_random_agent(url).content)



