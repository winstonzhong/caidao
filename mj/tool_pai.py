'''
Created on 2022年8月24日

@author: lenovo
'''
import itertools
import json
import os
import re

import pandas

LAID = -2  # 立牌
NULLTYPE = -1
TONG = 1
TIAO = 2
WAN = 3
SY = 4
FENG = 5

HU = 1 + 100
GANG = 2 + 100
PENG = 3 + 100
CHI = 4 + 100
GUO = 5 + 100
TING = 6 + 100
FANGQI = 7 + 100
KAISHI = 8 + 100

POINT_DOWN = 9 + 100
POINT_RIGHT = 10 + 100
POINT_UP = 11 + 100
POINT_LEFT = 12 + 100

UNKONWN = 34
TIMER_DOWN = 35
TIMER_RIGHT = 36
TIMER_UP = 37
TIMER_LEFT = 38
ACTION_HU = 39
ACTION_CHI = 40
ACTION_GANG = 41
ACTION_PENG = 42
ACTION_TING = 43
ACTION_GUO = 44
READY = 45
OTHERS = {
    '未知':UNKONWN,
    '下':TIMER_DOWN,
    '右':TIMER_RIGHT,
    '上':TIMER_UP,
    '左':TIMER_LEFT,
    '胡':ACTION_HU,
    '杠':ACTION_GANG,
    '碰':ACTION_PENG,
    '吃':ACTION_CHI,
    '听':ACTION_TING,
    '过':ACTION_GUO,
    '准备':READY,
    # '立牌': LAID,
    }

ACTIONS = {
    '胡':HU,
    '杠':GANG,
    '碰':PENG,
    '吃':CHI,
    '过':GUO,
    '放弃':FANGQI,
    '听':TING,
    '开始': KAISHI,
    '下':POINT_DOWN,
    '右':POINT_RIGHT,
    '上':POINT_UP,
    '左':POINT_LEFT,
    }

ACTIONS_T = {v:k for k,v in ACTIONS.items()}

TYPES = {
    TONG:'筒',
    TIAO:'条',
    WAN:'万',
    SY:'三元',
    FENG:'风',
         }

VALUES = {
    1:range(1,10),
    2:range(1,10),
    3:range(1,10),
    4:range(1,4),
    5:range(1,5),
    }

NAMES = {
    1:{
        1:'一',
        2:'一',
        3:'一',
        4:'中',
        5:'东',
        },
    2:{
        1:'二',
        2:'二',
        3:'二',
        4:'发',
        5:'南',
        },
    3:{
        1:'三',
        2:'三',
        3:'三',
        4:'白',
        5:'西',
        },
    4:{
        1:'四',
        2:'四',
        3:'四',
        5:'北',
        },
    5:{
        1:'五',
        2:'五',
        3:'五',
        },
    6:{
        1:'六',
        2:'六',
        3:'六',
        },
    7:{
        1:'七',
        2:'七',
        3:'七',
        },
    8:{
        1:'八',
        2:'八',
        3:'八',
        },

    9:{
        1:'九',
        2:'九',
        3:'九',
        },

    }

def get_clean_label(s):
    '''
    >>> get_clean_label('10;') == '10'
    True
    >>> get_clean_label('10') == '10'
    True
    '''
    return re.search('\d+', s).group()
    

def get_action_label_yolo(i):
    '''
    >>> get_action_label_yolo(101) == 34
    True
    >>> get_action_label_yolo('101') == 34
    True
    >>> get_action_label_yolo(108) == 41
    True
    >>> get_action_label_yolo(0) == 0
    True
    >>> get_action_label_yolo(33) == 33
    True
    >>> get_action_label_yolo('19.') == 19
    True
    '''
    i = i if type(i) is int else get_clean_label(i)
    i = int(i)
    if i > 100:
        return i % 100 + 33
    return i
    

