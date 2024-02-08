'''
Created on 2023年11月28日

@author: lenovo
'''

import json
import os

import cv2

from helper_cmd import CmdProgress
from tool_ffmpeg import to_timestr_with_hour, trim_video


def split_video(fpath):
    vidcap = cv2.VideoCapture(fpath)
    while 1:
        success,image = vidcap.read()
        if not success:
            break
        yield image

def split_video_into_pngs(fpath):
    base_dir = os.path.join(os.path.dirname(fpath), 'output')
    if not os.path.lexists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    for i, x in enumerate(split_video(fpath)):
        print(i)
        cv2.imwrite(os.path.join(base_dir, '%d.png' % i), x)
        
        
def merge_video(images, fpath, fps, margin_top=0, margin_bottom=0):
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    h, w = images[0].shape[:2]
    h -= margin_top + margin_bottom
    out = cv2.VideoWriter(fpath,fourcc,fps,(w, h), True)
    cp = CmdProgress(len(images))
    for img in images:
        out.write(img[margin_top:h+margin_top,0:w,...])
        cp.update()
    out.release() 


def read_draft_info(fpath, do_trim=True, fpath_video=None):
    with open(fpath, 'r', encoding='utf8') as fp:
        d = json.load(fp)
    # return d.get("draft_materials")
    base_dir = os.path.dirname(fpath) 
    for i, x in enumerate(d.get("draft_materials")[0].get('value')):
        if x.get('sub_time_range').get('duration') != -1:
            # num = models.PositiveSmallIntegerField(verbose_name='编号', null=True, blank=True)
            # subtitle = models.CharField(max_length=255, null=True, blank=True, verbose_name='字幕')
            # clip = models.FileField(upload_to=BASE_DIR, null=True, blank=True)
            # start = models.CharField(max_length=12, verbose_name='起始时间', null=True, blank=True)
            # end = models.CharField(max_length=12, verbose_name='结束时间', null=True, blank=True)
            # duration = models.FloatField(null=True, blank=True,verbose_name='时长')
            # trimed = models.BooleanField(default=False,verbose_name='是否已剪切到文件')            
            fpath_src = fpath_video or x.get('file_Path')
            
            if fpath_video is not None:
                if not os.path.basename(fpath_video) == os.path.basename(x.get('file_Path')):
                    print(fpath_video)
                    print(x.get('file_Path'))
                    # raise ValueError
            
            # base_dir = os.path.dirname(fpath_src)
            start = x.get('roughcut_time_range').get('start') / 1000000
            duration = x.get('roughcut_time_range').get('duration') / 1000000
            end = start + duration 
            fname = os.path.basename(fpath_src)
            d = {
                # 'clip':f'{base_dir}/{i}_{fname}',
                'clip':os.path.join(base_dir, f'{i}_{fname}'),
                'num':i, 
                'start': to_timestr_with_hour(start),
                'end': to_timestr_with_hour(end),
                'duration':duration,
                'trimed':1,
                'is_draft':1,
                }
            if do_trim:
                if not os.path.lexists(d.get('clip')):
                    trim_video(fpath_input=fpath_src, fpath_output=d.get('clip'),start=d.get('start'), end=d.get('end'))
            yield d
        
