'''
Created on 2023年11月28日

@author: lenovo
'''

import os

import cv2

from helper_cmd import CmdProgress


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
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    h, w = images[0].shape[:2]
    h -= margin_top + margin_bottom
    out = cv2.VideoWriter(fpath,fourcc,fps,(w, h), True)
    cp = CmdProgress(len(images))
    for img in images:
        out.write(img[margin_top:h+margin_top,0:w,...])
        cp.update()
    out.release() 
            