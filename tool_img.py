'''
Created on 2023年10月19日

@author: lenovo
'''
import base64
import io

from PIL import Image, ImageEnhance
from cached_property import cached_property
import cv2
import numpy
import pandas

from helper_net import get_with_random_agent
from tool_rect import Rect

def fast_rolling_split(img, win_height=7, stacked=True):
    '''
    >>> arr = numpy.random.choice((0,255), size=(100, 350)).astype(numpy.uint8)
    >>> c = fast_rolling_split(arr, 7) == slow_rolling_split(arr, 7)
    >>> numpy.any(c == 0)
    False
    >>> c.sum() == c.size
    True
    '''
    h, window_width = img.shape[:2]
    span = (win_height - 1) //2
    img = add_head_tail(img, span=span)

    
    
    strides = img.strides
    
    new_strides = (strides[0], strides[0], strides[1])
    
    shape=(h, win_height, window_width)

    windows = numpy.lib.stride_tricks.as_strided(img, 
                                             shape=shape, 
                                             strides=new_strides)
    
    return windows.reshape(-1, window_width) if stacked else windows    

def slow_rolling_split(img, win_height=7):
    h, w = img.shape[:2]
    span = (win_height - 1) //2
    img = add_head_tail(img, span=span)
    l = []
    for i in range(h):
        l.append(img[i:i+win_height,:])
    return numpy.stack(l).reshape(-1, w)

def add_head_tail(img, span=3):
    _, w = img.shape[:2]
    head = tail = numpy.zeros((span, w)).astype(numpy.uint8)
    return numpy.concatenate((head, img, tail))

def rotate_90(img):
    return img.T[...,::-1]

