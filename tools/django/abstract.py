'''
Created on 2022年5月1日

@author: Administrator
'''
from django.db import models
from evovle.helper_store import compute, get_train_test_df

NEW_RECORD = 0
EMPTY_RECORD = -1
DOWNLOADED_RECORD = 1
PRODUCED_RECORD = 2
 
UPLOADED_RECORD = 3

STATUS = ((NEW_RECORD, "新"),
          (EMPTY_RECORD, "空"),
          (DOWNLOADED_RECORD, "已下载"),
          (PRODUCED_RECORD, "已制作"),
          (UPLOADED_RECORD, "已上传"),
          )

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
        index = cls.do_simple_cut(head, is_first=False)
        if root:
            index_root = cls.batch_simple_cut_parent(root)
            index = index_root.intersection(index)
        return index


    @classmethod
    def get_single_result(cls, d={'id': 152, 'ancestors': [125311]}):
        r = compute(cls.batch_simple_cut(ids=d.get('ancestors')))
        r['id'] = d.get('id')
        return r
    
    @classmethod
    def get_train_test_df(cls, ancestors=[125311]):
        return get_train_test_df(cls.batch_simple_cut(ids=ancestors))    


# class AbstractDna(models.Model):
#     level = models.PositiveSmallIntegerField()
#     # section = models.ForeignKey(Section, on_delete=models.DO_NOTHING)
#     parent = models.ForeignKey('Dna', on_delete=models.DO_NOTHING, null=True)
#     pl_avg = models.FloatField(null=True)
#     pl_avg_date = models.FloatField(null=True)
#     atte = models.FloatField(null=True)
#     atte_date = models.FloatField(null=True)
#
#     pl_avg_test = models.FloatField(null=True)
#     pl_avg_date_test = models.FloatField(null=True)
#     atte_test = models.FloatField(null=True)
#     atte_date_test = models.FloatField(null=True)
#
#     # dead = models.BooleanField(default=False)
#     status = models.SmallIntegerField(default=0, choices=STATUS)
#     update_time = models.DateTimeField(auto_now=True)
#
#
#     class Meta:
#         abstract = True

    # class Meta:
    #     verbose_name_plural = "Dna"
    #
    #     indexes = [
    #         # models.Index(fields=['level', 'status', 'pl_avg_date']),
    #         models.Index(fields=['level', 'status', 'atte_date', 'pl_avg_date']),
    #         models.Index(fields=['section']),
    #         models.Index(fields=['parent']),
    #         models.Index(fields=['atte_date']),
    #         models.Index(fields=['status', 'update_time']),
    #         # models.Index(fields=['status', 'atte_date', 'pl_avg_date']),
    #         # models.Index(fields=['status', 'pl_avg_date_test']),
    #     ]
        

