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

from django.utils import timezone
import datetime

from django.db.models import F, ExpressionWrapper, Value, Q
from django.db.models.fields import DurationField
from tool_time import shanghai_time_now
from .tool_task import calculate_rtn
from tool_remote_orm_model import RemoteModel
from urllib.parse import urlencode
import requests
import copy
from django.db import OperationalError

from django.db.models.query_utils import Q


import json

import helper_task_redis

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


class 抽象缓存任务(object):
    @property
    def 任务队列名称(self):
        raise NotImplementedError

    @property
    def 下一个任务数据(self):
        from helper_task_redis import get_REDIS_CONN

        _, task_data = get_REDIS_CONN().blpop(self.任务队列名称)
        if task_data:
            try:
                return json.loads(task_data)
            except json.JSONDecodeError:
                print("不是JSON格式")

    @property
    def 下一个任务对象(self):
        raise NotImplementedError


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

    @property
    def json(self):
        if not hasattr(self, "_json"):
            return model_to_dict(self)
        return self._json

    @json.setter
    def json(self, value):
        self._json = value

    @classmethod
    def get_fields(cls):
        if not cls.FIELDS:
            cls.FIELDS = list(map(lambda x: x.get_attname(), cls._meta.fields))
        return cls.FIELDS

    @classmethod
    def 是否数据库字段(cls, name, fields):
        name = name.split("__", maxsplit=1)[0]
        return name in fields or f"{name}_id" in fields

    @classmethod
    def 筛选出数据库字段(cls, d):
        fields = cls.get_fields()
        # print(fields)
        # print(d)
        rtn = {k: v for k, v in d.items() if cls.是否数据库字段(k, fields)}
        print('rtn', rtn)
        return rtn

    @classmethod
    def has_field(cls, name):
        return name in cls.get_fields()

    @classmethod
    def get_fields_without_id(cls):
        return filter(lambda x: x != "id", cls.get_fields())

    @classmethod
    def get_field_type(cls, field_name):
        return cls._meta.get_field(field_name).get_internal_type()

    def clone(self):
        cls = self.__class__
        d = model_to_dict(self)
        data = {}
        for k, v in d.items():
            if k == "id":
                continue
            if cls.get_field_type(k) == "ForeignKey":
                k = f"{k}_id"
            data[k] = v
        return cls(**data).save()

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


