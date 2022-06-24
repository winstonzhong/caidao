'''
Created on 2022年6月23日

@author: winston
'''
import glob
import os

import ffmpeg
import pandas

from tool_env import OS_WIN
from helper_cmd import CmdProgress


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