def bgr2rgb(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

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

def cv2bytes(a):
    buffer = io.BytesIO()
    numpy.savez_compressed(buffer,
               a, 
    )
    return buffer.getvalue()

def bytes2cv2(b):
    return numpy.load(io.BytesIO(b))['arr_0']

def cv2b64(a):
    return base64.b64encode(cv2bytes(a)).decode()

def b642cv2(s):
    return bytes2cv2(base64.b64decode(s.encode('utf8')))

def b642bin(b64):
    return base64.b64decode(b64)

def bin2img(b):
    if b is not None and b:
        img = numpy.frombuffer(b, numpy.uint8)
        return cv2.imdecode(img, cv2.IMREAD_ANYCOLOR)
    
def base642cv2(b64):
    return bin2img(base64.b64decode(b64))    
        # image = numpy.asarray(bytearray(self.bin), dtype="uint8")
        # return cv2.imdecode(image, cv2.IMREAD_COLOR)

def to_jpeg(img):
    _, buffer = cv2.imencode(".jpg", img)
    io_buf = io.BytesIO(buffer)
    decode_img = cv2.imdecode(numpy.frombuffer(io_buf.getbuffer(), numpy.uint8), -1)
    return  decode_img  
    
def url2img(url):
    return bin2img(get_with_random_agent(url).content)

def to_buffer(img, suffix='.png'):
    if img is not None:
        is_success, buffer = cv2.imencode(suffix, img)
        return buffer if is_success else None

def img2io(img):
    return io.BytesIO(to_buffer(img))


def img2base64(img):
    if img is not None:
        return base64.b64encode(to_buffer(img)).decode('utf8')
    

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


def bin_to_base64(bin_buffer):
    return base64.b64encode(bin_buffer).decode()

def show(img, max_length=900):
    if max_length is not None:
        img = resize_if_too_large(img, max_length)
    cv2.imshow('image', img)
    cv2.waitKey()
    cv2.destroyAllWindows()
    
def show_in_plt(img):
    from matplotlib import pyplot as plt
    from skimage.io import imshow
    if len(img.shape) == 2:
        imshow(img, cmap='gray')
    else:
        imshow(img)
    plt.show()

def show_plt_safe(*imgs, 
                  return_fig=False, 
                  h_stack=True,
                  cfg={},
                  ):
    from matplotlib import pyplot as plt
    
    if len(imgs) > 1:
        shape = [1, len(imgs)]
        
        if not h_stack:
            shape.reverse()
        
        fig, axs = plt.subplots(*shape)
        # fig.suptitle('Images')
        
        for i, img in enumerate(imgs):
            rect = cfg.get(i, None)
            if rect is not None:
                # h, w = img.shape[:2]
                axs[i].set_xlim(rect.left, rect.right)
                axs[i].set_ylim(rect.bottom, rect.top)
                # print(rect)
                axs[i].imshow(img, cmap='gray', extent=(rect.left, rect.right,rect.bottom, rect.top))
            else:
                axs[i].imshow(img, cmap='gray')
    else:
        fig, axs = plt.subplots()
        axs.imshow(imgs[0], cmap='gray')
    
    if not return_fig:
        plt.show()
    else:
        return fig
    
    
def to_plot_img(img, cmap=None):
    from matplotlib import pyplot as plt
    plt.tight_layout()

    ax = plt.imshow(img, interpolation='nearest', cmap=cmap)
    fig = ax.get_figure()
    canvas = fig.canvas
    canvas.draw()
    width, height = canvas.get_width_height()
    image_array = numpy.frombuffer(canvas.tostring_rgb(), dtype='uint8')
    image_array = image_array.reshape(height, width, 3)    
    return image_array

def to_plot_img_safe(*imgs, h_stack=True,cfg = {}):
    fig = show_plt_safe(*imgs, return_fig=True, h_stack=h_stack, cfg=cfg)
    canvas = fig.canvas
    canvas.draw()
    width, height = canvas.get_width_height()
    image_array = numpy.frombuffer(canvas.tostring_rgb(), dtype='uint8')
    image_array = image_array.reshape(height, width, 3)    
    return image_array

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

def rgb_to_mono(img):
    return img[...,0]

def mask_to_img(mask):
    return mask.astype(numpy.uint8) * 255

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

def get_canvas(width=None, height=None, img=None, mono=False):
    if img is not None:
        # height, width = img.shape[:2]
        return numpy.zeros(img.shape, dtype=numpy.uint8)
    if not mono:
        return numpy.zeros((height, width, 3), dtype=numpy.uint8)    
    return numpy.zeros((height, width), dtype=numpy.uint8)

def get_dsize(width, height, w, h):
    # r = min(h / height, w / width)
    r = min(height/h, width/w)
    return int(w * r), int(h * r)
    
def resize_image(img, width, height, simple_direct=False):
    if simple_direct:
        return cv2.resize(img,dsize=(width, height),fx=None,fy=None,interpolation=cv2.INTER_LINEAR)
    
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

def resize_if_too_large_with_ratio(img, max_length=720):
    max_len = max(img.shape[:2])
    if max_len > max_length:
        ratio = max_length / max_len 
        img = cv2.resize(img,dsize=None,fx=ratio,fy=ratio,interpolation=cv2.INTER_LINEAR)
    else:
        ratio = 1
    return img, ratio

def resize_if_too_large(img, max_length=720):
    return resize_if_too_large_with_ratio(img, max_length)[0]
    # max_len = max(img.shape[:2])
    # if max_len > max_length:
    #     ratio = max_length / max_len 
    #     img = cv2.resize(img,dsize=None,fx=ratio,fy=ratio,interpolation=cv2.INTER_LINEAR)
    # return img

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
    
    
    color = (0, 0, 255) if len(img.shape) > 2 else 255
    
    for pt in points:
        cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), color, 2)

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


def get_exteral_rect(mask, with_img=False):
    mask, top, bottom = cut_core(mask, axis=1, v=0, vtype=1)
    if top is not None and bottom is not None:
        img, left, right = cut_core(mask, axis=0, v=0, vtype=1)
        if left is not None and right is not None:
            rect = Rect(left, right, top, bottom)
            if not with_img:
                return rect
            return rect, img


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

def flatten_contours(contours):
    points = []
    for contour in contours:
        for point in contour:
            points.append(point[0])
    return numpy.array(points)

def contours_to_convexHull(contours):
    return cv2.convexHull(flatten_contours(contours))

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
     

