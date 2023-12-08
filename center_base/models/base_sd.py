'''
Created on 2023年11月16日

@author: lenovo
'''
import cv2
from django.db import models

from caidao_tools.django.abstract import BaseModel, AbstractModel, StatusModel
from tool_file import get_url
from django.utils.functional import cached_property


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


class AbstractTag(AbstractModel):
    name = models.CharField(max_length=50, verbose_name='标签', default='')
    clout = models.IntegerField(verbose_name='热度', default=0)
    is_show = models.BooleanField(verbose_name='是否显示', default=True)
    is_top_level = models.BooleanField(verbose_name='是否顶级分类', default=False)
    repeat = models.PositiveIntegerField(default=0)
    similarity = models.FloatField(default=0)
    disabled = models.BooleanField(default=False)
    

    class Meta:
        abstract = True

        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['disabled']),
        ]


class AbstractMedia(AbstractModel):
    TYPE_IMG = 0
    TYPE_VIDEO = 1
    
    
    TYPES = (
        (TYPE_IMG,'图片'),
        (TYPE_VIDEO,'视频'),
        )
    
    STATUS_ORIGIN = 0
    STATUS_MASK = 1
    STATUS_RMBGD = 2
    STATUS_TRANS = 3
    
    STATUS_META_EDITED = 10
    
    STATUS = ((STATUS_ORIGIN, "原始记录"),
              (STATUS_MASK, "掩码"),
              (STATUS_RMBGD, "无背景"),
              (STATUS_TRANS, "已迁移"),
              (STATUS_META_EDITED, "已编辑"),
              )
    
    url_from = models.URLField(verbose_name='来源url')
    # fpath = models.FilePathField(verbose_name='路径')
    file = models.FileField(upload_to=r'V:\static\uploaded', null=True, blank=True)
    type_media = models.PositiveSmallIntegerField(default=TYPE_IMG, choices=TYPES, verbose_name='类别')
    status = models.PositiveSmallIntegerField(default=STATUS_ORIGIN, choices=STATUS, verbose_name='状态')
    meta = models.TextField(null=True, blank=True)
    prompt = models.TextField(null=True, blank=True)
    negativePrompt = models.TextField(null=True, blank=True)
    base_module = models.CharField(max_length=100, verbose_name='基础模型', null=True, blank=True)
    
    class Meta:
        abstract = True

    
    @cached_property
    def url(self):
        return get_url(self.file.path)
    
    @cached_property
    def img(self):
        return cv2.imread(self.file.path)




class AbstractFrame(AbstractMedia):
    index = models.PositiveIntegerField()

    class Meta:
        abstract = True


class AbstractRelation(AbstractModel):
    tag_id = models.IntegerField(verbose_name='标签ID', default=0)
    meida_id = models.IntegerField(verbose_name='发型模板图ID', default=0)
    rank = models.IntegerField(verbose_name='关系权重', default=0)

    class Meta:
        abstract = True
