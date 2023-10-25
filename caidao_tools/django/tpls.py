'''
Created on 2023 Oct 25

@author: Winston
'''
from django.db import models

from caidao_tools.django.abstract import StatusModel, FullTextField


class AbstractTemplateModel(StatusModel):
    mid = models.PositiveBigIntegerField(verbose_name='模型id')
    tid = models.PositiveBigIntegerField(verbose_name='tid of csite')
    bin = models.BinaryField()
    meta_info = FullTextField(null=True, blank=True)

    class Meta:
        abstract = True
