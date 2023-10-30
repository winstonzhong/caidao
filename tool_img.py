'''
Created on 2023年10月19日

@author: lenovo
'''
import base64
import io

import cv2
import numpy


def to_buffer(img):
    if img is not None:
        is_success, buffer = cv2.imencode(".png", img)
        return buffer if is_success else None

def cv2_to_base64url(img):
    if img is not None:
        content = base64.b64encode(to_buffer(img))
        return 'data:image/png;base64,' + content.decode('utf8')

def pil_to_base64url(img):
    if img is not None:
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        content = base64.b64encode(buf.getvalue())
        return 'data:image/png;base64,' + content.decode('utf8')


def show(img):
    cv2.imshow('image', img.astype(numpy.uint8))
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

def make_mask_by_high(img, rl, gl, bl):
    return (
        (img[...,0] <= bl) * (img[...,1] <= gl) * (img[...,2] <= rl) 
        )


def make_mask_by_equal(img, r, g, b):
    return (
        (img[...,0] == b) * (img[...,1] == g) * (img[...,2] == r) 
        ) 

def mono_to_rgb(mask):
    return numpy.stack((mask.astype(numpy.uint8),)*3, axis=-1)

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
    # return mask
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
    # return a
    # return a, wm
    # r = a.astype(numpy.int) + wm
    # c = r.flatten()
    # c = numpy.where(c>=255, 255, c).astype(numpy.uint8).reshape(wm.shape)
    
    b = cv2.bitwise_xor(wm.astype(numpy.int), a.astype(numpy.int))
    img[top:bottom, left:right, ...] = b.astype(numpy.uint8)
    return img

def get_canvas(width, height):
    return numpy.zeros((height, width, 3), dtype=numpy.uint8)    

def get_dsize(width, height, w, h):
    # r = min(h / height, w / width)
    r = min(height/h, width/w)
    return int(w * r), int(h * r)
    
def resize_image(img, width, height):
    canvas = get_canvas(width, height)
    h, w = img.shape[:2]
    # if h > w:
    #     dsize = (int((height/h) * w), height)
    # else:
    #     dsize = (width, int((width/w) * h))
    # print(dsize)
    dsize = get_dsize(width, height, w, h)
    img = cv2.resize(img,dsize=dsize,fx=None,fy=None,interpolation=cv2.INTER_LINEAR)
    # return img
    # max_len = max(img.shape[:2])
    # if max_len > MAX_LENGTH:
    #     ratio = MAX_LENGTH / max_len 
    #     img = cv2.resize(img,dsize=None,fx=ratio,fy=ratio,interpolation=cv2.INTER_LINEAR)
    # return force_exact_division(img)
    h, w = img.shape[:2]
    left = (width - w) // 2
    top = (height - h) // 2
    
    right = left+w
    bottom = top+h
    
    canvas[top:bottom,left:right,...] = img
    return canvas

def get_template_points(img, template, threshold = 0.8):
    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    loc = numpy.where(res >= threshold)
    points = list(zip(*loc[::-1][-2:]))
    return points

def has_tempate(img, template, threshold = 0.8):
    return len(get_template_points(img, template, threshold)) > 0

def find_template(img, template, threshold = 0.8):
    img = img.copy()
    w, h = template.shape[::-1][-2:]
     
    points = get_template_points(img, template, threshold)
    
    for pt in points:
        cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
        
    return img

    
