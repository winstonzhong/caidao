'''
Created on 2023年10月19日

@author: lenovo
'''
import cv2
import numpy


def show(img):
    cv2.imshow('image', img)
    cv2.waitKey()
    cv2.destroyAllWindows()

def make_mask(img, rl, rh, gl, gh, bl, bh):
    return (
        (img[...,0] >= bl) * (img[...,0] <= bh) * (img[...,1] >= gl) * (img[...,1] <= gh) * (img[...,2] >= rl) * (img[...,2] <= rh)
        )

def make_mask_by_low(img, rl, gl, bl):
    return (
        (img[...,0] >= bl) * (img[...,1] >= gl) * (img[...,2] >= rl) 
        )

def make_mask_by_equal(img, r, g, b):
    return (
        (img[...,0] == b) * (img[...,1] == g) * (img[...,2] == r) 
        ) 

def mono_to_rgb(mask):
    return numpy.stack((mask,)*3, axis=-1)

def do_remove_background(img, mask):
    mask = mask.astype(numpy.uint8)*255
    mask_invert = mono_to_rgb(cv2.bitwise_not(mask))
    mask = mono_to_rgb(mask)
    return cv2.bitwise_and(mask_invert, img) + mask

def to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def to_black_white_by_upper_gray_value(img, v):
    gray = to_gray(img)
    mask = ((gray < v) * 255).astype(numpy.uint8)
    return mono_to_rgb(mask)

def remove_background_by_upper_gray_value(img, v):
    gray = to_gray(img)
    mask = ((gray < v) * 255).astype(numpy.uint8)
    mask = mono_to_rgb(mask)
    return cv2.bitwise_and(mask, img)

def put_water_mark(img, wm):
    h,w = img.shape[:2]
    h1,w1 = wm.shape[:2]
    if w < 960:
        ratio = 0.434375 * w / w1
        wm = cv2.resize(wm,dsize=None,fx=ratio,fy=ratio,interpolation=cv2.INTER_LINEAR)
        h1,w1 = wm.shape[:2]
        
    top = h - h1
    bottom = h
    # top = 0
    # bottom = h1

    left = w - w1
    right = w
    # left = 0
    # right = w1
    a = img[top:bottom, left:right, ...]
    
    # return a, wm
    # r = a + wm
    b = cv2.bitwise_or(wm, a)
    img[top:bottom, left:right, ...] = b
    return img
    
    
    
    
