from django.db import models


class AbstractUser(models.Model):
    name = models.CharField(verbose_name="姓名", max_length=50, blank=True, null=True)
    sn = models.CharField(verbose_name="注册码", max_length=50, blank=True, null=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = []
        verbose_name_plural = verbose_name = '用户'


class AbstractContact(models.Model):
    RELATION_UNKNOWN = 0
    RELATION_FRIEND = 1
    RELATION_FAMILY = 2


    RELATION_WORK = 3
    RELATION_COWORKER = 4
    RELATION_FRIEND = 5
    RELATION_FAMILY = 6
    RELATION_WORK = 7
    RELATION_COWORKER = 8
    RELATION_TEACHER = 9
    RELATION_SCHOOLMATE = 10
    RELATION_STUDENT = 11
    RELATION_MEMBER = 12
    RELATION_CLIENT = 13

    RELATIONS = (
        (RELATION_UNKNOWN, '未知'),
        (RELATION_FRIEND, '朋友'),
        (RELATION_FAMILY, '亲人'),
        (RELATION_WORK, '同事'),
        (RELATION_COWORKER, '合作伙伴'),
        (RELATION_TEACHER, '老师'),
        (RELATION_SCHOOLMATE, '同学'),
        (RELATION_STUDENT, '学生'),
        (RELATION_MEMBER, '会员'),
        (RELATION_CLIENT, '客户'),
    )
    RELATION_MAP = dict(RELATIONS)
    user_id = models.PositiveIntegerField(verbose_name="用户ID")
    name = models.CharField(verbose_name="姓名", max_length=50, blank=True, null=True)
    relation = models.SmallIntegerField(verbose_name="消息类型", choices=RELATIONS, default=RELATION_UNKNOWN)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = []
        verbose_name_plural = verbose_name = '联系人'


class AbstractMessage(models.Model):
    STATUS_GENERATING = 0
    STATUS_GENERATED = 1
    STATUS_SENT = 2
    STATUS_SEND_FAILED = 3

    STATUS = (
        (STATUS_GENERATING, '生成中'),
        (STATUS_GENERATED, '已生成'),
        (STATUS_SENT, '已发送'),
        (STATUS_SEND_FAILED, '发送失败'),
    )
    user_id = models.PositiveIntegerField(verbose_name="用户ID", default=0)
    contact_id = models.PositiveIntegerField(verbose_name="通讯录成员ID", default=0)
    requirement = models.TextField(verbose_name="要求", blank=True, null=True)
    content = models.TextField(verbose_name="内容", blank=True, null=True)
    voice_url = models.URLField(verbose_name='语音消息URL',blank=True, null=True)
    status = models.SmallIntegerField(verbose_name="消息类型", choices=STATUS, default=STATUS_GENERATING)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = []
        verbose_name_plural = verbose_name = '消息'


class AbstractTask(models.Model):
    TASK_TYPE_INIT = 0
    TASK_TYPE_RUNNING = 1
    TASK_TYPE_OK = 2
    TASK_TYPE_FAILED = 3

    TASK_TYPES = (
        (TASK_TYPE_INIT, '初始化'),
        (TASK_TYPE_RUNNING, '执行中'),
        (TASK_TYPE_OK, '执行成功'),
        (TASK_TYPE_FAILED, '执行失败'),
    )
    user_id = models.PositiveIntegerField(verbose_name="用户ID", default=0)
    contact_id = models.PositiveIntegerField(verbose_name="通讯录成员ID", default=0)
    type = models.SmallIntegerField(verbose_name="消息类型", choices=TASK_TYPES, default=0)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = []
        verbose_name_plural = verbose_name = '任务'