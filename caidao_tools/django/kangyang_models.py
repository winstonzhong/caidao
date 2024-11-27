from django.db import models

from caidao_tools.django.abstract import AbstractModel
from caidao_tools.django.storage import MyStorage


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
    data = models.TextField(verbose_name='用户授权信息', null=True, blank=True)
    phone = models.CharField(verbose_name='手机号', max_length=20, blank=True, null=True)
    email = models.CharField(verbose_name='邮箱地址', max_length=50, blank=True, null=True)
    birthday = models.DateTimeField(verbose_name='出生日期', null=True, blank=True)

    class Meta:
        abstract = True
        indexes = []

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
    STATUS_SYNCED = 200
    STATUS = (
        (STATUS_INIT, '初始化'),
        (STATUS_SYNCED, '已同步'),
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
            models.Index(fields=['status']),
        ]


class AbstractAddress(models.Model):
    user_id = models.PositiveIntegerField(verbose_name='用户ID', blank=True, null=True)
    name = models.CharField(verbose_name='收货人姓名', max_length=64, null=True, blank=True)
    phone = models.CharField(verbose_name='手机号', max_length=20, blank=True, null=True)
    area = models.CharField(verbose_name='省市地区', max_length=100, blank=True, null=True)
    address = models.CharField(verbose_name='详细地址', max_length=200, blank=True, null=True)
    is_default = models.BooleanField(verbose_name='是否默认地址', default=False)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = []


class AbstractProduct(models.Model):
    STATUS_FOR_SALE = 0
    STATUS_SOLD_OUT = 1
    STATUS_DELETE = 2
    TYPE_CHOICE = (
        (STATUS_FOR_SALE, "在售"),
        (STATUS_SOLD_OUT, "下架"),
        (STATUS_DELETE, "删除"),
    )
    name = models.CharField(verbose_name='产品描述', max_length=200, null=True, blank=True)
    price = models.DecimalField(verbose_name='价格', max_digits=6, decimal_places=2, default=0)
    stock = models.IntegerField(verbose_name='库存', default=0)
    weight = models.IntegerField(verbose_name='权重', default=0)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    enabled = models.BooleanField(verbose_name='可用', default=True)
    style = models.CharField(verbose_name='款式', max_length=200, null=True, blank=True)
    json_data = models.TextField(verbose_name='json数据', null=True, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['stock']),
        ]


class AbstractProductImg(models.Model):
    TYPE_SLIDE_SHOW = 0
    TYPE_DETAIL = 1
    TYPE_CHOICE = (
        (TYPE_SLIDE_SHOW, "轮播图"),
        (TYPE_DETAIL, "详情图片"),
    )
    product_id = models.PositiveIntegerField(verbose_name='产品ID', blank=True, null=True)
    img = models.FileField(verbose_name='图片', storage=MyStorage, null=True, blank=True)
    # img = models.FileField(verbose_name='图片', null=True, blank=True)
    seq = models.IntegerField(verbose_name='序号', default=0)
    type = models.SmallIntegerField(verbose_name='类型', choices=TYPE_CHOICE, default=TYPE_SLIDE_SHOW)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    enabled = models.BooleanField(verbose_name='可用', default=True)

    class Meta:
        abstract = True
        indexes = []


class AbstractOrder(models.Model):
    STATUS_INIT = 0
    STATUS_WAIT_PAID = 1
    STATUS_WAIT_DELIVER = 2
    STATUS_WAIT_RECEIVE = 3
    STATUS_WAIT_COMPLETE = 4
    TYPE_CHOICE = (
        (STATUS_INIT, "待付款"),
        (STATUS_WAIT_PAID, "已付款"),
        (STATUS_WAIT_DELIVER, "待发货"),
        (STATUS_WAIT_RECEIVE, "待收货"),
        (STATUS_WAIT_COMPLETE, "已完成"),
    )
    order_sn = models.CharField(verbose_name='订单编号', max_length=40, null=True, blank=True)
    user_id = models.PositiveIntegerField(verbose_name='用户ID', blank=True, null=True)
    amount = models.DecimalField(verbose_name='订单金额', max_digits=6, decimal_places=2, default=0)
    address = models.CharField(verbose_name='详细地址', max_length=200, blank=True, null=True)
    status = models.SmallIntegerField(verbose_name='状态', choices=TYPE_CHOICE, default=STATUS_INIT)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['order_sn']),
            models.Index(fields=['status']),
        ]


class AbstractOrderDetail(models.Model):
    order_id = models.PositiveIntegerField(verbose_name='产品ID', blank=True, null=True)
    product_name = models.CharField(verbose_name='产品描述', max_length=200, default='')
    product_img = models.TextField(verbose_name='图片', max_length=200, null=True, blank=True)
    quantity = models.IntegerField(verbose_name='数量', default=1)
    price = models.DecimalField(verbose_name='价格', max_digits=6, decimal_places=2, default=0)
    product_id = models.PositiveIntegerField(verbose_name='产品ID', blank=True, null=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['order_id']),
        ]
