'''
Created on 2022年5月1日

@author: Administrator
'''

from django.db import models

from evovle.helper_store import compute, get_train_test_df, compute_group
from helper_net import retry
from caidao_tools.django.tool_django import get_filters


NEW_RECORD = 0
DOWNLOADED_RECORD = 1
PRODUCED_RECORD = 2
UPLOADED_RECORD = 3
ROOT_RECORD = 4
COMPUTEED_RECORD = 5
TRANSLATED_RECORD = 6
EMPTY_RECORD = 400
DEAD_RECORD =  401
ABNORMAL_RECORD =  402
FAILED_TRANS_RECORD = 403


STATUS = ((NEW_RECORD, "新记录"),
          (DOWNLOADED_RECORD, "已下载"),
          (PRODUCED_RECORD, "已制作"),
          (UPLOADED_RECORD, "已上传"),
          (ROOT_RECORD, "根记录"),
          (COMPUTEED_RECORD, "已计算"),
          (TRANSLATED_RECORD, "已翻译"),
          (EMPTY_RECORD, "空记录"),
          (DEAD_RECORD, "坏记录"),
          (ABNORMAL_RECORD, "异常记录"),
          (FAILED_TRANS_RECORD, "翻译失败记录"),          
          )

class FullTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['blank'] = True
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'fts'

    def get_prep_value(self, value):
        return value


class Base(object):
    @classmethod
    def get_fields(cls):
        return [x.name for x in cls._meta.fields if x.name != 'id']


class BaseModel(models.Model):
    FIELDS = None
    @classmethod
    def get_fields(cls):
        if not cls.FIELDS:
            cls.FIELDS = list(map(lambda x: x.get_attname(), cls._meta.fields))
        return cls.FIELDS
    
    @classmethod
    def get_fields_without_id(cls):
        return filter(lambda x:x !='id', cls.get_fields())

    @retry(10, True)
    def save_safe(self):
        self.save()
        return self

    @classmethod
    def get_all(cls):
        start = 0
        while 1:
            o = cls.objects.filter(id__gt=start).first()
            if o is None:
                break
            yield o
            start = o.id
    
    @classmethod
    def get_filters(cls, **k):
        return get_filters(cls.get_fields(), **k)
    
    
    class Meta:
        abstract = True

class AbstractModel(BaseModel):
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True

class StatusModel(AbstractModel):
    status = models.SmallIntegerField(default=NEW_RECORD, choices=STATUS)

    class Meta:
        abstract = True
    
class BaseSection(object):
    result_cache = {}
    @property
    def direction_display(self):
        return '>=' if self.direction else '<='

    def __str__(self):
        return '{self.single_chain}{self.direction_display}{self.point}'.format(self=self)

    def simple_cut(self, is_first=False):
        s = self.single_chain.s
        if self.direction:
            s = s[s >= self.point]
        else:
            s = s[s <= self.point]
        if is_first:
            s.sort_values(ascending=not self.direction, inplace=True)
        return s.index
    
    @classmethod
    def do_simple_cut(cls, oid, is_first=False):
        obj = cls.objects.get(id=oid)
        return obj.simple_cut(is_first)
    
    @classmethod
    def batch_simple_cut_parent(cls, ids):
        ids.reverse()
        key = ','.join([str(x) for x in ids])
        if cls.result_cache.get(key) is None:
            index = cls.do_simple_cut(ids[0], is_first=True)
            for oid in ids[1:]:
                tmp = cls.do_simple_cut(oid, is_first=False)
                index = index.intersection(tmp)
            cls.result_cache.clear()
            cls.result_cache[key] = index
        return cls.result_cache.get(key)
    
    @classmethod
    def batch_simple_cut(cls, ids):
        head, root = ids[0], ids[1:]
        
        if root:
            index_root = cls.batch_simple_cut_parent(root)
            index = cls.do_simple_cut(head, is_first=False)
            index = index_root.intersection(index)
        else:
            index = cls.do_simple_cut(head, is_first=False)
        return index


    @classmethod
    def get_single_result(cls, d={'id': 152, 'ancestors': [125311]}):
        r = compute(cls.batch_simple_cut(ids=d.get('ancestors')))
        r['id'] = d.get('id')
        return r
    
    @classmethod
    def get_train_test_df(cls, ancestors=[125311]):
        return get_train_test_df(cls.batch_simple_cut(ids=ancestors))    


