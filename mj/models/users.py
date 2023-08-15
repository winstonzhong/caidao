
from django.db import models

# Create your models here.


class AbstractPackage(models.Model):
    name = models.CharField(max_length=50, verbose_name='套餐名称', default='')
    price = models.DecimalField(verbose_name='价格', max_digits=6, decimal_places=2, default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

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
    name = models.CharField(max_length=50, verbose_name='用户名称', default='')
    head_img = models.TextField(verbose_name='用户头像', default='')
    group_id = models.IntegerField(verbose_name="群组ID", blank=True, null=True)
    sn = models.CharField(max_length=10, verbose_name='Sn', default='', unique=True)
    package_id = models.IntegerField(verbose_name="套餐ID", blank=True, null=True)
    remark = models.TextField(verbose_name='备注', blank=True, null=True)
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

