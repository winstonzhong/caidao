from django.db import models


class AbstractVideo(models.Model):
    """视频"""
    fpath = models.CharField(max_length=300, verbose_name='文件路径', default='')
    fpath_md5 = models.CharField(max_length=32, verbose_name='文件路径md5', default='', db_index=True)
    name = models.CharField(max_length=50, verbose_name='文件名称', default='')
    srt = models.TextField(verbose_name='视频字幕', null=True, blank=True)
    remark = models.TextField(verbose_name='备注', null=True, blank=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            # models.Index(fields=['fpath_md5']),
        ]


class AbstractVideoFragment(models.Model):
    """视频片段"""
    seq = models.IntegerField(verbose_name='片段序号', default=0)
    video_id = models.PositiveIntegerField(verbose_name="视频ID")
    fpath = models.CharField(max_length=100, verbose_name='文件路径', default='')
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
        ]
