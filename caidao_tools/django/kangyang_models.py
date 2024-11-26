from django.db import models

from caidao_tools.django.abstract import AbstractModel


class AbstractUser(models.Model):
    """用户"""
    MALE_CODE = 0
    FEMALE_CODE = 1
    GENDER_CHOICE = (
        (MALE_CODE, "男性"),
        (FEMALE_CODE, "女性"),
    )
    name = models.CharField(max_length=50, verbose_name='用户名称', default='')
    open_id = models.CharField(max_length=50, verbose_name='微信Open ID', blank=True, null=True, unique=True)
    head_img = models.TextField(verbose_name='用户头像', blank=True, null=True)
    gender = models.SmallIntegerField(verbose_name='性别', choices=GENDER_CHOICE, blank=True, null=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return '[{self.open_id}]{self.name}'.format(self=self)


class AbstractMsg(models.Model):
    """用户消息"""

    TYPES = (
        (0, '未知'),
        (1, '文本消息'),
        (2, '图片消息'),
        (3, '语音消息'),
        (4, '视频消息'),
        (5, '小程序卡片消息'),
        (6, '短视频消息'),
        (7, '坐标消息'),
        (8, '链接消息'),
        (8, '消息消息转发到客服'),
        (10, '事件推送消息'),
    )

    EVENTS = (
        (0, '无'),
        (1, '订阅'),
        (2, '取消订阅'),
        (3, '带场景值扫描事件'),
        (4, '上报地理位置'),
        (5, '点击菜单拉取消息'),
        (6, '点击菜单跳转链接'),
    )

    STATUS_INIT = 0
    STATUS = (
        (STATUS_INIT, '初始化'),
    )
    user_id = models.PositiveIntegerField(verbose_name="用户ID")
    type = models.SmallIntegerField(verbose_name="消息类型", choices=TYPES, default=0)
    event = models.SmallIntegerField(verbose_name="事件", choices=EVENTS, default=0)
    content = models.TextField(verbose_name='内容', default="")
    raw_data = models.TextField(verbose_name='源数据', default="")
    status = models.SmallIntegerField(verbose_name="状态", choices=STATUS, default=STATUS_INIT)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)


    class Meta:
        abstract = True
        
        indexes = [
            models.Index(fields=['status',]),
        ]
        