def get_root(c, below_object=True):
    '''
    >>> get_root(Pai, False) == object
    True
    >>> get_root(Pattern, False) == object
    True
    >>> get_root(ZHL, True) == Pattern
    True
    '''
    if c == object:
        return object
     
    if type(c) != type:
        return 
     
    if not c.__bases__:
        return
     
    if below_object and c.__bases__[0] == object:
        return c
     
    return get_root(c.__bases__[0], below_object)

def get_json(obj):
    if isinstance(obj, list):
        return [get_json(x) for x in obj]
    if isinstance(obj, dict):
        return {k:get_json(v) for k,v in obj.items()}
    if hasattr(obj, 'dict'):
        return obj.dict
    return obj

def get_classes_df():
    l = Pai.get_singles()
    l = [{'name':x.fullname, 'value':x.index} for x in l]
    for k,v in ACTIONS.items():
        l.append({'name':k, 'value':v})
    df = pandas.DataFrame(l)
    return df

def get_yolo_labels():
    df = get_classes_df()
    l = df.to_dict('records')
    for d in l:
        print('  %d: %s' % (d.get('value'), d.get('value')))
        
def get_yolo_labels7():
    for i in range(34):
        if i % 5 == 0:
            print('')
        print("'%s', " % Pai.get_name_by_index(i), end='') 
    print('')
    for x in ACTIONS.keys():
        print("'%s', " % x, end='')

def get_yolo_labels7_v2():
    rtn = []
    for i in range(34):
        rtn.append(Pai.get_name_by_index(i))
        
    for x in ACTIONS.keys():
        rtn.append(x)
        
    return rtn

def get_yolo_labels7_v2_display():
    rtn = get_yolo_labels7_v2()
    print('total:', len(rtn))
    return json.dumps(rtn, indent = 3, ensure_ascii=False).replace('"', "'")


def get_yolo_classess(with_actions=False):
    total = len(Pai.get_singles())
    if with_actions:
        total += len(ACTIONS)
    return list(range(0, total))

def get_yolo_classess_actions():
    start = len(Pai.get_singles())
    total = len(ACTIONS)
    return list(range(start, start+total))

def save_yolo_classes(base=r'F:\workspace\mj\it\raw_actions', write_name=False, with_actions=True):
    # l = Pai.get_singles()
    l = get_yolo_classess(with_actions)
    l = map(lambda x:str(x), l)
    fpath = os.path.join(base, 'classes.txt')
    with open(fpath, 'w') as fp:
        # l = '\n'.join(map(lambda x:str(x.index) if not write_name else x.fullname, l))
        content = '\n'.join(l)
        fp.write(content)
        

def save_yolo_classes_action(base=r'F:\workspace\mj\it\raw_actions', write_name=False):
    if write_name:
        total = len(ACTIONS)
        l = list(range(0, total))
    else:
        l = ACTIONS.key()
    fpath = os.path.join(base, 'classes.txt')
    with open(fpath, 'w') as fp:
        l = '\n'.join(map(lambda x:str(x), l))
        fp.write(l)



