'''
Created on 2022年5月1日

@author: Administrator
'''
from django.db import models

class AbstractModel(models.Model):
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
