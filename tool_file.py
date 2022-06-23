'''
Created on 2022年6月23日

@author: winston
'''
import glob
import os

import pandas
from tool_env import OS_WIN

suffix_mv = ('mp4', 'mkv', 'rmvb')


def get_all_files(fpath, suffixs):

    l = glob.glob(os.path.join(fpath, '**', '*'), recursive=True)

    l = (list(filter(lambda x: not os.path.isdir(x), l)))

    df = pandas.DataFrame(l, columns=['fpath'])

    df['suffix'] = df.fpath.str.split('.').apply(lambda x: x[-1].lower())

    df = df[df.suffix.isin(suffixs)]

    return df


def get_all_movie_files(root='/large', suffixs=('mp4', 'mkv', 'rmvb')):
    fpath = os.path.join(root, 'movie')
    return get_all_files(fpath, suffixs)


def get_all_movie_files_auto_root():
    if OS_WIN:
        root = 'z:/'
    elif os.path.lexists('/home/zyc'):
        root = '/media/zyc/Data56T'
    else:
        root = '/large'

    return get_all_movie_files(root)
