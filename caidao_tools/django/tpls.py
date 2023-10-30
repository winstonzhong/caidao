'''
Created on 2023 Oct 25

@author: Winston
'''
from django.db import models

from caidao_tools.django.abstract import StatusModel, FullTextField, BaseModel


class AbstractWord(BaseModel):
    MAX_LEN_EN = 50
    MAX_LEN_CN = 100
    en = models.CharField(max_length=MAX_LEN_EN)
    cn = models.CharField(max_length=MAX_LEN_CN)
    
    

    class Meta:
        abstract = True

class AbstractTemplateModel(StatusModel):
    mid = models.PositiveBigIntegerField(verbose_name='csite模型id')
    vid = models.PositiveBigIntegerField(verbose_name='csite模型vid')
    tid = models.PositiveBigIntegerField()
    bin = models.BinaryField()
    meta_info = FullTextField(null=True, blank=True)

    class Meta:
        abstract = True