def pack_img(img, x, y):
    b = io.BytesIO()
    b.write(int.to_bytes(x, 2, 'big'))
    b.write(int.to_bytes(y, 2, 'big'))
    b.write(to_buffer(img))
    return b.getvalue() 

def unpack_img(b):
    x = int.from_bytes(b[:2], 'big')
    y = int.from_bytes(b[2:4], 'big')
    img = bin2img(b[4:])
    return img, x, y    
          
def img2edges(img, low=80, high=200):
    img = img if len(img.shape) == 2 else to_gray(img)
    img_blur = cv2.GaussianBlur(img, (3,3), 0) 
    edges = cv2.Canny(img_blur,low, high)
    return edges
    
def contours_rect(contours, shape):
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) == 4 and SquareRect(approx, shape).is_valid():
            # print('approx:', approx.tolist())
            yield contour, approx


    
class SquareRect(object):
    def __init__(self, contour, shape=(1024,1024)):
        self.contour = contour
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        self.points = approx.reshape((-1,2))
        self.num_points = len(self.points)
        self.shape = shape
    
    @cached_property
    def min_length(self):
        return max(self.shape) * 0.08
    
    @cached_property
    def min_area(self):
        return self.min_length ** 2
    
    @cached_property
    def area(self):
        return cv2.contourArea(self.points)
    
    @cached_property
    def num_points(self):
        return len(self.points)
    
    @cached_property
    def distance(self):
        a = self.points
        b = numpy.roll(a,-2)
        return numpy.linalg.norm(a-b, axis=1)
    
    @cached_property
    def intersection_angles(self):
        a = self.points
        b = numpy.roll(a,-2)
        a = numpy.arctan2(b[...,1] - a[...,1], b[...,0] - a[...,0])
        return numpy.abs((numpy.roll(a,-1) - a) * 180/ numpy.pi)
    
    @property
    def df(self):
        d = {
                'x': pandas.Series(self.points[...,0]),
                'y': pandas.Series(self.points[...,1]),
                'distance': pandas.Series(self.distance),
                'angles': pandas.Series(numpy.mod(self.intersection_angles, 90)),
            }
        return pandas.DataFrame(d)
    
    
    def is_too_small(self):
        return (self.distance < self.min_length).sum() > 0
    
    @property
    def delta_distance(self):
        return (self.distance - numpy.roll(self.distance, -2)) / self.distance
    
    def is_distance_close(self):
        return numpy.isclose(numpy.roll(self.distance, -2),self.distance, rtol=0.18).sum() == 4
    
    def is_close_90(self):
        a = numpy.isclose(self.intersection_angles, 90, atol=10) + numpy.isclose(self.intersection_angles, 270, atol=15)
        return a.sum() == 4
             
    def is_valid(self):
        # return not self.is_too_small() and self.is_distance_close() and self.is_close_90()
        if self.num_points >= 4 and \
            not self.is_area_too_small() and \
            self.has_two_right_angle_at_least():
            return True
        return False
    
    def is_area_too_small(self):
        return self.area < self.min_area     
    
    @cached_property
    def right_angles(self):
        return numpy.isclose(self.intersection_angles, 90, atol=15) + numpy.isclose(self.intersection_angles, 270, atol=15)
    
    @cached_property
    def num_right_angle(self):
        return self.right_angles.sum()
    
    def has_two_right_angle_at_least(self):
        return self.num_right_angle >= 2
    
    @property
    def dict(self):
        return {'points_to_4': numpy.abs(self.num_points-4),
                'area': self.area,
                'right_angle_to_4':numpy.abs(self.num_right_angle - 4),
                # 'points':self.points,
                # 'contour':self.contour,
                'sr':self,
                }
    
    @classmethod
    def get_contour_valid(cls, contours, shape):
        for contour in contours:
            s = cls(contour, shape)
            if s.is_valid():
                yield s
 
    @classmethod
    def get_contour_valid_all(cls, img, masks):
        shape = img.shape[:2]
        for mask in masks:
            contours, _  = cv2.findContours(mask, 
                                            cv2.RETR_EXTERNAL,
                                            # cv2.RETR_LIST,
                                            cv2.CHAIN_APPROX_SIMPLE, 
                                            )
            for sr in cls.get_contour_valid(contours, shape):
                yield sr
                
    @classmethod
    def get_contour_valid_df(cls, img, masks):
        return pandas.DataFrame(data=map(lambda x:x.dict, 
                                         cls.get_contour_valid_all(img, masks))
        )

    @classmethod
    def get_contour_valid_most(cls, img, masks):
        df = cls.get_contour_valid_df(img, masks)
        if not df.empty:
            df = df.sort_values(by=['right_angle_to_4','points_to_4','area'], ascending=(True, True, False))
            sr = df.iloc[0].sr
            print(sr.df)
            print(sr.points.tolist())
            return sr.contour, sr.points 


