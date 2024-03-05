'''
Created on 2023年10月19日

@author: lenovo
'''
import base64
import io

import cv2
import numpy

from helper_net import get_with_random_agent
from tool_rect import Rect

from PIL import Image, ImageEnhance


def to_9_16(img):
    h,w = img.shape[:2]
    v = 9*h // 16
    left = (w - v) // 2
    right = v + left
    return img[0:h, left:right,...]

def pil2cv2(img):
    return cv2.cvtColor(numpy.asarray(img),cv2.COLOR_RGB2BGR)

def cv2pil(img):
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)) 

def bin2img(b):
    if b is not None:
        img = numpy.frombuffer(b, numpy.uint8)
        return cv2.imdecode(img, cv2.IMREAD_ANYCOLOR)
    
def base642cv2(b64):
    return bin2img(base64.b64decode(b64))    
        # image = numpy.asarray(bytearray(self.bin), dtype="uint8")
        # return cv2.imdecode(image, cv2.IMREAD_COLOR)

    
def url2img(url):
    return bin2img(get_with_random_agent(url).content)

def to_buffer(img):
    if img is not None:
        is_success, buffer = cv2.imencode(".png", img)
        return buffer if is_success else None

def img2io(img):
    return io.BytesIO(to_buffer(img))
# io_buf = io.BytesIO(im_buf_arr)

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

def bin_to_base64url(bin_buffer):
    return 'data:image/png;base64,' + base64.b64encode(bin_buffer).decode()


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

def stack_alpha(img, mask):
    return numpy.dstack((img, mask)).astype(numpy.uint8)

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


# def put_img_left_top_with_mask(src, mask, dst, left, top, mothod='bitwise_or'):
#     img = dst.copy()
#     h, w = src.shape[:2]
#     right = left + w
#     bottom = top + h
#     a = img[top:bottom, left:right, ...]
#     b = cv2.bitwise_and(a, mask)
#     b = getattr(cv2, mothod)(wm.astype(numpy.int), a.astype(numpy.int))
#     img[top:bottom, left:right, ...] = b.astype(numpy.uint)
#     return img

def get_mask_invert(mask):
    return mask == False

def make_watermark(a, mask):
    mask_invert = mono_to_rgb((get_mask_invert(mask)*255).astype(numpy.uint8))
    mask = mono_to_rgb(mask.astype(numpy.uint8) * 255)
    b = cv2.bitwise_and(mask, a)
    
    c = (b ^ 255).astype(numpy.uint8)
    # v = 100
    # c = (numpy.where(b >= 125, 12, 200)).astype(numpy.uint8)
    
    d = cv2.bitwise_and(c, mask)
    x = cv2.bitwise_and(a, mask_invert)
    return d+x
    


def get_mask_hairstyle(wm):
    return make_mask_by_low(wm, 90,0,0)

def get_mask_logo(wm):
    return to_gray(wm) < 80

def put_better_water_mark_left_top(img, mask, left, top):
    img = img.copy()
    # gray = to_gray(wm)
    # mask = ((gray < v) * 255).astype(numpy.uint8)
    
    h,w  = mask.shape[:2]
    
    right = left + w
    bottom = top + h
    
    a = img[top:bottom, left:right, ...]
    
    img[top:bottom, left:right, ...] = make_watermark(a, mask).astype(numpy.uint8) 
    
    return img


def put_better_water_mark_middle(img, mask):
    h,w  = mask.shape[:2]
    H, W = img.shape[:2]
    left = (W - w) //2
    top = (H - h) //2
    return put_better_water_mark_left_top(img, mask, left, top)


def put_logo_and_slogan(img, logo, slogan):
    mask_logo = get_mask_logo(logo)
    mask_slogan = get_mask_hairstyle(slogan)    
    
    img = put_better_water_mark_middle(img, mask_logo)
    
    H, W = img.shape[:2]
    h1, w1 = mask_slogan.shape[:2]
    h2, w2 = logo.shape[:2]
    
    left =  (W - w1) // 2
    top = (H - h2) // 2 + h2
    
    img = put_better_water_mark_left_top(img, mask_slogan, left, top)
    return img
    
    # img = img.copy()
    # gray = to_gray(wm)
    # mask = ((gray < v) * 255).astype(numpy.uint8)
    #
    # h,w  = wm.shape[:2]
    # a = img[0:h,0:w,...]
    #
    # H, W = img.shape[:2]
    #
    # left = (W - w) //2
    # right = left + w
    #
    # top = (H - h) //2
    # bottom = top + h
    #
    # img[top:bottom, left:right, ...] = make_watermark(a, mask) 
    #
    # return img


