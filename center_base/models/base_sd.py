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


class AbstractTag(BaseModel):

    name = models.CharField(max_length=50, verbose_name='标签', default='')
    clout = models.IntegerField(verbose_name='热度', default=0)
    is_show = models.BooleanField(verbose_name='是否显示', default=True)
    is_top_level = models.BooleanField(verbose_name='是否顶级分类', default=False)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


    class Meta:
        abstract = True
        verbose_name_plural = "标签表"


class AbstractHairStyleDraft(BaseModel):

    url = models.ImageField(verbose_name='参考图URL', max_length=255)
    tpl_id = models.IntegerField(verbose_name='来源模板ID', default=0)
    mdeta_info = models.BinaryField(verbose_name='Meta信息')
    mask_url = models.ImageField(verbose_name='掩码图URL', max_length=255)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name_plural = "发型参考图"


class AbstractHairStyleImage(BaseModel):
    url = models.ImageField(verbose_name='参考图URL', max_length=255)
    draft_id = models.IntegerField(verbose_name='发型参考图ID', default=0)
    prompt = models.TextField(verbose_name='提示词', blank=True, null=True)
    negative_prompt = models.TextField(verbose_name='反向提示词', blank=True, null=True)
    base_module = models.CharField(max_length=100, verbose_name='基础模型', default='')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name_plural = "发型模板图"


class AbstractTagHairStyleImageRelation(BaseModel):

    tag_id = models.IntegerField(verbose_name='标签ID', default=0)
    image_id = models.IntegerField(verbose_name='发型模板图ID', default=0)
    rank = models.IntegerField(verbose_name='关系权重', default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name_plural = "标签发型模板图关系表"