def get_contour_array(mask):
    contours, _  = cv2.findContours(mask, 
                                    # cv2.RETR_EXTERNAL,
                                    cv2.RETR_LIST,
                                    cv2.CHAIN_APPROX_SIMPLE, 
                                    )
    return numpy.stack([cv2.boundingRect(x) for x in contours])

def filter_contour_array(a, max_width, max_height, min_len=10):
    return a[(a[:,2] < max_width) & (a[:,3] < max_height) & (a[:,2] >= min_len) & (a[:,3] > min_len) ]

def get_default_config_by_width_height(width, height):
    return {
            'max_width': width * 1.1,
            'max_height': height * 1.1,
            'min_len': min(width, height) / 8,
        }

def get_default_config_by_rect(rect):
    return get_default_config_by_width_height(rect.width, rect.height)

def filter_contour_array_by_rect(a, rect):
    return filter_contour_array(a, **get_default_config_by_rect(rect))

def filter_contour_array_by_wh(a, width, height):
    return filter_contour_array(a, **get_default_config_by_width_height(width, height))

def compute_group_distance(a, gap):
    half = a[...,2:] // 2
    center = a[...,0:2] + half
    i = numpy.product(half,axis=1).argmax()
    delta = numpy.abs(center - center[i]) - half - half[i]  
    return a[numpy.all( delta < gap, axis=1)], a[numpy.any( delta >= gap, axis=1)]

def get_bounding_rect(a):
    return cv2.boundingRect(numpy.concatenate((a[...,:2], a[...,:2] + a[...,2:])))

def get_rect_by_group(a, gap, max_width, max_height):
    while 0 not in a.shape:
        b, a = compute_group_distance(a, gap)
        bounds = get_bounding_rect(b)
        
        if bounds[2] > max_width + gap or bounds[3] > max_height + gap:
            continue
        
        if len(b) > 1:
            a = numpy.concatenate((numpy.array(bounds).reshape(1,-1), a))
        else:
            yield get_bounding_rect(b)

def get_bounding_array_by_group(a, gap, max_width, max_height):
    return numpy.stack(list(get_rect_by_group(a, gap, max_width, max_height))) 

def get_bounding_dict_list_by_group(a, gap, x, y, max_width, max_height):
    a = get_bounding_array_by_group(a, gap, max_width, max_height)
    center = a[...,0:2] + a[...,2:]//2
    distance = numpy.linalg.norm(center - (x,y), axis=1)

    return [{'bounds':Rect.from_ltwh(*a[i]).to_lrtb(),
             'distance':distance[i],
             'w': a[i][2],
             'h': a[i][3],
             'center':center[i].tolist(),
             } for i in range(a.shape[0])] 
    

