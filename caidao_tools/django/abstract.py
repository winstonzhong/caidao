"""
Created on 2022年5月1日

@author: Administrator
"""

import traceback
from django.db import models
from django.forms import model_to_dict

from evovle.helper_store import compute, get_train_test_df, compute_group
from helper_net import retry
from caidao_tools.django.tool_django import get_filters
import time
from tool_time import convert_time_description_to_seconds
from django.utils import timezone
import datetime

from django.db.models import F, ExpressionWrapper, Value
from django.db.models.fields import DurationField
from tool_time import shanghai_time_now
from .tool_task import calculate_rtn
from tool_static import 存储字典到文件
import requests
import json



NEW_RECORD = 0
DOWNLOADED_RECORD = 1
PRODUCED_RECORD = 2
UPLOADED_RECORD = 3
ROOT_RECORD = 4
COMPUTEED_RECORD = 5
TRANSLATED_RECORD = 6
EMPTY_RECORD = 400
DEAD_RECORD = 401
ABNORMAL_RECORD = 402
FAILED_TRANS_RECORD = 403


STATUS = (
    (NEW_RECORD, "新记录"),
    (DOWNLOADED_RECORD, "已下载"),
    (PRODUCED_RECORD, "已制作"),
    (UPLOADED_RECORD, "已上传"),
    (ROOT_RECORD, "根记录"),
    (COMPUTEED_RECORD, "已计算"),
    (TRANSLATED_RECORD, "已翻译"),
    (EMPTY_RECORD, "空记录"),
    (DEAD_RECORD, "坏记录"),
    (ABNORMAL_RECORD, "异常记录"),
    (FAILED_TRANS_RECORD, "翻译失败记录"),
)


class FullTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        kwargs["null"] = True
        kwargs["blank"] = True
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return "fts"

    def get_prep_value(self, value):
        return value


class Base(object):
    @classmethod
    def get_fields(cls):
        return [x.name for x in cls._meta.fields if x.name != "id"]


class BaseModel(models.Model):
    FIELDS = None

    @classmethod
    def get_fields(cls):
        if not cls.FIELDS:
            cls.FIELDS = list(map(lambda x: x.get_attname(), cls._meta.fields))
        return cls.FIELDS

    @classmethod
    def has_field(cls, name):
        return name in cls.get_fields()

    @classmethod
    def get_fields_without_id(cls):
        return filter(lambda x: x != "id", cls.get_fields())

    @retry(10, True)
    def save_safe(self):
        self.save()
        return self

    @classmethod
    def get_all(cls):
        start = 0
        while 1:
            o = cls.objects.filter(id__gt=start).first()
            if o is None:
                break
            yield o
            start = o.id

    @classmethod
    def get_filters(cls, **k):
        return get_filters(cls.get_fields(), **k)

    class Meta:
        abstract = True


class AbstractModel(BaseModel):
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True

    @classmethod
    def 得到一条任务(cls, 字段名称):
        return (
            cls.objects.filter(**{f"{字段名称}_完成": False})
            .order_by("create_time")
            .first()
        )

    @classmethod
    def 得到一条任务json(cls, 字段名称):
        obj = cls.得到一条任务(字段名称)
        return obj.json if obj is not None else {}

    def 设置制作结果(self, name, value):
        setattr(self, f"{name}", value)
        setattr(self, f"{name}_完成", True)
        self.save()

    @property
    def json(self):
        return model_to_dict(self)

class 抽象任务(AbstractModel):

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["update_time"]),
        ]

    @classmethod
    def 得到日志类(cls):
        raise NotImplementedError

    def 执行任务(self):
        raise NotImplementedError

    @classmethod
    def 得到当前待执行的任务(cls):
        raise NotImplementedError

    @classmethod
    def 单步执行(cls):
        obj = cls.得到当前待执行的任务()
        if obj is not None:
            try:
                obj.执行任务()
            except Exception:
                log = cls.得到日志类()
                log.异常日志 = traceback.format_exc()
                print(log.异常日志)
                log.save()


class 抽象定时任务(BaseModel):
    类名 = models.CharField(max_length=50)
    静态函数 =  models.CharField(max_length=50, default="单步执行")
    任务描述 = models.CharField(max_length=200, null=True, blank=True)
    定时表达式 = models.CharField(max_length=50, default="every 1 second")
    间隔秒 = models.IntegerField(null=True, blank=True)
    设定时间 = models.DateTimeField()
    一次执行 = models.BooleanField(default=False)
    激活 = models.BooleanField(default=True)
    update_time = models.DateTimeField(verbose_name="更新时间", null=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["激活", "update_time"]),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def save(self, *args, **kwargs):
        if self.一次执行:
            self.激活 = False
        else:
            self.update_time = calculate_rtn(self.update_time, self.间隔秒, shanghai_time_now())
            print(self.update_time)
        super().save(*args, **kwargs)

    @property
    def 全局命名空间(self):
        raise NotImplementedError

    @property
    def 执行类(self):
        return eval(self.类名, self.全局命名空间)
        # return eval(self.类名, globals(), locals())

    @property
    def 执行类静态函数(self):
        return getattr(self.执行类, self.静态函数)

    @classmethod
    def 得到所有待执行的任务(cls):
        queryset = cls.objects.filter(
            激活=True,
            update_time__lte=timezone.now() - ExpressionWrapper(
                Value(datetime.timedelta(seconds=1)) * F('间隔秒'),
                output_field=DurationField()
            )
        )
        return queryset

    @classmethod
    def 执行所有定时任务(cls, 每轮间隔秒数=1):
        while 1:
            q = cls.得到所有待执行的任务().order_by("update_time")
            for obj in q:
                obj.执行类静态函数()
            time.sleep(每轮间隔秒数)

