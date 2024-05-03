'''
Created on 2023年6月12日

@author: lenovo
'''
import numpy
import pandas


LEFT_DIRECTION = -1
RIGHT_DIRECTION = 1
UP_DIRECTION = -1
DOWN_DIRECTION = 1

class Rect(object):
    SPACE_TOP_RATIO = 1.1
    SPACE_LEFT_RATIO = 2.5
    SPACE_RIGHT_RATIO = 2.5
    FACE_DENSITY = 0.04
    
    MIN_FACE_WIDTH = 40

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
    
    def crop_img(self, img):
        bottom = self.bottom
        right = self.right
        return img[self.top:bottom, self.left:right, ...]
    
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
    
    @classmethod
    def get_out_bounds(cls, l):
        return cls(min(map(lambda x:x.left, l)), 
                   max(map(lambda x:x.right, l)),
                   min(map(lambda x:x.top, l)),
                   max(map(lambda x:x.bottom, l)),
                   )
        
    

if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))
    