class Pai(object):
    singles = []
    all = []
    

    def __init__(self, index, pair):
        self.index = index
        self.type, self.value = pair
    
    def __repr__(self, *args, **kwargs):
        return self.__str__()
    
    def set_xy(self, x, y):
        self.x = x
        self.y = y
        return self
    
    def is_tongtiaowan(self):
        return self.type in (TONG, TIAO, WAN)
    
    @property
    def dict(self):
        return self.index
    
    @property
    def type_name(self):
        return TYPES.get(self.type,'') if self.type != 4 else ''
    
    @property
    def value_name(self):
        return NAMES.get(self.value, {}).get(self.type,'空')
        
    @property
    def fullname(self):
        return '{self.value_name}{self.type_name}'.format(self=self)
    
    def __str__(self, *args, **kwargs):
        return '<{self.index}>{self.fullname}'.format(self=self)
    
    def __hash__(self, *args, **kwargs):
        return self.index
    
    def __eq__(self, other):
        '''
        >>> Pai.get('东风') == Pai(30,(5,1))
        True
        >>> l = [Pai.get('东风'),Pai.get('东风')]
        >>> l.remove(Pai.get('东风'))
        >>> l
        [<30>东风]
        '''
        return self.index == other.index
    
    
    def get_related_sequence_index(self):
        '''
        >>> Pai.get('白').get_related_sequence_index() # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        TypeError: 'error'
        >>> Pai.get('一万').get_related_sequence_index()
        [[19, 20], [17, 19], [16, 17]]
        >>> Pai.get('九万').get_related_sequence_index()
        [[27, 28], [25, 27], [24, 25]]
        '''
        if self.type not in (TONG, TIAO, WAN):
            raise TypeError('error')
        i = self.index
        r = []
        for j in range(3):
            r.append(list(filter(lambda x:x!=i, range(i-j, i+3-j))))
        return r

    @classmethod
    def from_index_list(cls, l):
        '''
        >>> Pai.from_index_list([-2,-1,0])
        [<-1>空, <-1>空, <0>一筒]
        '''
        return [cls.from_index(x) for x in l]
            
    @classmethod
    def from_index(cls, i):
        '''
        >>> Pai.from_index(18).fullname == '一万'
        True
        >>> Pai.from_index(27).fullname == '中'
        True
        >>> Pai.from_index(-1).index == -1
        True
        '''
        try:
            return cls.get_singles()[cls.get_singles().index(cls(i, (0,0)))]
        except ValueError:
            return cls(NULLTYPE,(None, None))
    
    @classmethod
    def get(cls, name):
        '''
        >>> Pai.get('一万').index == 18
        True
        >>> Pai.get('中').index == 27
        True
        >>> Pai.get('东风').index == 30
        True
        >>> Pai.get('东风').type == 5
        True
        >>> Pai.get('东风').value == 1
        True
        >>> Pai.get('东').value == 1
        True
        >>> Pai.get('五万').index
        22
        >>> Pai.get('伍万').index
        22
        '''
        if name in ('东', '南', '西', '北', ):
            name += '风'
        name = name.replace('伍','五')
        return list(filter(lambda x:x.fullname == name, cls.get_all()))[0]
    
    @classmethod
    def list(cls, *names):
        return [cls.get(x) for x in names]
    
    @classmethod
    def get_singles(cls):
        if not cls.singles:
            i = 0
            for x in TYPES:
                for y in VALUES.get(x):
                    cls.singles.append(cls(i, (x,y)))
                    i += 1
        return cls.singles
    
    @classmethod
    def get_tuples(cls):
        return list((x.index, x.fullname) for x in cls.get_singles())
    
    @classmethod
    def get_name_by_index(cls, i):
        return Pai.get_singles()[i].fullname
    
    
    @classmethod
    def get_all(cls):
        if not cls.all:
            for x in cls.get_singles():
                for _ in range(4):
                    cls.all.append(x)
        return cls.all
    

    def is_yao(self):
        '''
        >>> Pai.get('一万').is_yao()
        True
        >>> Pai.get('二万').is_yao()
        False
        >>> Pai.get('一筒').is_yao()
        True
        >>> Pai.get('东风').is_yao()
        True
        >>> Pai.get('发').is_yao()
        True
        '''
        if self.type in (1,2,3):
            return self.value in (1,9)
        return True
    
    def chi_groups(self):
        '''
        >>> list( Pai.get('一万').chi_groups())
        [(<19>二万, <20>三万)]
        >>> list( Pai.get('二万').chi_groups())
        [(<18>一万, <20>三万), (<20>三万, <21>四万)]
        >>> list( Pai.get('三万').chi_groups())
        [(<19>二万, <18>一万), (<19>二万, <21>四万), (<21>四万, <22>五万)]
        '''
        if self.is_tongtiaowan():
            p_1, p_2 = self.shift(-1), self.shift(-2)
            p1, p2 = self.shift(1), self.shift(2)
            if p_1 and p_2:
                yield p_1, p_2

            if p_1 and p1:
                yield p_1, p1            
                
            if p1 and p2:
                yield p1, p2            
        
    
    def shift(self, i):
        '''
        >>> Pai.get('一万').shift(1).index
        19
        >>> Pai.get('发').shift(1)
        >>> Pai.get('东风').shift(1)
        >>> Pai.get('西风').shift(1)
        >>> Pai.get('西风').shift(-1)
        >>> Pai.get('一万').shift(-1)
        >>> Pai.get('一万').shift(2).index
        20
        >>> Pai.get('三万').shift(-1).index
        19
        >>> Pai.get('三万').shift(-2).index
        18
        '''
        if self.is_tongtiaowan():
            if self.value + i in range(1,10):
                return Pai.from_index(self.index + i)
    
    @property
    def pre(self):
        '''
        >>> Pai.get('一万').next
        <19>二万
        >>> Pai.get('一万').pre
        >>> Pai.get('二万').pre
        <18>一万
        >>> Pai.get('二万').next
        <20>三万
        '''
        return self.shift(-1)
        
    
    @property
    def next(self):
        return self.shift(1)
    
    
    @property
    def periphery(self):
        '''
        >>> list(Pai.get('一万').periphery)
        [<19>二万, <20>三万]
        >>> list(Pai.get('二万').periphery)
        [<20>三万, <18>一万]
        >>> list(Pai.get('九筒').periphery)
        [<7>八筒, <6>七筒]
        >>> list(Pai.get('发').periphery)
        []
        '''
        if self.is_tongtiaowan():
            if self.value == 1:
                yield self.shift(1)
                yield self.shift(2)
            elif self.value == 9:
                yield self.shift(-1)
                yield self.shift(-2)
            else:
                yield self.shift(1)
                yield self.shift(-1)
            