class 抽象定时任务日志(AbstractModel):
    定时任务_id = models.BigIntegerField()
    数据_id = models.BigIntegerField(null=True)
    异常日志 = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["定时任务_id", "数据_id"]),
        ]

class StatusModel(AbstractModel):
    status = models.SmallIntegerField(default=NEW_RECORD, choices=STATUS)

    class Meta:
        abstract = True


class BaseSection(object):
    result_cache = {}

    @property
    def direction_display(self):
        return ">=" if self.direction else "<="

    def __str__(self):
        return "{self.single_chain}{self.direction_display}{self.point}".format(
            self=self
        )

    def simple_cut(self, is_first=False):
        s = self.single_chain.s
        if self.direction:
            s = s[s >= self.point]
        else:
            s = s[s <= self.point]
        if is_first:
            s.sort_values(ascending=not self.direction, inplace=True)
        return s.index

    @classmethod
    def do_simple_cut(cls, oid, is_first=False):
        obj = cls.objects.get(id=oid)
        return obj.simple_cut(is_first)

    @classmethod
    def batch_simple_cut_parent(cls, ids):
        ids.reverse()
        key = ",".join([str(x) for x in ids])
        if cls.result_cache.get(key) is None:
            index = cls.do_simple_cut(ids[0], is_first=True)
            for oid in ids[1:]:
                tmp = cls.do_simple_cut(oid, is_first=False)
                index = index.intersection(tmp)
            cls.result_cache.clear()
            cls.result_cache[key] = index
        return cls.result_cache.get(key)

    @classmethod
    def batch_simple_cut(cls, ids):
        head, root = ids[0], ids[1:]

        if root:
            index_root = cls.batch_simple_cut_parent(root)
            index = cls.do_simple_cut(head, is_first=False)
            index = index_root.intersection(index)
        else:
            index = cls.do_simple_cut(head, is_first=False)
        return index

    @classmethod
    def get_single_result(cls, d={"id": 152, "ancestors": [125311]}):
        r = compute(cls.batch_simple_cut(ids=d.get("ancestors")))
        r["id"] = d.get("id")
        return r

    @classmethod
    def get_train_test_df(cls, ancestors=[125311]):
        return get_train_test_df(cls.batch_simple_cut(ids=ancestors))


class AbstractSection(BaseSection, models.Model):
    sid = models.PositiveIntegerField()
    direction = models.BooleanField(null=True)
    point = models.FloatField()

    class Meta:
        abstract = True

        indexes = [
            models.Index(fields=["sid", "direction"]),
        ]

    @property
    def single_chain(self):
        raise NotImplementedError

    def simple_cut(self):
        s = self.single_chain.s
        if self.direction:
            s = s[s >= self.point]
        else:
            s = s[s <= self.point]
        return s.index

    @classmethod
    def do_simple_cut(cls, oid):
        return cls.objects.get(id=oid).simple_cut()

    @classmethod
    def batch_simple_cut_parent(cls, ids):
        key = ",".join([str(x) for x in ids])
        if cls.result_cache.get(key) is None:
            index = cls.do_simple_cut(ids[0])
            for oid in ids[1:]:
                index = index.intersection(cls.do_simple_cut(oid))
            cls.result_cache.clear()
            cls.result_cache[key] = index
        return cls.result_cache.get(key)

    @classmethod
    def batch_simple_cut(cls, ids):
        head, root = ids[-1], ids[:-1]

        if root:
            index_root = cls.batch_simple_cut_parent(root)
            index = cls.do_simple_cut(head)
            index = index_root.intersection(index)
        else:
            index = cls.do_simple_cut(head)
        return index

    @classmethod
    def get_single_result(cls, d={"id": 152, "ancestors": [125311]}):
        r = compute_group(cls.batch_simple_cut(ids=d.get("ancestors")))
        r["id"] = d.get("id")
        return r


