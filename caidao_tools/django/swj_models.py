'''
Created on 2024年12月16日

@author: lenovo
'''
import hashlib

from django.db import models

from helper_cmd import CmdProgress


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
    expanded = models.SmallIntegerField(default=0)
    key = models.CharField(max_length=64, null=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @classmethod
    def do_compute(cls, task, i):
        if not i.empty:
            df = task.df
            tmp = df.loc[i]
            attend = tmp.dantian.drop_duplicates().count() / task.total
            pl = tmp.pl3.mean()
            tmp2 = df.loc[~df.index.isin(i)]
            pl_cut = tmp2.pl3.mean()
        else:
            attend = 0
            pl = -1
            pl_cut = 0
        return {'attend':attend,
                'pl':pl,
                'pl_cut':pl_cut,
                }
    
    @classmethod
    def get_all_level0(cls):
        return cls.objects.filter(level=0)
    
    @classmethod
    def has_key(cls, key):
        return cls.objects.filter(key=key).first() is not None
