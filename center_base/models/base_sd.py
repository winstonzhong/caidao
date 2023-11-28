'''
Created on 2023年11月16日

@author: lenovo
'''
from django.db import models

from caidao_tools.django.abstract import BaseModel, AbstractModel, StatusModel
from tool_file import get_url


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


    class Meta:
        abstract = True

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
    
    STATUS = ((STATUS_ORIGIN, "原始记录"),
              (STATUS_MASK, "掩码"),
              (STATUS_RMBGD, "去背景"),
              )
    
    url_from = models.URLField(verbose_name='来源url')
    fpath = models.FilePathField(verbose_name='路径')
    type_media = models.PositiveSmallIntegerField(default=TYPE_IMG, choices=TYPES, verbose_name='类别')
    status = models.PositiveSmallIntegerField(default=STATUS_ORIGIN, choices=STATUS, verbose_name='状态')
    meta = models.TextField(null=True, blank=True)
    
    class Meta:
        abstract = True

        indexes = [
            models.Index(fields=['url_from']),
        ]
    
    
    @property
    def url(self):
        return get_url(self.fpath)




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

# class AbstractImage(AbstractModel):
#     url_origin = models.URLField(null=True, blank=True)
#     img_fpath = models.ImageField(verbose_name='原图')
#     mask_fpath = models.ImageField(verbose_name='掩码')
#     result_fpath = models.ImageField(verbose_name='结果')
#     bin = models.BinaryField(verbose_name='Meta信息')
#
#     class Meta:
#         abstract = True


# class AbstractVideo(AbstractModel):
#     url_origin = models.URLField(null=True, blank=True)
#     video_fpath = models.FilePathField(verbose_name='原视频')
#     bin = models.BinaryField(verbose_name='Meta信息')        

# class AbstractImage

# class AbstractHairStyleDraft(AbstractModel):
#     img_fpath = models.ImageField(verbose_name='图像')
#     # tpl_id = models.IntegerField(verbose_name='来源模板ID', default=0)
#     url_origin = models.URLField(null=True, blank=True)
#     bin = models.BinaryField(verbose_name='Meta信息')
#     mask_fpath = models.ImageField(verbose_name='掩码')
#
#     class Meta:
#         abstract = True
#         verbose_name_plural = "发型参考图"
#         indexes = [
#             models.Index(fields=['url_origin',]),
#         ]


# class AbstractHairStyleImage(AbstractModel):
#     img_fpath = models.ImageField(verbose_name='图像')
#     draft_id = models.IntegerField(verbose_name='发型参考图ID', default=0)
#     prompt = models.TextField(verbose_name='提示词', blank=True, null=True)
#     negative_prompt = models.TextField(verbose_name='反向提示词', blank=True, null=True)
#     base_module = models.CharField(max_length=100, verbose_name='基础模型', default='')
#
#     class Meta:
#         abstract = True
#         verbose_name_plural = "发型模板图"


# class AbstractTagHairStyleImageRelation(AbstractModel):
#     tag_id = models.IntegerField(verbose_name='标签ID', default=0)
#     image_id = models.IntegerField(verbose_name='发型模板图ID', default=0)
#     rank = models.IntegerField(verbose_name='关系权重', default=0)
#
#     class Meta:
#         abstract = True
#         verbose_name_plural = "标签发型模板图关系表"

        
        
# class AbstractFrame(AbstractModel):
#     img_fpath = models.ImageField(verbose_name='图像')
#     # tpl_id = models.IntegerField(verbose_name='来源模板ID', default=0)
#     # bin = models.BinaryField(verbose_name='Meta信息')
#     mask_fpath = models.ImageField(verbose_name='掩码')

# class AbstractVideo(AbstractModel):
#     fpath = models.FilePathField(null=True, )        