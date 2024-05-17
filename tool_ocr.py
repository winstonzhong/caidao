'''
Created on 2023年11月29日

@author: lenovo
'''
import itertools
import time

import cv2
import numpy
from paddleocr import PaddleOCR
import pandas

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

def is_result_list(l):
    if type(l) == list and len(l) == 2 and len(l[0]) == 4 and type(l[1]) == tuple:
        return True
    return False

def flatten_result(l):
    # print(l)
    if is_result_list(l):
        yield l
    else:
        for x in l:
            for y in flatten_result(x):
                yield y
            
def to_dict(l):
    # print(l)
    return {
        'x0':l[0][0][0],
        'y0':l[0][0][1],

        'x1':l[0][1][0],
        'y1':l[0][1][1],

        'x2':l[0][2][0],
        'y2':l[0][2][1],

        'x3':l[0][3][0],
        'y3':l[0][3][1],

        'text': l[1][0],
        'prob': l[1][1],
        'area': cv2.contourArea(numpy.array(l[0]).astype(int)),
        }    


def get_angle_horizntal(df):
    y = df.y1 - df.y0
    x = df.x1 - df.x0
    return numpy.arctan2(y, x) * 180 / numpy.pi

def detect_to_df(img):
    result = ocr.ocr(img, cls=True)
    df = pandas.DataFrame(data=map(lambda x:to_dict(x), flatten_result(result)))
    df['angle'] = get_angle_horizntal(df)
    return df[['x0', 'y0', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'prob', 'angle', 'area','text']]

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
    
    