class 抽象任务数据(BaseModel):
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    cnt_saved = models.IntegerField(verbose_name="保存次数", default=0)
    processing = models.BooleanField(verbose_name="正在处理", default=False)
    done = models.BooleanField(verbose_name="已经完成", default=False)

    class Meta:
        abstract = True
        indexes = [
            models.Index(
                fields=[
                    # "done",
                    "processing",
                    "update_time",
                ]
            ),
        ]

    # @classmethod
    # def 得到结果处理函数(cls, pk=None):
    #     if pk is not None:
    #         return getattr(cls.objects.get(pk=pk), "处理结果")
    #     return getattr(cls, "处理结果类函数")

    @classmethod
    def 得到结果处理函数(cls, **k):
        if k:
            obj = cls.objects.filter(**k).first()
            assert obj is not None, f"{cls} 没有找到 {k}"
            return getattr(obj, "处理结果")
        return getattr(cls, "处理结果类函数")

    @classmethod
    def 得到最大队列容量(cls):
        raise NotImplementedError

    @classmethod
    def 得到队列名称(cls):
        raise NotImplementedError

    def 写入任务队列(self, 队列名称, 数据, 队列容量=None, 设备相关=False):

        队列名称 = 队列名称 if not 设备相关 else self.获取设备相关队列名称(队列名称)
        print('队列名称:', 队列名称)

        if (
            队列容量 is None
            or helper_task_redis.获取队列中任务个数(队列名称) < 队列容量
        ):
            if bool(
                helper_task_redis.写任务到缓存(
                    队列名称, 数据, expire_seconds=self.get_seconds_expiring()
                )
            ):
                self.设置为处理中()
                return True
        else:
            print(f"{self} 队列已满")
            self.processing = 0
            self.save()
        return False

    # @classmethod
    # def 获取未完成记录(cls):
    #     # 计算超时时间
    #     timeout_time = timezone.now() - datetime.timedelta(
    #         seconds=cls.get_seconds_expiring()
    #     )

    #     return cls.objects.filter(
    #         Q(processing=False) | Q(update_time__lt=timeout_time),
    #         done=False,
    #     )

    def 是否超时(self):
        return (
            # self.processing
            not self.done
            and timezone.now() - datetime.timedelta(seconds=self.get_seconds_expiring())
            >= self.update_time
        )

    def 是否过期(self):
        return timezone.now() >= self.update_time + datetime.timedelta(
            seconds=self.get_seconds_expiring()
        )

    def 设置为处理中(self, **k):
        k = k.copy()
        k.update(processing=1, update_time=timezone.now())
        self.__class__.objects.filter(pk=self.pk).update(**k)
        self.refresh_from_db()
        return self

    def 是否在处理中(self):
        return (
            self.processing
            and self.update_time
            >= timezone.now() - datetime.timedelta(seconds=self.get_seconds_expiring())
        )

    @classmethod
    def 是否有记录正在处理(cls):
        return cls.objects.filter(
            processing=True,
            update_time__gte=timezone.now()
            - datetime.timedelta(seconds=cls.get_seconds_expiring()),
        ).exists()

    @classmethod
    def 获取需要处理的记录(cls, **paras):
        timeout_time = timezone.now() - datetime.timedelta(
            seconds=cls.get_seconds_expiring()
        )

        obj = (
            cls.objects.filter(
                Q(processing=False) | Q(update_time__lt=timeout_time),
                **paras,
            )
            .order_by("-update_time")
            .first()
        )

        if obj is not None:
            obj.processing = True
            obj.save()

        return obj

    def 是否被占用(self):
        return (
            self.processing
            and timezone.now() - datetime.timedelta(seconds=self.get_seconds_expiring())
            < self.update_time
        )

    def 占用(self):
        self.设置为处理中()

    def 解除占用(self):
        self.processing = False
        self.save()

    def save(self, *a, **kw):
        self.cnt_saved += 1
        # self.processing = False
        return super().save(*a, **kw)

    @classmethod
    def get_seconds_expiring(cls):
        return 300

    @classmethod
    def get_task(cls, **paras):
        return (
            cls.objects.filter(**paras)
            .filter(
                Q(processing=False)
                | Q(
                    update_time__lt=(
                        timezone.now()
                        - datetime.timedelta(seconds=cls.get_seconds_expiring())
                    )
                )
            )
            .first()
        )

    @classmethod
    def select_for_processing(cls, pk, seconds=300):
        try:
            if (
                cls.objects.filter(pk=pk)
                .filter(
                    Q(processing=False)
                    | Q(
                        update_time__lt=(
                            timezone.now() - datetime.timedelta(seconds=seconds)
                        )
                    )
                )
                .update(processing=1, update_time=timezone.now())
            ):
                return cls.objects.get(pk=pk)
        except OperationalError:
            pass

    @classmethod
    def 尝试获得处理权(cls, obj):
        return cls.select_for_processing(obj.pk) if obj is not None else None

    def 获取队列字典(self, *a, **kwargs):
        d = {
            "pk": self.pk,
            "cls": self.__class__.__name__,
        }
        for x in a:
            if isinstance(x, str):
                if hasattr(self, x):
                    d[x] = getattr(self, x)
        d.update(kwargs)
        return d

    def 获取设备相关队列名称(self, name):
        return f"{name}_{self.设备串行号}"


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
    名称 = models.CharField(max_length=50, null=True)
    任务服务url = models.URLField(null=True, blank=True)
    任务下载参数 = models.JSONField(default=dict, blank=True)
    优先级 = models.PositiveSmallIntegerField(default=0)
    执行函数 = models.CharField(max_length=50, default="加载配置执行")
    任务描述 = models.TextField(null=True, blank=True)
    定时表达式 = models.CharField(max_length=50, default="every 1 second")
    间隔秒 = models.IntegerField(null=True, blank=True)
    # 超时秒 = models.PositiveBigIntegerField(default=60)
    设定时间 = models.DateTimeField()
    一次执行 = models.BooleanField(default=False)
    # 任务数据 = models.JSONField(default=dict, blank=True, null=True)
    激活 = models.BooleanField(default=True)
    输出调试信息 = models.BooleanField(default=True)
    group_name = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="任务组"
    )

    update_time = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    begin_time = models.TimeField(verbose_name="开始时间", null=True, blank=True)
    end_time = models.TimeField(verbose_name="结束时间", null=True, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["激活", "优先级", "update_time"]),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"[{self.id}]{self.名称} - {self.执行函数}"

    # def 是否超时(self):
    #     return (timezone.now() - self.update_time).seconds >= self.超时秒

    def 刷新任务更新时间(self):
        self.激活 = not self.一次执行
        if self.是否到了执行时间():
            update_time = timezone.localtime(self.update_time)
            self.update_time = calculate_rtn(
                update_time, self.间隔秒, shanghai_time_now(), safe=True
            )

    def save(self, *args, **kwargs):
        self.刷新任务更新时间()
        super().save(*args, **kwargs)

    def 是否到了执行时间(self):
        return (
            not self.id or self.得到所有待执行的任务().filter(id__in=[self.id]).exists()
        )

    # @property
    # def 执行函数实例(self):
    #     return getattr(self, self.执行函数)

    @classmethod
    def 构建所有待执行的任务查询字典(cls, **kwargs):
        _without_updated = kwargs.pop("_without_updated", None)
        if _without_updated is None:
            kwargs["update_time__lte"] = timezone.now() - ExpressionWrapper(
                Value(datetime.timedelta(seconds=1)) * F("间隔秒"),
                output_field=DurationField(),
            )
        kwargs["激活"] = True

        return kwargs

    @classmethod
    def 编写起止参数集合(cls):
        t = timezone.localtime().time()
        return (
            Q(begin_time__isnull=True) | Q(begin_time__lte=t),
            Q(end_time__isnull=True) | Q(end_time__gte=t),
        )

    @classmethod
    def 得到当前时间对象(cls, hour, minute, second):
        now = timezone.localtime(timezone.now())
        return now.replace(hour=hour, minute=minute, second=second)

    @classmethod
    def 得到所有待执行的任务(cls, **kwargs):
        exclude = kwargs.pop("_exclude", "")
        if "id" not in kwargs:
            q = cls.objects.filter(
                *cls.编写起止参数集合(), **cls.构建所有待执行的任务查询字典(**kwargs)
            )
        else:
            q = cls.objects.filter(id=kwargs["id"])
        return q if not exclude else q.exclude(id__in=exclude.strip().split(","))

    # @classmethod
    # def 执行所有定时任务(cls, 每轮间隔秒数=1, 单步=False, **kwargs):
    #     seconds_sleep_when_exception = 10
    #     while 1:
    #         q = cls.得到所有待执行的任务(**kwargs).order_by("-优先级", "update_time")
    #         try:
    #             for obj in q.iterator():
    #                 if obj.step() and obj.优先级 > 0:
    #                     break
    #         except Exception:
    #             print(traceback.format_exc())
    #             print(f"发生异常, 等待{seconds_sleep_when_exception}秒后继续执行")
    #             time.sleep(seconds_sleep_when_exception)
    #         if 单步:
    #             break
    #         time.sleep(每轮间隔秒数) if 每轮间隔秒数 else None

    @classmethod
    def 执行所有定时任务(cls, 每轮间隔秒数=1, 单步=False, **kwargs):
        print('----------------------------------执行所有定时任务')
        while 1:
            q = cls.得到所有待执行的任务(**kwargs).order_by("-优先级", "update_time")
            print('--------------', q.count())
            max_priority = 0
            for obj in q.iterator():
                if obj.优先级 < max_priority:
                    break
                if obj.step() and obj.优先级 > max_priority:
                    max_priority = obj.优先级

            print('--------------=====', q.count())
            if 单步:
                break
            time.sleep(每轮间隔秒数) if 每轮间隔秒数 else None
            print('--------------=====---------', q.count())

    def print_info(self, *a):
        if self.输出调试信息:
            print(*a)

    def step(self, seconds_sleep_when_exception=1):
        executed = False
        try:
            self.下载任务数据()
            if self.远程数据记录 is None or not self.远程数据记录.is_empty():
                self.print_info(f"开始执行任务:{self.名称} - {self.执行函数}")
                executed = getattr(self, self.执行函数)()
            self.save()

        except Exception:
            print(traceback.format_exc())
            print(f"发生异常, 等待{seconds_sleep_when_exception}秒后继续执行")
            time.sleep(seconds_sleep_when_exception)
        return executed

    def 组建下载参数(self):
        return copy.copy(self.任务下载参数)

    def 获取完整任务数据下载链接(self, clear=False, **kwargs):
        if not clear:
            d = self.组建下载参数()
            d.update(**kwargs)
        else:
            d = kwargs
        return f"{self.任务服务url}?{urlencode(d)}"

    def 下载任务数据(self):
        try:
            self.远程数据记录 = (
                RemoteModel(self.任务服务url, pk_name="id", **self.组建下载参数())
                if self.任务服务url
                else None
            )
        except requests.exceptions.HTTPError as e:
            print(e)
            self.远程数据记录 = None
        return self.远程数据记录


