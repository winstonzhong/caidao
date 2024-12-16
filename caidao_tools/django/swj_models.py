'''
Created on 2024年12月16日

@author: lenovo
'''
from django.db import models

# Create your models here.

class AbstractComputeTask(models.Model):
    name = models.CharField(max_length=10)
    data = models.BinaryField()

    class Meta:
        abstract = True

class AbstractMonoChain(models.Model):
    task_id = models.PositiveBigIntegerField()
    data = models.BinaryField()

    class Meta:
        abstract = True

class AbstractDnaFragment(models.Model):
    chain_id = models.PositiveBigIntegerField()
    up = models.FloatField(null=True)
    low = models.FloatField(null=True)
    attend = models.FloatField()
    pl3 = models.FloatField()
    pl5 = models.FloatField()
    
    class Meta:
        abstract = True
    