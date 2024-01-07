'''
Created on 2023年11月29日

@author: lenovo
'''
import itertools
import time

import numpy
from paddleocr import PaddleOCR

from tool_img import get_canvas
from tool_rect import Rect


ocr = PaddleOCR(use_angle_cls=True, lang='ch') 


def detect(img):
    result = ocr.ocr(img, cls=True)
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            print(line)
    return result

def speed_test(img):
    old = time.time()
    r = ocr.ocr(img, cls=False)
    print(time.time() - old)
    return r

def find_text_simpile(img):
    r = ocr.ocr(img, cls=False)
    for x in itertools.chain.from_iterable(r):
        a, b = x
        text, prob = b
        a = numpy.array(a)
        yield text,Rect(a[...,0].min(), a[...,0].max(),a[...,1].min(),a[...,1].max()),prob

def get_oneline(img):
    if img is not None:
        l = find_text_simpile(img)
        return ''.join([x[0] for x in l])

def get_text_mask(img, left_margin=10, right_margin=10, top_margin=10, bottom_margin=10):
    h, w = img.shape[:2]
    mask = get_canvas(w, h)
    for x in find_text_simpile(img):
        rect = x[1].expand(left_margin,right_margin,top_margin,bottom_margin,width=w, height=h)
        mask[rect.top:rect.bottom, rect.left:rect.right, ...] = 255
    return mask
    
    