class 抽象定时任务日志(AbstractModel):
    定时任务_id = models.BigIntegerField()
    数据_id = models.BigIntegerField(null=True)
    异常日志 = models.JSONField(default=dict)

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
class 抽象标签组(AbstractModel):
    初始化表 = [
        ("儿童", "青少年", "青年", "中年", "老年", "未知_年龄段"),
        ("体重不足", "超重", "肥胖", "未知_体重", "正常体重"),
        ("男性", "女性", "未知_性别"),
        ("哮喘", "高血压", "心脏病", "糖尿病", "未知_疾病"),
    ]

    健康档案字段名choices = (
        ("gender", "性别"),
        ("bmi", "bmi"),
        ("age", "年龄"),
        ("chronic_disease", "慢性病"),
    )

    列表 = models.JSONField(default=list)
    健康档案字段名 = models.CharField(
        max_length=64, null=True, choices=健康档案字段名choices
    )
    # 抽取提示词 = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def 初始化标签组(cls):
        for i, y in enumerate(cls.初始化表):
            y = sorted(list(y))
            cls.objects.get_or_create(
                列表=y,
                健康档案字段名=cls.健康档案字段名choices[i][0],
            )


class 抽象原子标签(AbstractModel):
    # 组_id = models.PositiveBigIntegerField(null=True)
    名称 = models.CharField(max_length=100)
    提示词 = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return self.名称

    @classmethod
    def 初始化原子标签(cls):
        for y in 抽象标签组.初始化表:
            for z in y:
                if not z.startswith("未知_"):
                    cls.objects.get_or_create(名称=z)

    @classmethod
    def 生成提示词的提示词(cls):
        return """我目前有一个词汇标签：“{名称}”，我希望使用这个标签：“{名称}”去匹配一段文字，这个匹配能够输出该段内容是否匹配成功的结果。
    通常这个过程是通过大模型提示词完成的，我希望你能写出这个标签匹配过程的提示词：
1，提示词和“{名称}”这个标签相关，是否也能匹配它的各类近义词，并在提示词中举例一些近义词，同时也强调不限于这些近义词。
2，界定输出的格式，为json格式。{{'标签匹配结果':‘是’}}
3, 如果结果是否，则JSON格式为：{{'标签匹配结果':‘否’}}
4, 请以如下开头编写：你是一个贴标签的专家，你现在需要使用如下标签“{名称}”去匹配输入内容，。。。。
5， 请直接输出结果，不要再加前后说明性解释和其他内容。

"""

    @classmethod
    def 未生成提示词的提示词的字典(cls):
        q = cls.objects.filter(提示词__isnull=True).exclude(名称="其他")
        if q.exists():
            d = {"名称": [x.名称 for x in q]}
            d["模版"] = cls.生成提示词的提示词()
            return d

    @property
    def 集成提示词(self):
        return (
            self.提示词.replace("标签匹配结果", f"{self.名称}") if self.提示词 else None
        )

    @classmethod
    def 得到标签抽取集成提示词(cls):
        l = map(lambda x: x.集成提示词, cls.objects.all())
        l = filter(lambda x: x, l)
        # prompt_list = '\n'.join([x.集成提示词 for x in cls.objects.all()])
        prompt_list = "\n".join(l)
        return f"""
        你是一个贴标签的专家，以下是一些标签抽取的列表：
        ******标签抽取列表：开始******
        {prompt_list}
        ******标签抽取列表：结束******

        ******输出要求：******
        1， 以上全部标签抽取列表处理完成后，将结果放入一个list， 输出的格式为一个JSON，列表格式，例如：[{{"糖尿病":"是"}},{{"青少年":"否"}},...]
        2， 列表中的每个元素都是一个字典，只含一个键，举例如：{{"糖尿病":"是"}} 或 {{"糖尿病":"否"}}
        3， 值只有两种结果："是"或"否"
        请严格按以下规则输出JSON：仅输出结果，不要解释。
    """


class 抽象微信组合标签(models.Model):
    原子标签列表 = models.JSONField(default=list)

    class Meta:
        abstract = True

    def __str__(self):
        return self.名称

    @property
    def 名称(self):
        return self.原子标签列表

    @classmethod
    def 初始化微信组合标签(cls):
        import itertools

        for y in itertools.product(*抽象标签组.初始化表, repeat=1):
            y = sorted(list(y))
            cls.objects.get_or_create(原子标签列表=y)