class Pattern(object):
    patterns = []
    def __init__(self, *a):
        self.l = a #if type(a) == tuple and len(a) > 1 else a[0]
        self.desk = []

    def __repr__(self, *args, **kwargs):
        return self.__str__()
        
    def __str__(self, *args, **kwargs):
        d = {}
        for x in self.l:
            d.setdefault(x.type, []).append(x)
        r = []
        for k in range(1,6):
            l = d.get(k)
            if l:
                l.sort(key=lambda x:x.index)
                r.append(''.join([x.fullname for x in l]))
        return ' '.join(r)

    @classmethod
    def get_patterns(cls):
        if not cls.patterns:
            cls.patterns = list(filter(lambda x:get_root(x)==Pattern and not x.__subclasses__(), globals().values()))
        return cls.patterns
            
    def is_valid(self):
        '''
        >>> Pattern(*Pai.list('一万','一万','一万')).is_valid()
        True
        '''
        for cls in self.get_patterns():
            if cls.is_valid(self):
                return True
        return False
    
    def clone(self, l):
        return self.__class__(*l)
    
    def get_sub(self, ptype):
        return self.clone(filter(lambda x:x.type==ptype, self.l))
    
    @property
    def tongs(self):
        return self.get_sub(ptype=1)


    @property
    def tiaos(self):
        return self.get_sub(ptype=2)

    @property
    def wans(self):
        return self.get_sub(ptype=3)
    
    @property
    def types(self):
        return map(lambda x:x.type, self.l)


    @property
    def values(self):
        return map(lambda x:x.value, self.l)
    
    
    @property
    def indexs(self):
        return map(lambda x:x.index, self.l)
    
    @property
    def count_types(self):
        return len(set(self.types))

    @property
    def count_values(self):
        return len(set(self.values))

    @property
    def count_indexs(self):
        return len(set(self.indexs))

    @property
    def length(self):
        return len(self.l)

    @property
    def INDEX_J(self):
        return set(range(27,30))


    @property
    def INDEX_Z(self):
        return set(range(30,34))
    
    @property
    def INDEX_JZ(self):
        return self.INDEX_J.union(self.INDEX_Z)

    @property
    def INDEX_WAN(self):
        return set(range(18,27))

    @property
    def INDEX_TIAO(self):
        return set(range(9,18))

    @property
    def INDEX_TONG(self):
        return set(range(0,9))
    
    @property
    def count_indexs_jz(self):
        '''
        >>> Pattern(*Pai.list('一万','四万', '二条', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','白')).count_indexs_jz == 7
        True
        >>> Pattern(*Pai.list('一万','发','白')).count_indexs_jz == 2
        True
        >>> Pattern(*Pai.list('一万','发','白','白')).count_indexs_jz == 2
        True
        '''
        return len(set(self.indexs).intersection(self.INDEX_JZ))

    @property
    def count_indexs_tong(self):
        '''
        >>> Pattern(*Pai.list('一万','四万', '二条', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','白')).count_indexs_tong == 2
        True
        >>> Pattern(*Pai.list('一万','发','白')).count_indexs_tong == 0
        True
        >>> Pattern(*Pai.list('一万','发','白','白')).count_indexs_tong == 0
        True
        '''
        return len(set(self.indexs).intersection(self.INDEX_TONG))

    @property
    def count_indexs_tiao(self):
        '''
        >>> Pattern(*Pai.list('一万','四万', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','白')).count_indexs_tiao == 1
        True
        >>> Pattern(*Pai.list('一万','发','白')).count_indexs_tiao == 0
        True
        >>> Pattern(*Pai.list('一万','发','白','白')).count_indexs_tiao == 0
        True
        '''
        return len(set(self.indexs).intersection(self.INDEX_TIAO))

    @property
    def count_indexs_wan(self):
        '''
        >>> Pattern(*Pai.list('一万','四万', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','白')).count_indexs_wan == 2
        True
        >>> Pattern(*Pai.list('一万','发','白')).count_indexs_wan == 1
        True
        >>> Pattern(*Pai.list('一万','发','白','白')).count_indexs_wan == 1
        True
        '''
        return len(set(self.indexs).intersection(self.INDEX_WAN))


    def is_sequence(self):
        s = pandas.Series(self.values).sort_values()
        return s.diff().fillna(1).astype(int).sum() == self.length
    
    def is_all_same(self):
        return self.count_types == 1 and self.count_values == 1
    
    def is_all_yao(self):
        return len(list(filter(lambda x:not x.is_yao(), self.l))) == 0
    
    def get_sequence_type(self, step=1, i=[], ptype=None, allow_break=False, drop_duplicates=False, length=None):
        p = self if ptype is None else self.get_sub(ptype)
        s = pandas.Series(p.values).sort_values()
        s = s if not drop_duplicates else s.drop_duplicates()
        s1 = s.diff().dropna()
        if length:
            flag1 = len(s) == length
        elif not allow_break:
            flag1 = s1[s1 != step].empty
        else:
            flag1 = s1[~s1.isin([step, step*2])].empty
        flag2 = True if not i else not s[s.isin(i)].empty
        return s.mod(3).min() if flag1 and flag2 else None
    
    
    def has_sequence(self, step=1, i=[], ptype=None, allow_break=False, drop_duplicates=False, length=None):
        '''
        >>> Pattern(*Pai.list('一万','一万','一万')).has_sequence()
        False
        >>> Pattern(*Pai.list('一万','二万','三万')).has_sequence()
        True
        >>> Pattern(*Pai.list('一万','二筒','三万')).has_sequence()
        True
        >>> Pattern(*Pai.list('一万','二筒','三万')).has_sequence(ptype=3)
        False
        >>> Pattern(*Pai.list('一万','二筒','三万', '二万')).has_sequence(ptype=3)
        True
        >>> Pattern(*Pai.list('一万','二筒','三万', '二万')).has_sequence(ptype=3, i=[1])
        True
        >>> Pattern(*Pai.list('一万','二筒','三万', '二万')).has_sequence(ptype=3, i=[4])
        False
        >>> Pattern(*Pai.list('一万','二筒','四万', '七万')).has_sequence(ptype=3, i=[1], step=3)
        True
        >>> Pattern(*Pai.list('一万','二筒','四万', '七万')).has_sequence(ptype=3, i=[1,4,7], step=3)
        True
        >>> Pattern(*Pai.list('一万','二筒','四万', '七万')).has_sequence(ptype=1, i=[2], step=3)
        True
        >>> Pattern(*Pai.list('一万','二筒','四万', '七万')).has_sequence(ptype=1, i=[2,5,8], step=3)
        True
        >>> Pattern(*Pai.list('一万','二筒','四万', '七万', '八筒')).has_sequence(ptype=1, i=[2,5,8], step=3, allow_break=True)
        True
        >>> Pattern(*Pai.list('一万','二筒','四万', '七万', '八筒')).has_sequence(ptype=1, i=[2,5,8], step=3, allow_break=False)
        False
        >>> Pattern(*Pai.list('三万','二筒','四万', '九万', '八筒')).has_sequence(ptype=3, i=[3], step=3, allow_break=False)
        False
        >>> Pattern(*Pai.list('三万','二筒','四万', '九万', '八筒')).has_sequence(ptype=3, i=[3], step=3, allow_break=True)
        False
        >>> Pattern(*Pai.list('三万','二筒','九万', '八筒')).has_sequence(ptype=3, i=[3], step=3, allow_break=True)
        True
        >>> Pattern(*Pai.list('六万','二筒','九万', '八筒')).has_sequence(ptype=3, i=[3,6,9], step=3, allow_break=True)
        True
        >>> Pattern(*Pai.list('六万','二筒','九万', '八筒')).has_sequence(ptype=3, i=[3,6,9], step=3, allow_break=False)
        True
        '''
        return self.get_sequence_type(step, i, ptype, allow_break, drop_duplicates, length) is not None

    def is_bk(self, allow_break=True, length=None):
        if self.length != 13:
            return False
        
        l = [self.get_sequence_type(3, ptype=i, allow_break=allow_break, length=length) for i in (1,2,3)]
        
        s = set(filter(lambda x:x is not None, l))
        
        return len(s) == 3
    
    def is_jiao(self):
        pass
    
    def is_3(self):
        return self.length == 3 and (ABC.is_valid(self) or A3.is_valid(self))
    
        
