'''
Created on 2023年11月16日

@author: lenovo
'''
from caidao_tools.django.abstract import BaseModel
from django.db import models


class AbstractHeadFace(BaseModel):
    NEW = -1
    DETECTED = 0
    REMARKED = 1
    FEMALE = 100
    MALE = 101
    NO_WHOLE_FACE = 400
    SIDE_FACE = 401
    BAD = 402
    FAKE = 403
    MULTIPLE = 404
    GLASSES = 405
    OTHERS = 406
    
    STATUS = (
        (NEW, "新"),
        (DETECTED, "已检测"),
        (REMARKED, "已标注"),
        (FEMALE, "女"),
        (MALE, "男"),
        (NO_WHOLE_FACE, "脸部不全"),
        (SIDE_FACE, "侧脸"),
        (BAD, "错误"),
        (FAKE, "疑似遮挡"),
        (MULTIPLE, "多人"),
        (GLASSES, "带眼镜"),
        (OTHERS, "不明性别"),
        
        )

    gender = models.SmallIntegerField(choices=STATUS, default=NEW, verbose_name='性别')
    size = models.PositiveBigIntegerField(default=0)
    uri = models.URLField(verbose_name="图片uri")
    left = models.SmallIntegerField(null=True) 
    right = models.SmallIntegerField(null=True)
    top = models.SmallIntegerField(null=True) 
    bottom = models.SmallIntegerField(null=True)
    remark = models.TextField(null=True)
    points = models.BinaryField(null=True)
    
    class Meta:
        abstract = True
        verbose_name_plural = "头脸"

        indexes = [
            models.Index(fields=['uri', 'size']),
            models.Index(fields=['uri', 'left', 'right', 'top', 'bottom']),
        ]