class FracContours(object):
    def __init__(self, contours, w, h, max_len=40):
        l = list(map(lambda x:cv2.boundingRect(x), contours))
        a = numpy.stack(l)
        a = a[(a[:,2] < max_len) & (a[:,3] < max_len)]
        lt = a[:,0:2]
        rb = lt + a[:,2:] 
        b = numpy.concatenate((lt,rb[:,0:1], lt[:,1:2], rb, lt[:,0:1], rb[:,1:2]), axis=1)
        c = b.reshape(-1,4,2)
        self.canvas = get_canvas(w, h, mono=True)
        cv2.drawContours(self.canvas, c, -1, 255, 1)
    
    
    @classmethod
    def compute_mask(cls, mask, max_len=50):
        H, W = mask.shape
        contours, h  = cv2.findContours(mask, 
                                        # cv2.RETR_EXTERNAL,
                                        # cv2.RETR_LIST,
                                        # cv2.RETR_CCOMP,
                                        cv2.RETR_TREE,
                                        cv2.CHAIN_APPROX_SIMPLE, 
                                        )
        l = list(map(lambda x:cv2.boundingRect(x), contours))
        
        if l:
            a = numpy.stack(l)
    
            b = a[(a[:,2] < max_len) & (
                    a[:,3] < max_len)
                  ]
    
            
            return cls.draw_canvas(b, W, H), a
        return None, None


    @classmethod
    def compute_mask_ext(cls,mask,max_width=300,max_height = 150,c_mode=cv2.RETR_TREE):
        
        H, W = mask.shape
        contours, _  = cv2.findContours(mask, 
                                        # cv2.RETR_EXTERNAL,
                                        # cv2.RETR_LIST,
                                        # cv2.RETR_CCOMP,
                                        # cv2.RETR_TREE,
                                        c_mode,
                                        cv2.CHAIN_APPROX_SIMPLE, 
                                        )
        l = list(map(lambda x:cv2.boundingRect(x), contours))
        
        if l:
            a = numpy.stack(l)
            
            q = (a[:,2] < max_width) & (a[:,3] < max_height)
            
            b = [contours[int(i)] for i in numpy.where(q == True)[0]]
            
            return cls.draw_contours(b, W, H), a
        return None, None

    
    @classmethod
    def find_x(cls, mask, min_len = 16, max_len = 40):
        contours, h  = cv2.findContours(mask, 
                                        # cv2.RETR_EXTERNAL,
                                        # cv2.RETR_LIST,
                                        # cv2.RETR_CCOMP,
                                        cv2.RETR_TREE,
                                        cv2.CHAIN_APPROX_SIMPLE, 
                                        )
        l = list(map(lambda x:cv2.boundingRect(x), contours))

        if l:
            a = numpy.stack(l)
    
            b = a[(a[:,2] < max_len) & (
                    a[:,3] < max_len) & (
                    a[:,2] > min_len) & (
                    a[:,3] > min_len)
                  ]
            return b
            
    
    
    @classmethod
    def compute(cls, d):
        max_width = 250
        max_height = 100
        
        l = list(map(lambda x:cv2.boundingRect(x), d.get('contours')))
        a = numpy.stack(l)
        b = numpy.concatenate((a,numpy.full((1,4), numpy.nan)))
        
        b = b[d.get('h')]
        
        a_lt = a[:,0:2]
        a_rb = a_lt + a[:, 2:]
        
        b_lt = b[:,0:2]
        b_rb = b_lt + b[:, 2:]
        
        delta_lt = a_lt - b_lt
        delta_rb = b_rb - a_rb
        
        h = numpy.min(numpy.concatenate((delta_lt, delta_rb), axis=1), axis=1)
        
        a = a[(a[:,2] < max_width) & (
                a[:,3] < max_height) & (
                    h > 30 )
              ]
        # return a
        return cls.draw_canvas(a, d.get('W'), d.get('H'))
    
    @classmethod
    def draw_canvas(cls, a, w, h):
        lt = a[:,0:2]
        rb = lt + a[:,2:] 
        b = numpy.concatenate((lt,rb[:,0:1], lt[:,1:2], rb, lt[:,0:1], rb[:,1:2]), axis=1)
        c = b.reshape(-1,4,2)
        canvas = get_canvas(w, h, mono=True)
        cv2.drawContours(canvas, c, -1, 255, 1)
        return canvas
    
    @classmethod
    def draw_contours(cls, c, w, h):
        canvas = get_canvas(w, h, mono=True)
        cv2.drawContours(canvas, c, -1, 255, 1)
        return canvas
        
    
    

    
if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
