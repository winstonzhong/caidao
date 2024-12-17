'''
Created on 2024年12月16日

@author: lenovo
'''
from django.db import models

# Create your models here.

class AbstractComputeTask(models.Model):
    name = models.CharField(max_length=255)
    data = models.BinaryField()
    total = models.PositiveSmallIntegerField(null=True)
    pl = models.FloatField(null=True)

    class Meta:
        abstract = True

class AbstractMonoChain(models.Model):
    task_id = models.PositiveBigIntegerField()
    name = models.CharField(max_length=20)
    data = models.BinaryField()
    fraged = models.BooleanField(default=False)

    class Meta:
        abstract = True

class AbstractDnaFragment(models.Model):
    task_id = models.PositiveBigIntegerField(null=True)
    chain_id = models.PositiveBigIntegerField()
    up = models.FloatField(null=True)
    low = models.FloatField(null=True)
    computed = models.BooleanField(default=False)
    
    class Meta:
        abstract = True

class AbstractDnaStrand(models.Model):
    task_id = models.PositiveBigIntegerField(null=True)
    fragment_ids = models.TextField(null=True)
    attend = models.FloatField(null=True)
    pl = models.FloatField(null=True)
    pl_cut = models.FloatField(null=True)
    level = models.PositiveSmallIntegerField(default=0)
    expanded = models.BooleanField(default=False)
    key = models.CharField(max_length=64, null=True)

    class Meta:
        abstract = True
