'''
Created on 2022年5月1日

@author: Administrator
'''
from django.db import models

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

class StatusModel(AbstractModel):
    status = models.SmallIntegerField(default=NEW_RECORD, choices=STATUS)

    class Meta:
        abstract = True
    