class ABC(Pattern):
    '''
    >>> ABC(*Pai.list('一万','一万','一万')).is_valid()
    False
    >>> ABC(*Pai.list('一万','二万','三万')).is_valid()
    True
    >>> ABC(*Pai.list('三万','一万','二万')).is_valid()
    True
    >>> ABC(*Pai.list('一万','二条','三万')).is_valid()
    False
    '''
    def is_valid(self):
        if self.count_types != 1:
            return False
        return self.is_sequence()

class A3(Pattern):
    '''
    >>> A3(*Pai.list('一万','一万','一万')).is_valid()
    True
    >>> A3(*Pai.list('一万','二万','三万')).is_valid()
    False
    >>> A3(*Pai.list('三万','一万','二万')).is_valid()
    False
    >>> A3(*Pai.list('一万','二条','三万')).is_valid()
    False
    >>> A3(*Pai.list('一万','一万')).is_valid()
    False
    '''
    def is_valid(self):
        return self.length == 3 and self.is_all_same()


class A2(Pattern):
    '''
    >>> A2(*Pai.list('一万','一万','一万')).is_valid()
    False
    >>> A2(*Pai.list('一万','二万','三万')).is_valid()
    False
    >>> A2(*Pai.list('三万','一万','二万')).is_valid()
    False
    >>> A2(*Pai.list('一万','二条','三万')).is_valid()
    False
    >>> A2(*Pai.list('一万','一万')).is_valid()
    True
    '''
    def is_valid(self):
        return self.length == 2 and self.is_all_same()