def put_water_mark_left_top(img, wm, left, top, mothod='bitwise_or'):
    img = img.copy()
    h, w = wm.shape[:2]
    right = left + w
    bottom = top + h
    a = img[top:bottom, left:right, ...]
    b = getattr(cv2, mothod)(wm.astype(numpy.int), a.astype(numpy.int))
    img[top:bottom, left:right, ...] = b.astype(numpy.uint8)
    return img
    

# def put_water_mark_left_top_better(img, wm, left, top):
#     img = img.copy()
#     h, w = wm.shape[:2]
#     right = left + w
#     bottom = top + h
#     a = img[top:bottom, left:right, ...]
#     b = getattr(cv2, mothod)(wm.astype(numpy.int), a.astype(numpy.int))
#     img[top:bottom, left:right, ...] = b.astype(numpy.uint8)
#     return img


def put_water_mark(img, wm):
    h,w = img.shape[:2]
    h1,w1 = wm.shape[:2]
    if w < 960:
        ratio = 0.434375 * w / w1
        wm = cv2.resize(wm,dsize=None,fx=ratio,fy=ratio,interpolation=cv2.INTER_LINEAR)
        h1,w1 = wm.shape[:2]
        
    top = h - h1
    bottom = h

    left = w - w1
    right = w
    a = img[top:bottom, left:right, ...]
    
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

