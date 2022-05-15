'''
Created on 2022年5月1日

@author: Administrator
'''
from django.db import models

class BaseModel(models.Model):
    FIELDS = None
    @classmethod
    def get_fields(cls):
        if not cls.FIELDS:
            cls.FIELDS = list(map(lambda x: x.get_attname(), cls._meta.fields))
        return cls.FIELDS
    class Meta:
        abstract = True

class AbstractModel(BaseModel):
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True

    
    