# class A4(Pattern):
#     '''
#     >>> A4(*Pai.list('一万','一万','一万')).is_valid()
#     False
#     >>> A4(*Pai.list('一万','二万','三万')).is_valid()
#     False
#     >>> A4(*Pai.list('三万','一万','二万')).is_valid()
#     False
#     >>> A4(*Pai.list('一万','二条','三万')).is_valid()
#     False
#     >>> A4(*Pai.list('一万','一万')).is_valid()
#     False
#     >>> A4(*Pai.list('一万','一万','一万','一万')).is_valid()
#     True
#     '''
#     def is_valid(self):
#         return self.length == 4 and self.is_all_same()

class Y13(Pattern):
    '''
    >>> Y13(*Pai.list('一万','一万','一万')).is_valid()
    False
    >>> Y13(*Pai.list('一万','一万','一万', '一条', '一筒', '九万', '九条', '九筒', '东风', '南风', '西风', '北风', '中')).is_valid()
    False
    >>> Y13(*Pai.list('一万','发','一万', '一条', '一筒', '九万', '九条', '九筒', '东风', '南风', '西风', '北风', '中')).is_valid()
    True
    >>> Y13(*Pai.list('一万','发','白', '一条', '一筒', '九万', '九条', '九筒', '东风', '南风', '西风', '北风', '中')).is_valid()
    True
    '''
    def is_valid(self):
        return self.length == 13 and self.is_all_yao() and self.count_indexs >= 12