def make_4(imgs_4):
    assert len(imgs_4) == 4
    h,w = imgs_4[0].shape[:2]
    canvas = get_canvas(w*2, h*2)
    for i, img in enumerate(imgs_4):
        left = 0 + (i %2) * w
        right = left + w
        top = 0 + (i // 2) * h
        bottom = top + h
        canvas[top:bottom,left:right,...] = img
    return canvas

def make_4_plus_qrcode(img_qrcode, imgs_4):
    # assert len(imgs_4) == 4
    # h,w = imgs_4[0].shape[:2]
    # canvas = get_canvas(w*2, h*2)
    # for i, img in enumerate(imgs_4):
    #     left = 0 + (i %2) * w
    #     right = left + w
    #     top = 0 + (i // 2) * h
    #     bottom = top + h
    #     canvas[top:bottom,left:right,...] = img
    canvas = make_4(imgs_4)
    # s = int(w * 0.4)
    # img_qrcode = cv2.resize(img_qrcode,dsize=(s,s),fx=None,fy=None,interpolation=cv2.INTER_LINEAR)
    
    qh, qw = img_qrcode.shape[:2]
    
    H, W = canvas.shape[:2]
    
    w = W//2
    h = H//2
    
    left = w - qw//2
    right = left + qw
    top = h - qh//2
    bottom = top + qh
    
    canvas[top:bottom,left:right,...] = img_qrcode
    
    return canvas
         

def cut_core(mask, axis, v, vtype=0):
    a = mask.sum(axis=axis)
    if vtype == 1:
        t = numpy.where(a != v)[0]
    else:
        t = numpy.where(a == v)[0]

    start, end = None, None
    
    if t.shape[0] > 1:
        start, end = t[0], t[-1]
        if axis == 1:
            mask = mask[start:end+1,...]
        else:
            mask = mask[..., start:end+1]
    
    return mask, start, end

def cut_empty_margin(mask_invert):
    mask_invert = cut_core(mask_invert, axis=1, v=0, vtype=1)[0]
    return cut_core(mask_invert, axis=0, v=0, vtype=1)[0]


def get_exteral_rect(mask):
    mask, top, bottom = cut_core(mask, axis=1, v=0, vtype=1)
    _, left, right = cut_core(mask, axis=0, v=0, vtype=1)
    return Rect(left, right, top, bottom)


def split_image_into_4(img):
    h, w = img.shape[:2]
    return {
        'left_top': img[0:h//2, 0:w//2, ...],
        'right_top': img[0:h//2, w//2:w, ...],
        'left_bottom': img[h//2:h, 0:w//2,...],
        'right_bottom': img[h//2:h, w//2:w,...],
        }
    
def make_mask_by_contours(img, contours):
    height, width = img.shape[:2]
    mask = numpy.zeros((height, width), numpy.uint8)
    for points in contours:
        cv2.fillConvexPoly(mask, cv2.convexHull(points), 255)
    return mask.astype(numpy.uint8)

def make_mask_by_raw_shape_mask(mask_raw, low=10):
    mask = to_gray(mask_raw)
    mask = (mask > low).astype(numpy.uint8)
    contours, _  = cv2.findContours(mask, 
                                    cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE, 
                                    )
    return make_mask_by_contours(mask_raw, contours)
                
def cut_left_for_kuotu(img, span=100):
    h,w = img.shape[:2]
    r = h / w
    w1 = w - span
    h1 = r * w1
    # delta_top = int((h - h1) / 3)
    # delta_bottom = int(h - h1 - delta_top)
    top = int((h - h1)/2)
    # delta_bottom = delta_top
    left = span
    # top = delta_top
    bottom = int(h1 + top)
    right = w
    print(left, right, top, bottom)
    return img[top:bottom, left:right, ...]
    
def do_img_brightness(img, bright):
    '''
    控制图像的亮度。增强因子为0.0将显示黑色图像，系数为1.0表示原始图像。系数为10表示纯白色图像，值越大图像越亮。
    '''
    return ImageEnhance.Brightness(img).enhance(bright)
    
def do_img_contrast(img, contrast):
    '''
    这个类可以用来控制图像的对比度，类似于电视机上的对比度控制。增强因子为0.0时，会产生一个稳定的灰色图像。系数为1.0表示原始图像。值越大颜色越纯净。
    '''
    return ImageEnhance.Contrast(img).enhance(contrast)
    

def do_img_color_balance(img, balance):
    '''
    这个类可以用来调整图像的色彩平衡，其方式类似于彩色电视机上的控件。增强因子为0.0时，将显示黑白图像。系数为1.0表示原始图像，值越大颜色也少越鲜艳。
    '''
    return ImageEnhance.Color(img).enhance(balance)


def do_img_sharpness(img, sharpness):
    '''
    此类可用于调整图像的清晰度。增强因子为0.0表示模糊图像，增强因子为1.0表示原始图像，增强因子为2.0表示锐化图像。值越大图像边界越多越清晰。
    '''
    return ImageEnhance.Sharpness(img).enhance(sharpness)


def shape_to_squrare(h, w):
    '''
    >>> shape_to_squrare(100,100)
    {'top': 0, 'bottom': 100, 'left': 0, 'right': 100}
    >>> shape_to_squrare(1920,1080)
    {'top': 420, 'bottom': 1500, 'left': 0, 'right': 1080}
    '''
    d = {}
    delta = abs(h - w)
    head = delta //2
    tail = delta - head
    if h >= w:
        d.update(top=head, bottom=h-tail, left=0, right=w)
    else:
        d.update(top=0, bottom=h, left=head, right=w-tail)
    return d

def to_squrare(img):
    h, w = img.shape[:2]
    if h == w:
        return img
    
    d = shape_to_squrare(h, w)
    
    return img[d.get('top'):d.get('bottom'), d.get('left'):d.get('right'),...]

def keep_width_to(img, width, height=None):
    h, w = img.shape[:2]
    height = width * h // w if height is None else height
    return cv2.resize(img,dsize=(width, height),fx=None,fy=None,interpolation=cv2.INTER_LINEAR),height 


def cut_empty_and_put_to_center(img, thresh_hold=0, margin=None, keep_width=None, keep_height=None):
    height, width = img.shape[:2]
    mask = to_gray(img) > thresh_hold
    r = get_exteral_rect(mask)
    tmp = r.crop_img(img)
    tmp = tmp[margin:-margin,margin:-margin,...] if margin is not None else tmp

    if keep_width is None:
        canvas = get_canvas(width, height)
        h, w = tmp.shape[:2]
        left = (width - w) // 2
        top = (height - h) // 2
        
        right = left+w
        bottom = top+h
        
        canvas[top:bottom,left:right,...] = tmp
    else:
        canvas, keep_height = keep_width_to(tmp, keep_width, keep_height)
        
    return canvas, keep_height
     
          
    
if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
