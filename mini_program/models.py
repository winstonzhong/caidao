from django.db import models

# Create your models here.
from caidao_tools.django.chat_models import AbstractOrderProduct


class Msg(models.Model):
    """用户消息"""

    from_user_name = models.CharField(max_length=50, verbose_name='发送方', default='')
    to_user_name = models.CharField(max_length=50, verbose_name='接收方', default='')
    text = models.TextField(verbose_name='消息', blank=True, null=True)
    pic_url = models.TextField(verbose_name='图片url', blank=True, null=True)
    media_url = models.TextField(verbose_name='图片url', blank=True, null=True)
    parent_id = models.SmallIntegerField(verbose_name="父记录", blank=True, null=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    reply = models.TextField(verbose_name='回复', blank=True, null=True)