class BK7(Pattern):
    '''
    >>> BK7(*Pai.list('一万','一万','一万')).is_valid()
    False
    >>> BK7(*Pai.list('一万','一万','一万', '一条', '一筒', '九万', '九条', '九筒', '东风', '南风', '西风', '北风', '中')).is_valid()
    False
    >>> BK7(*Pai.list('一万','发','一万', '一条', '一筒', '九万', '九条', '九筒', '东风', '南风', '西风', '北风', '中')).is_valid()
    False
    >>> BK7(*Pai.list('一万','发','白', '一条', '一筒', '九万', '九条', '九筒', '东风', '南风', '西风', '北风', '中')).is_valid()
    False
    >>> BK7(*Pai.list('一万','四万', '二条', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','白')).is_valid()
    True
    >>> BK7(*Pai.list('一万','四万', '一条', '七条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','白')).is_valid()
    False
    '''
    def is_valid(self):
        return self.is_bk() and self.count_indexs_jz == 7 

class QBK(Pattern):
    '''
    >>> QBK(*Pai.list('一万','一万','一万')).is_valid()
    False
    >>> QBK(*Pai.list('一万','一万','一万', '一条', '一筒', '九万', '九条', '九筒', '东风', '南风', '西风', '北风', '中')).is_valid()
    False
    >>> QBK(*Pai.list('一万','发','一万', '一条', '一筒', '九万', '九条', '九筒', '东风', '南风', '西风', '北风', '中')).is_valid()
    False
    >>> QBK(*Pai.list('一万','发','白', '一条', '一筒', '九万', '九条', '九筒', '东风', '南风', '西风', '北风', '中')).is_valid()
    False
    >>> QBK(*Pai.list('一万','四万', '二条', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','白')).is_valid()
    False
    >>> QBK(*Pai.list('一万','四万', '一条', '七条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','白')).is_valid()
    False
    >>> QBK(*Pai.list('一万','四万', '二条', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','七万')).is_valid()
    True
    >>> QBK(*Pai.list('一万','四万', '二条', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','五条')).is_valid()
    True
    >>> QBK(*Pai.list('一万','四万', '二条', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发','六筒')).is_valid()
    True
    >>> QBK(*Pai.list('一万','四万', '二条', '八条', '三筒', '九筒', '东风', '南风', '西风', '北风', '中','发')).is_valid()
    False
    '''
    def is_valid(self):
        return self.is_bk() and self.count_indexs_jz <= 6 

