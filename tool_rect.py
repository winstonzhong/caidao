'''
Created on 2023年6月12日

@author: lenovo
'''
import itertools
import re

from cached_property import cached_property
import numpy
from numpy.lib._iotools import _is_string_like
import pandas

from tool_numpy import numpy_fill, file2array


LEFT_DIRECTION = -1
RIGHT_DIRECTION = 1
UP_DIRECTION = -1
DOWN_DIRECTION = 1

def roll_down(a, shift=1, axis=None):
    assert shift > 0
    a = numpy.roll(a.astype(float), shift, axis=axis)
    a[:shift] = numpy.nan
    return a

def roll_up(a, shift=1, axis=None):
    assert shift > 0
    a = numpy.roll(a.astype(float), -shift, axis=axis)
    a[-shift:] = numpy.nan
    return a

class Rect(object):
    SPACE_TOP_RATIO = 1.1
    SPACE_LEFT_RATIO = 2.5
    SPACE_RIGHT_RATIO = 2.5
    FACE_DENSITY = 0.04
    
    MIN_FACE_WIDTH = 40
    
    ptn_bounds = re.compile('[\d\.]+')

    @classmethod
    def get_exact_division_size(cls, w, h):
        '''
        >>> Rect.get_exact_division_size(512,512) == (0, 512, 0, 512)
        True
        >>> Rect.get_exact_division_size(12,12) == (2, 10, 2, 10)
        True
        >>> Rect.get_exact_division_size(504,513) == (0, 512, 0, 504)
        True
        >>> Rect.get_exact_division_size(504,514) == (1, 513, 0, 504)
        True
        >>> Rect.get_exact_division_size(517,514) == (1, 513, 2, 514)
        True
        '''
        df = pandas.DataFrame(data=[w, h], index=('w', 'h'), columns=['v'])
        df['edv'] = (df.v / 8).astype(int) * 8
        df['delta'] = df.v - df.edv
        df['laoke'] = (df.delta / 2).astype(int)
        df['weiba'] = df.delta - df.laoke
        df.weiba = df.v - df.weiba
        d = df[['laoke', 'weiba']].to_dict('split').get('data')
        return *d[1], *d[0]

    def __str__(self, *args, **kwargs):
        return '{self.left} {self.right} {self.top} {self.bottom}<{self.width}, {self.height}>'.format(self=self)
    
    def __repr__(self, *args, **kwargs):
        return self.__str__()
    
    def __init__(self, left, right, top, bottom):
        self.left = int(left)
        self.right = int(right)
        self.top = int(top)
        self.bottom = int(bottom)
    
    def __eq__(self, other):
        return self.left == other.left and self.right == other.right and self.top == other.top and self.bottom == other.bottom
    
    def contains_point(self, x, y):
        '''判断坐标点是否在矩形范围内
        >>> Rect(*[100, 120, 100, 120]).contains_point(1,1)
        False
        >>> Rect(*[100, 120, 100, 120]).contains_point(110,111)
        True
        >>> Rect(*[100, 120, 100, 120]).contains_point(130,110)
        False
        '''
        return x >= self.left and x <= self.right and y >= self.top and y <= self.bottom
    
    def to_square(self, max_width=10000, max_height=10000):
        '''转换成正方形
        >>> Rect(*[100, 120, 100, 120]).to_square() == Rect(*[100, 120, 100, 120])
        True
        >>> Rect(*[100, 120, 100, 118]).to_square() == Rect(*[100, 120, 99, 119])
        True
        >>> Rect(*[100, 111, 100, 110]).to_square() == Rect(*[99,110,99,110])
        True
        >>> Rect(*[0, 120, 0, 100]).to_square() == Rect(*[10, 110, 0, 100])
        True
        >>> Rect(*[0, 120, 0, 130]).to_square() == Rect(*[0, 120, 5, 125])
        True
        >>> Rect(*[10, 120, 10, 140]).to_square() == Rect(*[0,130,10,140]) 
        True
        >>> Rect(*[10, 120, 10, 140]).to_square(max_width=126) == Rect(*[4,126,14,136])
        True
        >>> Rect(*[10, 160, 10, 144]).to_square(max_height=150) == Rect(*[12,158,4,150])
        True
        '''
        width = self.width
        
        height = self.height
        
        if width == height:
            return self
        
        r = max(width, height) / 2
        
        x, y = self.center
        
        left = x - max(x - r, 0)
        
        top = y - max(y - r, 0)
        
        right = min(x + r, max_width) - x
        
        bottom = min(y + r, max_height) - y
        
        r = min(left, top, right, bottom)
        
        return Rect(self.center_x - r, self.center_x + r, self.center_y - r, self.center_y + r)
        
    
    def __add__(self, other):
        return Rect(min(self.left, other.left),
                    max(self.right, other.right),
                    min(self.top, other.top),
                    max(self.bottom, other.bottom),
                    )
    
    def to_points(self):
        return numpy.array([(self.left,self.top),
                (self.right,self.top),
                (self.right,self.bottom),
                (self.left,self.bottom),
                ])
    
    @property
    def list(self):
        return [int(self.left),
                int(self.right),
                int(self.top),
                int(self.bottom)]
    
    def clone(self):
        return Rect(
            self.left,
            self.right,
            self.top,
            self.bottom,
            )
    
    def copy(self, other):
        self.left = other.left
        self.right = other.right
        self.top = other.top
        self.bottom = other.bottom
    
    def is_center_y_close(self, other, span=2):
        '''
        >>> Rect(0,4,0,4).is_center_y_close(Rect(0,4,0,4), span=2)
        True
        >>> Rect(0,4,0,4).is_center_y_close(Rect(0,4,0,3), span=2)
        True
        >>> Rect(0,4,0,4).is_center_y_close(Rect(0,4,0,10), span=2)
        False
        '''
        return abs(self.center_y - other.center_y) <= span 
    
    def is_close(self, other, span=10):
        '''
        >>> Rect(*[0, 576, 166, 768]).is_close(Rect(*[0, 576, 166, 768]))
        True
        >>> Rect(*[1, 576, 166, 768]).is_close(Rect(*[0, 576, 166, 768]))
        False
        >>> Rect(*[0, 566, 166, 768]).is_close(Rect(*[0, 576, 166, 768]))
        True
        >>> Rect(*[0, 565, 166, 768]).is_close(Rect(*[0, 576, 166, 768]))
        False
        >>> Rect(*[0, 566, 176, 768]).is_close(Rect(*[0, 576, 166, 768]))
        True
        >>> Rect(*[0, 566, 177, 768]).is_close(Rect(*[0, 576, 166, 768]))
        False
        '''
        names = ('left', 'right', 'top', 'bottom')
        for name in names:
            v2 = getattr(other, name)
            v1 = getattr(self, name)
            if v2 == 0 and v1 != v2:
                return False
            if v1 > v2 + span or v1 < v2 - span:
                return False
        return True
    
    @classmethod
    def is_src_closed_to_dst(cls, src, dst):
        if src is None and dst is None:
            return True
        if src is None or dst is None:
            return False
        return src.is_close(dst)
        
    
    def expand(self, left, right, top, bottom, width, height, safe=True):
        if safe:
            self.left = max(self.left - left, 0)  
            self.top = max(self.top - top, 0)
            self.right = min(self.right+right, width)
            self.bottom = min(self.bottom+bottom, height)
            return self
        self.left -= left
        self.top -= top
        self.right += right
        self.bottom += bottom
        
        if self.left < 0  or self.top < 0 or self.right > width or self.bottom > height:
            return None
        return self
    
    def change(self, width=None, height=None, shape=None, safe=True):
        '''
        >>> Rect(100,200,200,400).change(150, 250, (1000,900))
        75 225 175 425<150, 250>
        >>> Rect(100,200,200,400).change(80, 180, (1000,900))
        110 190 210 390<80, 180>
        >>> Rect(100,200,200,400).change(81, 181, (1000,900))
        110 191 210 391<81, 181>
        '''
        h, w = shape[:2]
        if width is not None:
            left = (width - self.width) // 2 
            right = (width - self.width) - left
        else:
            left = right =0
        
        if height is not None:
            top = (height - self.height) // 2
            bottom = (height - self.height) - top
        else:
            top = bottom = 0
        return self.expand(left, right, top, bottom, w, h, safe) 
    
    def expand_all_directions(self, shape,
                              left_ratio=0.3,
                              right_ratio=0.3,
                              top_ratio=0.3,
                              bottom_ratio=0.3,
                              ):
        return Rect(self.left - self.width * left_ratio,
                    self.right + self.width * right_ratio,
                    self.top - self.height * top_ratio,
                    self.bottom + self.height * bottom_ratio,
                    ).to_real(shape)
    
    def cut_leg_for_min_density(self, face_area, min_density=0.03):
        if face_area > 50 **2:
            density = face_area / self.area
            if density < min_density:
                new_height = (face_area / min_density) / self.width
                delta = max(0, int(self.height - new_height))
                assert self.bottom > delta
                self.bottom -= delta
        return self


    @classmethod
    def to_corners(cls, hull):
        y = hull[::, 0]
        x = hull[::, 1]
        return y.min(), y.max(), x.min(), x.max()
    
    @classmethod
    def from_array(cls, a):
        return cls(*cls.to_corners(a))
    
    @classmethod
    def from_two_points(cls, point1, point2):
        '''
        >>> Rect.from_two_points({'x':0,'y':0}, {'x':10,'y':10})
        0 10 0 10<10, 10>
        >>> Rect.from_two_points({'x':10,'y':10}, {'x':0,'y':1})
        0 10 1 10<10, 9>
        '''
        df = pandas.DataFrame((point1, point2))
        return cls(df.x.min(), df.x.max(), df.y.min(), df.y.max())
        
    @property
    def left_top(self):
        return self.left, self.top
    
    @property
    def right_bottom(self):
        return self.right, self.bottom
    
    @property
    def width(self):
        '''
        >>> Rect(0,10,0,100).width
        10
        '''
        return abs(self.right - self.left)
    
    @property
    def height(self):
        '''
        >>> Rect(0,10,0,100).height
        100
        '''
        return abs(self.bottom - self.top)
    
    @property
    def whr(self):
        return self.width / self.height
    
    @property
    def area(self):
        return self.width * self.height
    
    @property
    def center(self):
        return self.center_x, self.center_y
    
    @property
    def center_x(self):
        '''
        >>> Rect(0,10,0,100).center_x
        5
        '''
        return self.left + self.width // 2
    
    @property
    def center_y(self):
        '''
        >>> Rect(0,10,0,100).center_y
        50
        '''
        return self.top + self.height // 2
    
    def get_scale_ratio(self, other):
        '''
        >>> r1 = Rect(0,10,0,100)
        >>> r2 = Rect(0,20,0,400)
        >>> r2.get_scale_ratio(r1) == 0.375
        True
        '''
        return numpy.mean((other.width / self.width, other.height / self.height))
    
    def get_left_top(self, width, height):
        '''
        >>> Rect(0,10,0,100).get_left_top(8,80) == (1, 10)
        True
        '''
        return self.center_x - width //2, self.center_y - height //2
    
    def move(self, span_x, span_y, clone=True):
        '''
        >>> Rect(10,100,10,100).move(-10,-10)
        0 90 0 90<90, 90>
        '''
        r = self.clone() if clone else self
        r.left += span_x
        r.right += span_x
        r.top += span_y
        r.bottom += span_y
        return r
    
    def move_left_top_to(self, left, top):
        '''
        >>> Rect(0,10,0,10).move_left_top_to(1,1)
        1 11 1 11<10, 10>
        '''
        self.right -= self.left - left
        self.bottom -= self.top - top
        self.left = left
        self.top = top
        return self
        
    def move_to(self, center_x, center_y):
        '''
        >>> r = Rect(0,10,0,10).move_to(1,1)
        >>> r.width
        10
        >>> r.center_x == 1
        True
        >>> r.center_y == 1
        True
        >>> r = Rect(0,10,1,12).move_to(10,12)
        >>> r.center_x
        10
        >>> r.center_y
        12
        '''
        r = self.clone()
        delta_x = center_x - r.center_x
        r.left += delta_x
        r.right += delta_x
        delta_y = center_y - r.center_y
        r.top += delta_y
        r.bottom += delta_y
        return r
    
    def get_h_distance(self, other):
        return abs(self.center_x - other.center_x)
    
    def to_real(self, shape):
        h, w = shape[:2]
        return Rect(max(self.left, 0),
                    min(self.right, w),
                    max(self.top, 0),
                    min(self.bottom, h)
                    )
        
    def to_inner(self, shape):
        '''
        >>> Rect(0, 10, 0,10).to_inner((100,100))
        0 10 0 10<10, 10>
        >>> Rect(-5, 5, 0,10).to_inner((100,100))
        5 10 0 10<5, 10>
        >>> Rect(0, 10, -6,4).to_inner((100,100))
        0 10 6 10<10, 4>
        >>> Rect(95, 110, 0,10).to_inner((100,100))
        0 5 0 10<5, 10>
        >>> Rect(0, 10, 99,120).to_inner((100,100))
        0 10 0 1<10, 1>
        '''
        h, w = shape[:2]
        
        return Rect(abs(min(0, self.left)), 
             min(self.width, self.width - (self.right - w)),
             abs(min(0, self.top)),
             min(self.height, self.height - (self.bottom - h)),
             )

        # if self.left < 0:
        #     left = - self.left
        # else:
        #     left = 0
        #
        # if self.top < 0:
        #     top =  - self.top
        # else:
        #     top = 0
        #
        # if self.right > w:
        #     right = self.width - (self.right - w)
        # else:
        #     right = self.width
        #
        # if self.bottom > h:
        #     bottom = self.height - (self.bottom - h)
        # else:
        #     bottom = self.height
        #
        # return Rect(left, right, top, bottom)
        
    def to_exact_division_size(self):
        self.right -= self.width - 8 * (self.width  // 8)
        self.bottom -= self.height - 8 * (self.height  // 8)
        return self
    
    @property
    def space_top(self):
        return self.SPACE_TOP_RATIO * self.height
    
    @property
    def space_left(self):
        return self.SPACE_LEFT_RATIO * self.width
    
    @property
    def space_right(self):
        return self.SPACE_RIGHT_RATIO * self.width
    
    @property
    def body_width(self):
        return self.space_left + self.space_right
    
    @property
    def body_height(self):
        return int(self.area / self.FACE_DENSITY / self.body_width)
    
    @property
    def space_bottom(self):
        return self.body_height - self.space_top

    @property
    def space_bottom_full_body(self):
        return self.body_height + self.space_top

    
    @property
    def rect_body_virtual(self):
        return Rect(self.center_x - self.space_left,
                    self.center_x + self.space_right,
                    self.center_y - self.space_top,
                    self.center_y + self.space_bottom,
                    )
    

    @property
    def rect_body_virtual_full_body(self):
        return Rect(self.center_x - self.space_left,
                    self.center_x + self.space_right,
                    self.center_y - self.space_top,
                    self.center_y + self.space_bottom_full_body,
                    )
    
    def get_rect_body_real(self, shape):
        return self.rect_body_virtual.to_real(shape)
    
    # def crop_img(self, img):
    #     return img[self.top:self.bottom, self.left:self.right, ...]

    @property
    def shape(self):
        return self.height, self.width

    def crop_img(self, img):
        if self.shape == img.shape[:2]:
            return img
        return img[self.top:self.bottom + 1, self.left:self.right+1, ...]

    
    def draw_img(self, canvas, img):
        # tmp = canvas[self.top:self.bottom, self.left:self.right, ...]
        # h, w = canvas.shape[:2]
        # r = Rect(0,min(w, self.right), 0, min(h, self.bottom))
        r = self.to_real(canvas.shape)#.move_left_top_to(0,0)
        # print('canvas:', canvas.shape)
        # print('img:', img.shape)
        # print('rect:', self)
        canvas[self.top:self.bottom, self.left:self.right, ...] = img[0:r.height,0:r.width,...]
    
    def is_valid_face(self):
        return self.height > self.MIN_FACE_WIDTH and self.width > self.MIN_FACE_WIDTH
    
    def is_valid(self, min_len=5):
        '''
        >>> Rect(0,0,1,2).is_valid()
        False
        >>> Rect(0,10,1,12).is_valid()
        True
        >>> Rect(0,5,1,12).is_valid(min_len=5)
        True
        >>> Rect(0,5,1,5).is_valid(min_len=5)
        False
        '''
        return self.height >= min_len and self.width >= min_len
    
    def cut_margin(self, value):
        o = self.clone()
        o.left += value
        o.right -= value
        o.top += value
        o.bottom -= value
        if o.left >= 0 and o.top >= 0 and o.right > o.left and o.bottom > o.top:
            return o
        
    def is_collided(self, other):
        '''
        >>> Rect(0,0,10,10).is_collided(Rect(0,0,10,10))
        True
        >>> Rect(10,10,110,110).is_collided(Rect(0,0,10,10))
        False
        >>> Rect(0,0,10,10).is_collided(Rect(20,30,10,10))
        False
        '''
        if max(self.left, other.left
               ) <= min(self.right, other.right
                        ) and max(self.top, other.top
                                  ) <= min(self.bottom, other.bottom):
            return True
        else:
            return False        
    
    
    def get_horizontal_distance(self, other, direction, force_direction=True):
        '''
        >>> Rect(0,10,0,10).get_horizontal_distance(Rect(100,110,10,10), LEFT_DIRECTION) 
        inf
        >>> Rect(0,10,0,10).get_horizontal_distance(Rect(100,110,10,10), RIGHT_DIRECTION)
        90
        >>> Rect(100,110,0,10).get_horizontal_distance(Rect(0,10,10,10), RIGHT_DIRECTION)
        inf
        >>> Rect(100,110,0,10).get_horizontal_distance(Rect(0,10,10,10), LEFT_DIRECTION)
        90
        >>> Rect(0,10,0,10).get_horizontal_distance(Rect(0,10,0,10), LEFT_DIRECTION, False)
        0
        >>> Rect(0,10,0,10).get_horizontal_distance(Rect(0,10,0,10), RIGHT_DIRECTION, False)
        0
        >>> Rect(0,10,0,10).get_horizontal_distance(Rect(5,15,0,10), LEFT_DIRECTION, False)
        0
        '''
        if not force_direction and self.is_collided(other):
            return 0
        
        if direction == LEFT_DIRECTION:
            v = self.left - other.right
        elif direction == RIGHT_DIRECTION:
            v = other.left - self.right
        else:
            raise ValueError
        
        if v < 0:
            return numpy.Inf
        
        return v
    
    def is_in_range(self, other, direction, r):
        '''
        >>> Rect(0,10,0,10).is_in_range(Rect(100,110,10,10), RIGHT_DIRECTION, 0)
        False
        >>> Rect(0,10,0,10).is_in_range(Rect(100,110,10,10), RIGHT_DIRECTION, 85)
        True
        >>> Rect(0,10,0,10).is_in_range(Rect(100,110,10,10), RIGHT_DIRECTION, 84)
        False
        >>> Rect(0,10,0,10).is_in_range(Rect(100,110,10,10), LEFT_DIRECTION, 10000)
        False
        '''
        return self.get_horizontal_distance(other, direction) <= (self.width//2 + r)
    
    def is_point_in(self, x, y):
        '''
        >>> Rect(0,1080,202,1767).is_point_in(0,0)
        False
        >>> Rect(0,1080,202,1767).is_point_in(0,202)
        True
        >>> Rect(0,1080,202,1767).is_point_in(1081,202)
        False
        >>> Rect(0,1080,202,1767).is_point_in(1080,1767)
        True
        >>> Rect(0,1080,202,1767).is_point_in(1080,1768)
        False
        '''
        return x >= self.left and x<=self.right and y >= self.top and y <= self.bottom
    
    def contains(self, other):
        '''
        >>> Rect(0,1080,202,1767).contains(Rect(0,1080,202,1767))
        True
        >>> Rect(0,1080,202,1767).contains(Rect(100,1080,1202,1767))
        True
        '''
        return self.is_point_in(other.left, other.top) and self.is_point_in(self.right,self.bottom)
    
    def to_tuple(self):
        return self.left, self.top, self.right, self.bottom
    
    def to_lrtb(self):
        return self.left, self.right, self.top, self.bottom
    
    def to_bounds(self):
        return self.left, self.top, self.right, self.bottom

    def to_ltrb(self):
        return self.to_bounds()
    
    def to_lrtb_dict(self):
        return {'left':self.left,
                'right':self.right,
                'top':self.top,
                'bottom':self.bottom,
                }
    
    def to_cxy_dict(self, *a):
        d = {'x':self.center_x,
             'y':self.center_y,
             'w':self.width,
             'h':self.height,
                }
        d.update({x:getattr(self, x) for x in a})
        return d
    
    def to_xywhlp_key(self):
        return f'{self.center_x} {self.center_y} {self.width} {self.height} {self.pred_label_id} {self.prob:.2f}'
        
    
    @classmethod
    def get_out_bounds(cls, l):
        return cls(min(map(lambda x:x.left, l)), 
                   max(map(lambda x:x.right, l)),
                   min(map(lambda x:x.top, l)),
                   max(map(lambda x:x.bottom, l)),
                   )
    
    @classmethod
    def from_center(cls, center_x, center_y, len_half):
        return cls(center_x-len_half,
                   center_x+len_half,
                   center_y-len_half,
                   center_y+len_half,
                   )

    @classmethod
    def from_ltwh(cls, left, top, width, height):
        return cls(left, left+width, top, top+height)
    

    @classmethod
    def from_ltrb(cls, *ltrb):
        '''
        >>> Rect.from_ltrb(*(1,2,3,4))
        1 3 2 4<2, 2>
        >>> Rect.from_ltrb('(1,2,3,4)')
        1 3 2 4<2, 2>
        >>> Rect.from_ltrb('[1,2,3,4]')
        1 3 2 4<2, 2>
        >>> Rect.from_ltrb('[1, 2, 3, 4]')
        1 3 2 4<2, 2>
        '''
        if len(ltrb) == 4:
            left, top, right, bottom = ltrb
        elif len(ltrb) == 1:
            ltrb = ltrb[0]
            if not _is_string_like(ltrb[0]):
                left, top, right, bottom = ltrb
            else:
                l = cls.ptn_bounds.findall(ltrb)
                assert len(l) == 4
                left, top, right, bottom = [int(x) for x in l]
        else:
            raise ValueError
        return cls(left, right, top, bottom)
     

    @classmethod
    def from_xywh(cls, x, y, width, height):
        return cls(x - width//2,
                   x + width//2,
                   y - height//2,
                   y + height//2, 
                   ) 
        
    def offset(self, px, py):
        return self.left + int(self.width * px), self.top + int(self.height * py)
    
    
    @classmethod
    def from_lrtb(cls, lrtb):
        '''
        >>> Rect.from_lrtb((1,2,3,4))
        1 2 3 4<1, 1>
        >>> Rect.from_lrtb('(1,2,3,4)')
        1 2 3 4<1, 1>
        >>> Rect.from_lrtb('[1,2,3,4]')
        1 2 3 4<1, 1>
        >>> Rect.from_lrtb('[1, 2, 3, 4]')
        1 2 3 4<1, 1>
        '''
        if not _is_string_like(lrtb):
            return cls(*lrtb)
        else:
            l = cls.ptn_bounds.findall(lrtb)
            assert len(l) == 4
            return cls(*[int(x) for x in l])


    @classmethod
    def cut_empty(cls, img):
        a = numpy.any(img > 0, axis=1)
        t = numpy.where(a == 1)[0]
        if t.shape[0] == 0:
            return None, None
        return t[0], t[-1]
    
    @classmethod
    def cut_empty_margin_img(cls, img):
        top, bottom = cls.cut_empty(img)
        if top is not None and bottom is not None:
            left, right = cls.cut_empty(img.T)
            return Rect(left,right, top, bottom).crop_img(img)

    
class RectImage(Rect):
    DIRECTION_H = 0
    DIRECTION_V = 1
    COLUMNS = ('上','中','下',
               '上均','中均','下均',
               '上长','中长','下长',
               '方向','训练','标签',
               '结果')

    X_LEN = 9
    I_LASTX = X_LEN - 1 
    I_DIR = I_LASTX + 1
    I_TRAINING = I_LASTX + 2
    I_LABEL = I_LASTX + 3
    I_RESULT = I_LASTX + 4
    TOTAL_LEN = len(COLUMNS)

    
    def __init__(self, 
                 img,
                 left=None, 
                 right=None, 
                 top=None, 
                 bottom=None,
                 ):
        '''
        >>> RectImage(img1,100,200,300,500) == RectImage(img1,100,200,300,500)
        True
        >>> RectImage(img1,100,200,300,500) == RectImage(img1,100,200,300,501)
        False
        '''
        self.origin = img
        h, w = img.shape[:2]
        if left is None:
            left = 0 
            top = 0
            right = w - 1
            bottom = h - 1
        Rect.__init__(self, 
                      left, 
                      right, 
                      top, 
                      bottom)

    @classmethod
    def from_ltwh(cls, img, left, top, width, height):
        return cls(img, left, left+width, top, top+height) 

    
    def to_absolute(self, left, right, top, bottom):
        '''
        >>> RectImage(img1).width == img1.shape[1]
        True
        >>> ri=RectImage(img1,100,200,300,500)
        >>> ri.to_absolute(0,10,0,20)
        (100, 110, 300, 320)
        '''
        return left + self.left, right + self.left, top + self.top, bottom + self.top
    
    @property
    def img(self):
        return self.crop_img(self.origin)
    
    @classmethod
    def cut_empty_margin_lrtb(cls, img):
        top, bottom = cls.cut_empty(img)
        if top is not None:
            left, right = cls.cut_empty(img.T)
            if left is not None:
                return left, right, top, bottom
        return None,None,None,None
    
    
    def cut_empty_margin(self):
        left, right, top, bottom = self.cut_empty_margin_lrtb(self.img)
        if left is not None:
            return self.crop(left, right, top, bottom)
    
    @property
    def width(self):
        '''
        >>> RectImage(numpy.zeros(1000).reshape(100,-1)).width
        10
        '''
        return abs(self.right - self.left) + 1
    
    @property
    def height(self):
        '''
        >>> RectImage(numpy.zeros(1000).reshape(100,-1)).height
        100
        '''
        return abs(self.bottom - self.top) + 1
    
    # @property
    # def img(self):
    #     h, w = self._img.shape[:2]
    #     if h == self.height and w == self.width:
    #         return self._img
    #     return self.crop_img(self._img)
    
    @cached_property
    def mask(self):
        return self.img > 0

    @classmethod
    def get_boundary_points(cls, y):
        return numpy.argwhere(((y - roll_up(y)) == -1) | (((y - roll_down(y)) == -1)))
    
    @classmethod
    def add_head_tail(cls, a, n):
        if 0 not in a:
            a = numpy.concatenate(([0], a))
        if n - 1 not in a:
            a = numpy.concatenate((a, [n - 1]))
        return a
    
    @classmethod
    def get_boundary_points_zeros(cls, y, min_gap=3, debug=False):
        '''
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,1,0,0,0,0,1,1,1]), debug=0)
        [[0, 5], [8, 11]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([0,0,0,1,1,1,1,1,0,0,0,0,1,1,1,0]), debug=0)
        [[2, 8], [11, 15]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([0,0,0,1,1,1,1,1,0,0,0,0,1,1,1,1]), debug=0)
        [[2, 8], [11, 15]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([0,0,0,1,1,1,1,1,0,0,1,1,1,1,1,1]), debug=0)
        [[2, 15]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,1,0,0,1,1,1]), debug=0)
        [[0, 9]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,1,0,0,0,1,1,1]), debug=0)
        [[0, 5], [7, 10]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,1,0,0,0,1,1,1,0,0,0]), debug=0)
        [[0, 5], [7, 11]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([0,0,1,1,1,1,1,0,0,0,0,1,1,1,0]), debug=0)
        [[0, 7], [10, 14]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([0,1,1,1,1,1,0,0,0,0,1,1,1,0]), debug=0)
        [[0, 6], [9, 13]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,1,1,1,1]), debug=0)
        [[0, 7]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,0,1,1,1,1]), debug=0)
        [[0, 7]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,0,0,1,1,1]), debug=0)
        [[0, 7]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,0,0,0,1,1]), debug=0)
        [[0, 3], [5, 7]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([0] * 10), debug=0)
        []
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,1,0,1,1]), debug=0)
        [[0, 7]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,0,0,1,1]), debug=0)
        [[0, 7]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,0,0,0,1]), debug=0)
        [[0, 4], [6, 7]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,0,0,0,1,0,0,0]), debug=0)
        [[0, 4], [6, 8]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,0,0,0,1,0,0,0,1]), debug=0)
        [[0, 4], [6, 8], [10, 11]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([0,0,0,0,1,1,1,1]), debug=0)
        [[3, 7]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,0,0,0,0]), debug=0)
        [[0, 4]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,0,0,0,0,1]), debug=0)
        [[0, 4], [7, 8]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1,1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,1, 0]), debug=1)
        [[0, 111]]
        >>> RectImage.get_boundary_points_zeros(numpy.array([1,1,1,1,1,0,1,1]),min_gap=1)
        [[0, 5], [5, 7]]
        '''
        right = y - roll_up(y)
        left = y - roll_down(y)
        
            
        right = numpy.argwhere((right == -1) | ((numpy.isnan(right))  & (y == 0))).flatten()
        left = numpy.argwhere(((left) == -1) | ((numpy.isnan(left))  & (y == 0))).flatten()
        
        
        s = right - left
        
        a = numpy.concatenate((left.reshape(-1,1), right.reshape(-1,1)), axis=1)
        
        # print(a, s, right, left)
        
        a = a[ s >= min_gap - 1] if 0 not in s.shape else a
        
        a = numpy.concatenate(([0],a.flatten(),[y.shape[0]-1]))
         
        a = a.reshape(-1,2)
        
        a = a[a[:,0] != a[:,1]]
        
        return a.tolist()
        
        
        # if 0 in right:
        #     right = right[1:]
        #
        # if debug:
        #     print(right)
        #     print(left)
        #     # return
        #
        # # if 0 in right.shape:
        # #     pass
        #
        # if 0 not in left.shape and (0 in right.shape or right[0] > left[0]):
        #     right = cls.add_head_tail(right, y.shape[0])[:-1]
        #     left =  cls.add_head_tail(left, y.shape[0])[1:]
        #     m = min(right.shape[0], left.shape[0])
        #     right = right[:m]
        #     left = left[:m]
        # else:
        #     right = cls.add_head_tail(right, y.shape[0])
        #     left =  cls.add_head_tail(left, y.shape[0])
        #     m = min(right.shape[0], left.shape[0])
        #     right = right[:m]
        #     left = left[:m]
        #     s = right != left
        #     right = right[s]
        #     left = left[s]
        #
        # if debug:
        #     print('-' * 20)
        #     print(right)
        #     print(left)
        #
        #
        # mr = right[1:]
        # ml = left[0:-1]
        #
        # m = mr - ml >= min_len - 1
        #
        # if debug:
        #     print(mr, m)
        # mr = mr[m]
        # ml = ml[m]
        #
        # right = numpy.concatenate((right[0:1], mr)) if mr.size else right[0:1] 
        # left = numpy.concatenate((ml, left[-1:])) if ml.size else left[-1:]
        #
        # if debug:
        #     print('=' * 20)
        #     print(mr)
        #     print(ml)
        #     print(right)
        #     print(left)
        #
        # return list(zip(right, left)) if 0 not in right.shape else [(0, y.shape[0]-1)]
    

    def get_split_points(self, a, max_length):
        a = numpy.concatenate(([0],a.flatten(),[max_length-1]))
        return list(zip(a, roll_up(a)))[:-1]

    def split(self):
        img = self.img
        for left, right in self.v_split_points:
            for top, bottom in self.h_split_points:
                rect = RectImage(img, left, right, top, bottom)
                if rect.is_valid(min_len=5):
                    yield rect
    
    def split_zeros(self, 
                    min_gap=3, 
                    min_len=20,
                    max_missing_width=300,
                    max_missing_height=150,
                    ):
        y = self.mask.sum(axis=1) > 0
        x = self.mask.sum(axis=0) > 0
        
        l = self.get_boundary_points_zeros(x, min_gap)
        m = self.get_boundary_points_zeros(y, min_gap)
        
        
        if len(l) == 1 and len(m) == 1:
            flag_final = True
        else:
            flag_final = False
        
        for left, right in l:
            for top, bottom in m:
                if self.is_at_least_large_than(left, right, top, bottom,min_len):
                    rect = self.crop(left, right, top, bottom)
                    if flag_final:
                        if self.is_smaller_than(left, right, top, bottom, max_missing_width,max_missing_height):
                            yield rect
                            # r = rect.cut_empty_margin()
                            # if r is not None and r.width > 0 and r.height > 0:
                            #     yield r
                    else:
                        for x in rect.split_zeros(min_gap, min_len, max_missing_width, max_missing_height):
                            yield x


    def split_zeros_ext(self, 
                    min_gap=3, 
                    min_len=20,
                    ):
        y = self.mask.sum(axis=1) > 0
        x = self.mask.sum(axis=0) > 0
        
        l = self.get_boundary_points_zeros(x, min_gap)
        m = self.get_boundary_points_zeros(y, min_gap)
        
        
        if len(l) == 1 and len(m) == 1:
            flag_final = True
        else:
            flag_final = False
        
        for left, right in l:
            for top, bottom in m:
                if self.is_at_least_large_than(left, right, top, bottom,min_len):
                    rect = self.crop(left, right, top, bottom)
                    if flag_final:
                        r = rect.cut_empty_margin()
                        if r is not None and r.width > min_len and r.height > min_len:
                            yield r
                    else:
                        for x in rect.split_zeros_ext(min_gap, min_len):
                            yield x
            

    @property
    def h_split_points(self):
        return self.get_split_points(self.h_0_1_or_1_0, self.height) 

    @property
    def v_split_points(self):
        return self.get_split_points(self.v_0_1_or_1_0, self.width)
    
    @property
    def h_0_1_or_1_0(self):
        return self.get_boundary_points(self.mask.sum(axis=1) > 0)

    @property
    def v_0_1_or_1_0(self):
        return self.get_boundary_points(self.mask.sum(axis=0) > 0)
    
    def show(self):
        # show_plt_safe(*imgs, return_fig=False, h_stack=True)
        from tool_img import show_plt_safe
        show_plt_safe(self.img)
    
    def crop_img(self, img):
        if self.shape == img.shape[:2]:
            return img
        return img[self.top:self.bottom + 1, self.left:self.right+1, ...]
    
    # def crop(self, left, right, top, bottom):
    #     return RectImage(self.img,
    #                      left, right, top, bottom,
    #                      self.offset_x,
    #                      self.offset_y,
    #                      )

    def crop(self, left, right, top, bottom):
        '''
        >>> ri1 = RectImage(img1)
        >>> ri2 = ri1.crop(100,120,200,230)
        >>> ri2
        100 120 200 230<21, 31>
        >>> ri2.crop(10,16,10,18)
        110 116 210 218<7, 9>
        '''
        return RectImage(self.origin,
                         *self.to_absolute(left, right, top, bottom),
                         )
    
    def is_valid(self, min_len=5):
        return self.is_valid_rect(self.left, 
                                  self.right, 
                                  self.top, 
                                  self.bottom, 
                                  min_len)
    
    @classmethod
    def is_at_least_large_than(cls, left, right, top, bottom, min_len):        
        width = right - left
        height = bottom - top
        return width >= min_len and \
            height >= min_len
            
    @classmethod
    def is_smaller_than(cls, left, right, top, bottom, 
                        max_missing_width,
                        max_missing_height
                        ):
        width = right - left
        height = bottom - top
        return width < max_missing_width and \
            height < max_missing_height
    
    @classmethod
    def is_valid_rect(cls, left, right, top, bottom, 
                      min_len,
                      max_missing_width=300,
                      max_missing_height=150,
                      ):
        '''
        >>> RectImage.is_valid_rect(0,10,0,5,10)
        False
        >>> RectImage.is_valid_rect(0,10,0,5,5)
        True
        >>> RectImage.is_valid_rect(0,10,0,5,6)
        False
        >>> RectImage.is_valid_rect(0,10,0,5,16)
        False
        >>> RectImage.is_valid_rect(0,301,0,5,5)
        False
        >>> RectImage.is_valid_rect(0,30,0,5,5)
        True
        >>> RectImage.is_valid_rect(0,30,0,145,5)
        True
        >>> RectImage.is_valid_rect(0,30,0,150,5)
        False
        '''
        width = right - left
        height = bottom - top
        return width >= min_len and \
            height >= min_len and \
            width < max_missing_width and \
            height < max_missing_height
            
        


    def get_nonzero_count(self, axis):
        s = self.mask.sum(axis=axis)
        return numpy.nan_to_num(roll_down(s), 0),s,numpy.nan_to_num(roll_up(s), 0)
    
    @property
    def X_nonzero_count_h(self):
        return self.get_nonzero_count(axis=1)
    
    @property
    def X_nonzero_count_v(self):
        return self.get_nonzero_count(axis=0)

    @property
    def nonzero_index_fillabck(self):
        a = self.mask.flatten()
        return numpy.where(a > 0 , 
                           numpy.arange(a.size), 
                           numpy.nan).reshape(self.mask.shape)
    
    @property
    def matrix(self):
        mask = self.mask
        idx = numpy.where(mask == 0,numpy.arange(mask.shape[1]),numpy.nan)
        idx = numpy_fill(idx)
        return idx
    
    @cached_property
    def df_nonzero_index_fillabck(self):
        return pandas.DataFrame(self.nonzero_index_fillabck)

    
    def get_default_len(self, axis):
        return self.height if axis == 1 else self.width


    # def get_blank_line_segment(self, axis):
    #     df = self.df_nonzero_index_fillabck
    #     if axis == 0:
    #         df = df.floordiv(self.width)
    #     return df.fillna(method='ffill', axis=axis).diff(axis=axis)
    #
    # @cached_property
    # def df_nonzero_index_fillabck_blank_segment_length_v(self):
    #     return self.get_blank_line_segment(axis=0)
    #
    # @cached_property
    # def df_nonzero_index_fillabck_blank_segment_length_h(self):
    #     return self.get_blank_line_segment(axis=1)
        
    
    def get_mean_line_segment(self, axis):
        default_len = self.get_default_len(axis)
        df = self.df_nonzero_index_fillabck
        if axis == 0:
            df = df.floordiv(self.width)
        tmp = df.fillna(method='ffill', axis=axis).diff(axis=axis)
        # return tmp
        s = tmp.replace(0, numpy.nan).mean(axis=axis)
        s = numpy.nan_to_num(s, nan=default_len)
        return numpy.nan_to_num(roll_down(s), nan=default_len), s, numpy.nan_to_num(roll_up(s),nan=default_len)

    def get_line_segment(self, axis):
        default_len = self.get_default_len(axis)
        df = self.df_nonzero_index_fillabck
        if axis == 0:
            df = df.floordiv(self.width)
        tmp = df.fillna(method='ffill', axis=axis).diff(axis=axis)
        # return tmp
        # s = tmp.replace(0, numpy.nan)
        s_max = numpy.nan_to_num(tmp.max(axis=axis),nan=default_len) 
        s_mean = numpy.nan_to_num(tmp.replace(0, numpy.nan).mean(axis=axis),nan=default_len) 
        # s = tmp.replace(0, numpy.nan).mean(axis=axis)
        # s = numpy.nan_to_num(s, nan=default_len)
        return numpy.nan_to_num(roll_down(s_mean), nan=default_len), \
               s_mean, \
               numpy.nan_to_num(roll_up(s_mean),nan=default_len), \
               numpy.nan_to_num(roll_down(s_max), nan=default_len), \
               s_max, \
               numpy.nan_to_num(roll_up(s_max),nan=default_len)

        
    @property
    def X_line_segment_h(self):
        return self.get_line_segment(axis=1)
    
    @property
    def X_line_segment_v(self):
        return self.get_line_segment(axis=0)

    
    @property
    def X_h(self):
        return numpy.stack(list(itertools.chain(self.X_nonzero_count_h, 
                                           self.X_line_segment_h,
                                           )), 
                           axis=1)
    
    @property
    def X_v(self):
        return numpy.stack(list(itertools.chain(self.X_nonzero_count_v, 
                                           self.X_line_segment_v
                                           )), 
                           axis=1)
    

    @property
    def X_h_normalized(self):
        return self.X_h / self.height

    @property
    def X_v_normalized(self):
        return self.X_v / self.width

    def to_xyz(self, a, direction):
        return numpy.concatenate(
            (a,
             numpy.repeat(direction,a.shape[0]).reshape(-1,1),
             numpy.zeros(a.shape[0]).reshape(-1,1), 
             ),
            axis=1,
        )
    

    def predict_simple_rule(self, X):
        return numpy.where((X[...,0] == 0
                            ) & (
                                X[...,1] == 0) & (
                                    X[...,2] == 0),
                                0,
                                1,
                                )
    
    @property
    def Xyz(self):
        a = numpy.concatenate(
                (self.to_xyz(self.X_h_normalized, direction=self.DIRECTION_H),
                 self.to_xyz(self.X_v_normalized, direction=self.DIRECTION_V),
                 ),
                axis=0,
            )
        b = self.predict_simple_rule(a).reshape(-1,1)
        return numpy.concatenate((a, b), axis=1)
    
    

if __name__ == "__main__":
    import doctest
    img1 = file2array('test_split_zeros.bin')
    mask1 = img1 > 0
    print(doctest.testmod(verbose=False, report=False))
    