class AbstractDna(models.Model):
    DNA_STATUS = (
        (NEW_RECORD, "新"),
        (PRODUCED_RECORD, "已计算"),
        (DEAD_RECORD, "停止计算"),
        (ROOT_RECORD, "根节点"),
    )

    section_id = models.PositiveIntegerField()

    parent_id = models.PositiveBigIntegerField(null=True)

    pl = models.SmallIntegerField(null=True)

    atte = models.PositiveSmallIntegerField(null=True)

    status = models.SmallIntegerField(default=0, choices=DNA_STATUS)

    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

        indexes = [
            models.Index(fields=["status", "atte", "pl"]),
            models.Index(fields=["status", "update_time"]),
            models.Index(fields=["parent_id", "status"]),
        ]

    cache_section_ids = {}

    cache_singlechain_ids = {}

    @property
    def singlechain_id(self):
        if self.section_id not in self.cache_singlechain_ids:
            self.cache_singlechain_ids[self.section_id] = self.section.sid
        return self.cache_singlechain_ids.get(self.section_id)

    @property
    def parent(self):
        return self.__class__.objects.get(id=self.parent_id) if self.parent_id else None

    def set_cache_section_ids(self):
        self.cache_section_ids[self.id] = self.section_ids_clean

    @property
    def section_ids(self):
        rtn = self.cache_section_ids.get(self.id, None)
        if rtn is not None:
            return rtn

        if self.parent_id is None:
            return [self.section_id]

        return self.parent.section_ids + [self.section_id]

    @property
    def section_ids2(self):
        parent = self.parent
        if parent is not None:
            for x in parent.section_ids2:
                yield x
        yield self.section_id

    @property
    def section(self):
        raise NotImplementedError

    @property
    def dict(self):
        return {
            "id": self.id,
            "ancestors": list(self.section_ids),
        }

    @classmethod
    def has_tasks(cls):
        return len(cls.redis_conn.lrange(cls.cache_key, 0, 0)) == 1

    @classmethod
    def get_tasks_count(cls):
        return len(cls.redis_conn.lrange(cls.cache_key, 0, 1000))

    @classmethod
    def clear_tasks(cls):
        cls.redis_conn.delete(cls.cache_key)

    @classmethod
    def book(cls):
        return cls.redis_conn.rpop(cls.cache_key)

# {
#   "output": "\n\n你是一个贴标签的专家，你现在需要使用如下标签“儿童”去匹配输入内容，判断内容是否涉及儿童相关主题（包括但不限于小孩、孩子、幼儿、少年、青少年、小朋友、未成年人等近义词）。请严格按以下规则输出JSON：若相关则{'标签匹配结果':'是'}，否则{'标签匹配结果':'否'}。仅输出结果，不要解释。"
# }

# {
#   "output": "你是一个贴标签的专家，你现在需要使用如下标签“儿童”去匹配输入内容，判断内容是否与该标签相关。标签“儿童”的近义词包括但不限于：小孩、孩子、幼儿、少年、小朋友等。请根据输入内容判断是否匹配该标签或其近义词，并以JSON格式输出结果。如果是，输出{'标签匹配结果':'是'}；如果否，输出{'标签匹配结果':'否'}。"
# }
class 抽象原子标签(AbstractModel):
    名称 = models.CharField(max_length=100)
    提示词 = models.CharField(blank=True, null=True, max_length=255)
    
    class Meta:
        abstract = True


    @classmethod
    def 初始化家医智驾标签(cls):
        x = [
            ('儿童','青少年','青年','中年','老年'),
            ('体重不足', '超重', '肥胖'),
            ('男性','女性'),
            ('哮喘','高血压', '心脏病', '糖尿病')
        ]
        for y in x:
            for z in y:
                cls.objects.get_or_create(名称=z)

    @classmethod
    def 生成提示词的提示词(cls):
        return '''我目前有一个词汇标签：“{名称}”，我希望使用这个标签：“{名称}”去匹配一段文字，这个匹配能够输出该段内容是否匹配成功的结果。
    通常这个过程是通过大模型提示词完成的，我希望你能写出这个标签匹配过程的提示词：
1，提示词和“{名称}”这个标签相关，是否也能匹配它的各类近义词，并在提示词中举例一些近义词，同时也强调不限于这些近义词。
2，界定输出的格式，为json格式。{{'标签匹配结果':‘是’}}
3, 如果结果是否，则JSON格式为：{{'标签匹配结果':‘否’}}
4, 请以如下开头编写：你是一个贴标签的专家，你现在需要使用如下标签“{名称}”去匹配输入内容，。。。。
5， 请直接输出结果，不要再加前后说明性解释和其他内容。

'''

    @classmethod
    def 未生成提示词的提示词的字典(cls):
        # q = cls.objects.filter(提示词__isnull=True)
        q = cls.objects.filter()
        d = {'名称': [x.名称 for x in q]}
        d['模版'] = cls.生成提示词的提示词()
        return d

    @classmethod
    def 生成未生成提示词的提示词的字典链接(cls):
        return 存储字典到文件(cls.未生成提示词的提示词的字典(), '.json')

    @classmethod
    def 读取并更新结果(cls, url):
        d = requests.get(url).json()
        for k, v in d.items():
            print(f'{k}')
            cls.objects.filter(名称=k).update(提示词=v)

    @classmethod
    def 得到打标签字典链接(cls):
        return 存储字典到文件(cls.打标签字典(), '.json')
    
    