class D7(Pattern):
    '''
    >>> D7(*Pai.list('一万','一万','一万')).is_valid() 
    False
    >>> D7(*Pai.list('一万','一万','一条', '一条', '一筒', '一筒', '九条', '九条', '东风', '东风', '西风', '西风', '中')).is_valid()
    True
    >>> D7(*Pai.list('一万','一万','一万', '一万', '一筒', '一筒', '九条', '九条', '东风', '东风', '西风', '西风', '中')).is_valid()
    False
    '''
    def is_valid(self):
        return self.count_indexs == 7 and self.length == 13

class LD7(Pattern):
    '''
    >>> LD7(*Pai.list('一万','一万','一万')).is_valid() 
    False
    >>> LD7(*Pai.list('一万','一万','一条', '一条', '一筒', '一筒', '九条', '九条', '东风', '东风', '西风', '西风', '中')).is_valid()
    False
    >>> LD7(*Pai.list('一万','一万','一万', '一万', '一筒', '一筒', '九条', '九条', '东风', '东风', '西风', '西风', '中')).is_valid()
    False
    >>> LD7(*Pai.list('一万','一万','二万', '二万','三万', '三万','四万', '四万','五万', '五万','六万', '七万','七万',)).is_valid()
    True
    >>> LD7(*Pai.list('一万','一万','二万', '二万','三万', '三万','四万', '四万','五万', '五万','八万', '七万','七万',)).is_valid()
    False
    >>> LD7(*Pai.list('一万','一万','二万', '二万','三万', '三万','四万', '四万','五万', '五万','六万', '七万','八万',)).is_valid()
    False
    >>> LD7(*Pai.list('一万','一万','二万', '二万','三万', '三万','四万', '四万','五万', '五万','六万', '七条','七条',)).is_valid()
    False
    '''
    def is_valid(self):
        return self.count_indexs == 7 and self.length == 13 and self.count_types == 1 and self.has_sequence(step=1, drop_duplicates=True)

class ZHL(Pattern):
    '''
    >>> ZHL(*Pai.list('一万','四万', '二条', '八条', '三筒', '九筒', '七万', '五条', '六筒', '北风', '北风','北风','白')).is_valid()
    True
    >>> ZHL(*Pai.list('一万','四万', '二条', '白', '三筒', '九筒', '白', '五条', '六筒', '北风', '北风','北风','白')).is_valid()
    False
    >>> ZHL(*Pai.list('一万','四万', '二万', '八万', '三筒', '九筒', '七万', '五万', '六筒', '北风', '北风','北风','白')).is_valid()
    False
    '''
    def is_valid(self):
        return self.is_bk(allow_break=False, length=3)


def is_rect_overlaped(rect1, rect2):
    '''
    >>> is_rect_overlaped((0,1,10,11), (12,13,100,101))
    False
    >>> is_rect_overlaped((0,0,50,50), (10,10,100,100))
    True
    '''
    minx1, miny1, maxx1, maxy1 = rect1
    minx2, miny2, maxx2, maxy2 = rect2
    minx = max(minx1, minx2)
    miny = max(miny1, miny2)
    maxx = min(maxx1, maxx2)
    maxy = min(maxy1, maxy2)
    return minx <= maxx and miny <= maxy

ETYPES = list(itertools.chain(
        list(zip(OTHERS.values(),OTHERS.keys())),
        Pai.get_tuples(),
        ))

    
if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
