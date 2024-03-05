
from django.db import models

# Create your models here.
from caidao_tools.django.abstract import AbstractModel


class AbstractPackage(models.Model):
    name = models.CharField(max_length=50, verbose_name='套餐名称', default='')
    price = models.DecimalField(verbose_name='价格', max_digits=6, decimal_places=2, default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    remark = models.TextField(verbose_name='备注', blank=True, null=True)

    class Meta:
        abstract = True


class AbstractSn(models.Model):
    value = models.CharField(max_length=5, verbose_name='Sn', blank=True, null=True, unique=True)
    user_id = models.IntegerField(verbose_name="用户ID", blank=True, null=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True



class AbstractUser(models.Model):
    """用户"""
    # name = models.CharField(max_length=50, verbose_name='用户名称', default='')
    # head_img = models.TextField(verbose_name='用户头像', default='')
    # group_id = models.IntegerField(verbose_name="群组ID", blank=True, null=True)
    # sn = models.CharField(max_length=10, verbose_name='Sn', default='', unique=True)
    # package_id = models.IntegerField(verbose_name="套餐ID", blank=True, null=True)
    # remark = models.TextField(verbose_name='备注', blank=True, null=True)
    # expired_at = models.DateTimeField(verbose_name='过期时间', null=True)
    # updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    # created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    name = models.CharField(max_length=50, verbose_name='昵称', blank=True, null=True)
    icon = models.ImageField(blank=True, null=True, verbose_name='头像',upload_to="icons")
    qq_main = models.CharField(max_length=50, verbose_name='用户主qq号', blank=True, null=True)
    qq_main_name = models.CharField(max_length=50, verbose_name='用户主qq号昵称', blank=True, null=True)
    wx_main = models.CharField(max_length=50, verbose_name='用户主微信号', blank=True, null=True)
    wx_main_name = models.CharField(max_length=50, verbose_name='用户主微信号昵称', blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name='手机号', blank=True, null=True)
    sn = models.CharField(max_length=32, verbose_name='Sn', default='', unique=True)
    md5 = models.CharField(max_length=32, verbose_name='Sn md5', null=True)
    remark = models.TextField(verbose_name='备注', blank=True, null=True)
    real = models.BooleanField(default=False, verbose_name='真实客户')
    expired_at = models.DateTimeField(verbose_name='过期时间', null=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractGroup(models.Model):
    """群组"""
    name = models.CharField(max_length=50, verbose_name='群名称', default='')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractPurchase(AbstractModel):
    user = models.PositiveIntegerField()
    package = models.PositiveIntegerField()
    icon = models.ImageField(verbose_name='支付截图',upload_to="purchase")
    num = models.PositiveSmallIntegerField(verbose_name='购买月数', default=1)
    amount = models.DecimalField(verbose_name='总金额', max_digits=6, decimal_places=2, default=0)
    expire_date = models.DateTimeField(verbose_name='到期时间', null=True, blank=True)

    class Meta:
        abstract = True