class AbstractSection(BaseSection, models.Model):
    sid = models.PositiveIntegerField()
    direction = models.BooleanField(null=True)
    point = models.FloatField()
   
    class Meta:
        abstract = True

        indexes = [
            models.Index(fields=['sid', 'direction']),
        ]
    
    @property
    def single_chain(self):
        raise NotImplementedError
    
    
    def simple_cut(self):
        s = self.single_chain.s
        if self.direction:
            s = s[s >= self.point]
        else:
            s = s[s <= self.point]
        return s.index

    @classmethod
    def do_simple_cut(cls, oid):
        return cls.objects.get(id=oid).simple_cut()

    @classmethod
    def batch_simple_cut_parent(cls, ids):
        key = ','.join([str(x) for x in ids])
        if cls.result_cache.get(key) is None:
            index = cls.do_simple_cut(ids[0])
            for oid in ids[1:]:
                index = index.intersection(cls.do_simple_cut(oid))
            cls.result_cache.clear()
            cls.result_cache[key] = index
        return cls.result_cache.get(key)

    @classmethod
    def batch_simple_cut(cls, ids):
        head, root = ids[-1], ids[:-1]
        
        if root:
            index_root = cls.batch_simple_cut_parent(root)
            index = cls.do_simple_cut(head)
            index = index_root.intersection(index)
        else:
            index = cls.do_simple_cut(head)
        return index

    @classmethod
    def get_single_result(cls, d={'id': 152, 'ancestors': [125311]}):
        r = compute_group(cls.batch_simple_cut(ids=d.get('ancestors')))
        r['id'] = d.get('id')
        return r
    

class AbstractDna(models.Model):
    DNA_STATUS = ((NEW_RECORD, "新"),
              (PRODUCED_RECORD, "已计算"),
              (DEAD_RECORD, "停止计算"),
              (ROOT_RECORD, "根节点"),
              )
    
    section_id = models.PositiveIntegerField()
    
    parent_id = models.PositiveBigIntegerField(null=True)

    pl = models.SmallIntegerField(null=True)
    
    atte = models.PositiveSmallIntegerField(null=True)

    status = models.SmallIntegerField(default=0, choices=DNA_STATUS)

    update_time = models.DateTimeField(auto_now=True)
    

    class Meta:
        abstract = True
        
        indexes = [
            models.Index(fields=['status', 'atte', 'pl']),
            models.Index(fields=['status', 'update_time']),
            models.Index(fields=['parent_id', 'status']),
        ]
    
    cache_section_ids = {}

    cache_singlechain_ids = {}

    @property
    def singlechain_id(self):
        if self.section_id not in self.cache_singlechain_ids:
            self.cache_singlechain_ids[self.section_id] = self.section.sid
        return self.cache_singlechain_ids.get(self.section_id)

    
    @property
    def parent(self):
        return self.__class__.objects.get(id=self.parent_id) if self.parent_id else None
    
    def set_cache_section_ids(self):
        self.cache_section_ids[self.id] = self.section_ids_clean
    
    @property
    def section_ids(self):
        rtn = self.cache_section_ids.get(self.id, None)
        if rtn is not None:
            return rtn
        
        if self.parent_id is None:
            return [self.section_id]

        return self.parent.section_ids + [self.section_id]
    
    @property
    def section_ids2(self):
        parent = self.parent
        if parent is not None:
            for x in parent.section_ids2:
                yield x
        yield self.section_id

        
    @property
    def section(self):
        raise NotImplementedError

    @property
    def dict(self):
        return {'id': self.id, 
                'ancestors': list(self.section_ids), 
                }
        
    @classmethod
    def has_tasks(cls):
        return len(cls.redis_conn.lrange(cls.cache_key, 0, 0)) == 1
    
    @classmethod
    def get_tasks_count(cls):
        return len(cls.redis_conn.lrange(cls.cache_key, 0, 1000))
    
    @classmethod
    def clear_tasks(cls):
        cls.redis_conn.delete(cls.cache_key)

    @classmethod
    def book(cls):
        return cls.redis_conn.rpop(cls.cache_key)
    
