from django.db import models
from caidao_tools.django.abstract import AbstractModel


class AppAbstract(AbstractModel):
    name = models.CharField(verbose_name="应用名称", max_length=20, default='', unique=True)
    exchange_ratio = models.IntegerField(verbose_name="兑换比", default=0)

    class Meta:
        abstract = True


class AppIncomeAbstract(AbstractModel):
    app_id = models.IntegerField(verbose_name="应用ID", default=0)
    app_name = models.CharField(verbose_name="应用名称", max_length=20, default='')
    device = models.CharField(verbose_name="设备名称", max_length=20, default='')
    create_date = models.DateField(verbose_name="创建日期", blank=True, null=True)
    coin = models.DecimalField(verbose_name="金币数量", max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(verbose_name="余额", max_digits=6, decimal_places=2, default=0)
    withdraw = models.DecimalField(verbose_name="提现金额", max_digits=6, decimal_places=2, default=0)
    exchange_ratio = models.IntegerField(verbose_name="兑换比", default=0)


    class Meta:
        abstract = True