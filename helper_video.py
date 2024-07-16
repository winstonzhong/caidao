'''
Created on 2024年1月10日

@author: lenovo
'''
import glob
import os
import time

import cv2
from django.utils.functional import cached_property
import numpy
import pandas

from helper_cmd import CmdProgress
from tool_img import show, cut_empty_and_put_to_center, keep_width_to
from tool_video import split_video


def get_all_pngs(base_dir, start=0, end=None, suffix='*.png'):
    for x in glob.glob(os.path.join(base_dir, suffix)):
        try:
            i = int(os.path.basename(x).split('.')[0])
            if i >= start and (end is None or i <= end):
                yield x
        except:
            pass

class Frame(object):
    def __init__(self, img, index, fpath=None):
        self.img = img
        self.index = index
        self.fpath = fpath
        
    def show(self):
        show(self.img)
        
        
    def save(self, to_dir):
        fpath = os.path.join(to_dir, f'{self.index:05d}.png')
        cv2.imwrite(fpath, self.img)
             
    @property
    def fpath_removed_text(self):
        fdir = os.path.join(os.path.dirname(self.fpath), 'rtxt')
        if not os.path.lexists(fdir):
            os.makedirs(fdir, exist_ok=True)
        return os.path.join(fdir, '%d.png' % self.index)
    
    def __lt__(self, other):
        return self.index < other.index
    
    @classmethod
    def from_fpath(cls, fpath):
        return cls(cv2.imread(fpath),
                   int(os.path.basename(fpath).split('.')[0]),
                   fpath,
                   )
    
    @cached_property
    def a_hash(self):
        img = cv2.resize(self.img, (8, 8))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        avg = gray.sum() /gray.size
        r = numpy.where(gray > avg, 1, 0)
        return r
    
    def get_distance_a_hash(self, other):
        return cv2.bitwise_xor(self.a_hash, other.a_hash).sum()
    
    @classmethod
    def to_frames(cls, *a):
        i = 0
        for fpath in a:
            for img in split_video(fpath):
                yield cls(img, i)
                i += 1
                
    def cut_empty_and_put_to_center(self, keep_width=None, keep_height=None):
        # print(keep_width, keep_height)
        self.img, height = cut_empty_and_put_to_center(self.img, 
                                               keep_width=keep_width,
                                               keep_height=keep_height,
                                               )
        return height
        
    
    def keep_width_to(self, width, height=None):
        self.img, height =  keep_width_to(self.img, width, height)
        return height
                
    
    
class Video(object):
    def __init__(self, frames, fpath=None, fps=30):
        self.frames = frames
        self.frames.sort()
        self.fpath = fpath
        self.fps = fps
        self.d_frames = {x.index:x for x in self.frames}
        self.index = 0
        self.total_frames = len(self.frames)
        
    def play(self):
        for frame in self.frames:
            cv2.imshow('playing',frame.img)
            cv2.waitKey(10)
        cv2.waitKey()
        cv2.destroyAllWindows()
    
    def cut_empty_and_put_to_center_all(self, keep_width=None):
        cp = CmdProgress(self.total_frames)
        keep_height = None
        for x in self.frames:
            keep_height = x.cut_empty_and_put_to_center(keep_width, keep_height)
            cp.update()


    def keep_width_to_all(self, keep_width):
        cp = CmdProgress(self.total_frames)
        keep_height = None
        keep_width = int(keep_width)
        for x in self.frames:
            keep_height = x.keep_width_to(keep_width, keep_height)
            cp.update()

    
    @classmethod
    def extract_first_frame(cls, fpath, fpath_output_img=None):
        img = cls.from_video(fpath).frames[0].img
        if fpath_output_img is None:
            fpath_output_img = f'{os.path.dirname(fpath)}/{time.time()}.png'
        cv2.imwrite(fpath_output_img, img)
        return fpath_output_img
        
    @classmethod
    def from_dir(cls, base_dir, start=0, end=None, suffix='*.png', fps=30):
        fpath = os.path.join(base_dir, 'out_cv.mp4')
        frames = list(map(lambda x:Frame.from_fpath(x), get_all_pngs(base_dir, start, end, suffix)))
        return cls(frames, fpath=fpath, fps=fps)
    
    @classmethod
    def from_video(cls, *a, **kws):
        return cls(frames=list(Frame.to_frames(*a)), **kws)
    
    @property
    def df(self):
        data = map(lambda p:{'i':p[0], 'n':p[1].index}, enumerate(self.frames))
        df = pandas.DataFrame(data)
        df['pre'] = [numpy.nan] + list(map(lambda i:self.frames[i].get_distance_a_hash(self.frames[i-1]), range(1,len(self.frames))))
        # df['next'] = list(map(lambda i:self.frames[i].get_distance_a_hash(self.frames[i+1]), range(0,len(self.frames) - 1))) + [numpy.nan]
        return df
    
    @property
    def df_fangdou(self):
        df = self.df
        tmp = df[df.pre >=2].copy()
        tmp.i = tmp.i.diff()
        return tmp[tmp.i > 5]
    
    @property
    def d_fangdou(self):
        d = {}
        for x in  self.df_fangdou.to_dict('records'):
            for i in range(int(x.get('n') - 1), int(x.get('n') - x.get('i')), -1):
                d[i] = int(x.get('n') - x.get('i') - 1)
        return d
    
    def save(self, margin_top=0, margin_bottom=0, d_fangdou={}, fpath=None):
        fpath = fpath or self.fpath
        # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        h, w = self.frames[0].img.shape[:2]
        h -= margin_top + margin_bottom
        out = cv2.VideoWriter(fpath,fourcc,self.fps,(w, h), True)
        cp = CmdProgress(len(self.frames))
        for x in self.frames:
            if x.index in d_fangdou:
                img = self.d_frames.get(d_fangdou.get(x.index)).img
            else:
                img = x.img
            out.write(img[margin_top:h+margin_top,0:w,...])
            cp.update()
        out.release() 

    def save_removed_text_all(self):
        cp = CmdProgress(len(self.frames))
        for x in self.frames:
            x.save_removed_text()
            cp.update()
        
    def save_frames(self, to_dir):
        if not os.path.lexists(to_dir):
            os.makedirs(to_dir, exist_ok=True)
        cp = CmdProgress(len(self.frames))
        for x in self.frames:
            x.save(to_dir)
            cp.update()
    
    @classmethod
    def test_in_one(cls):
        v1 = Video.from_dir(r'Z:\backup\testit\1', 1360)
        d = v1.d_fangdou
        # v2 = Video.from_dir(r'Z:\backup\testit\1\1360_1490_f2f0\rtxt')
        v2 = Video.from_dir(r'Z:\backup\testit\1\1360_1490_f2f0')
        v2.save(d_fangdou=d, fpath='f:/test/test2.mp4', margin_top=73)
        
        
    @classmethod
    def save_first_frame(cls, src=r'V:\tmp\pic', dst_dir=r'V:\tmp\expand_test'):
        if os.path.isdir(src):
            files = glob.glob(os.path.join(src, '*.mp4'))
        else:
            files = (src,)
            
        for x in files:
            fname = os.path.basename(x).rsplit('.', 1)[0]
            fpath = os.path.join(dst_dir, f'{fname}.png')
            if not os.path.lexists(fpath):
                v = cls.from_video(x)
                cv2.imwrite(fpath, v.frames[0].img)

if  __name__ == "__main__":
    v1 = Video.from_dir(r'Z:\backup\testit\1', 1360)
    v1.save(fpath=r'Z:\backup\testit\1\test1111.mp4')
    print(v1.fpath)
    print('111')            