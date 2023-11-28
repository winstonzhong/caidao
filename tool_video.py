'''
Created on 2023年11月28日

@author: lenovo
'''

import cv2

from helper_cmd import CmdProgress


def split_video(fpath):
    vidcap = cv2.VideoCapture(fpath)
    while 1:
        success,image = vidcap.read()
        if not success:
            break
        yield image
        
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
            