from django.db import models


class AbstractUser(models.Model):

    STATUS_INIT = 0
    STATUS_SYNC_CONTACT = 1
    STATUS_GENERATE_MSG = 2
    STATUS_SEND_MSG = 3

    WORKER_STATUS = (
        (STATUS_INIT, '空闲'),
        (STATUS_SYNC_CONTACT, '通讯录同步'),
        (STATUS_GENERATE_MSG, '生成消息'),
        (STATUS_SEND_MSG, '发送消息'),
    )

    name = models.CharField(verbose_name="姓名", max_length=50, blank=True, null=True)
    sn = models.CharField(verbose_name="注册码", max_length=50, blank=True, null=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    worker_status = models.SmallIntegerField(verbose_name="worker状态", choices=WORKER_STATUS, default=STATUS_INIT)
    worker_thread = models.IntegerField(verbose_name="worker线程", blank=True, null=True)

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
    RELATION_TEACHER = 5
    RELATION_SCHOOLMATE = 6
    RELATION_STUDENT = 7
    RELATION_MEMBER = 8
    RELATION_CLIENT = 9

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
    relation = models.SmallIntegerField(verbose_name="关系", choices=RELATIONS, default=RELATION_UNKNOWN)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = []
        verbose_name_plural = verbose_name = '联系人'


class AbstractMessage(models.Model):
    STATUS_INIT = 0
    STATUS_GENERATED = 1
    STATUS_SENT = 2
    STATUS_SEND_FAILED = 3

    STATUS = (
        (STATUS_INIT, '初始化'),
        (STATUS_GENERATED, '已生成'),
        (STATUS_SENT, '已发送'),
        (STATUS_SEND_FAILED, '发送失败'),
    )
    user_id = models.PositiveIntegerField(verbose_name="用户ID", default=0)
    contact_id = models.PositiveIntegerField(verbose_name="通讯录成员ID", default=0)
    requirement = models.TextField(verbose_name="要求", blank=True, null=True)
    content = models.TextField(verbose_name="内容", blank=True, null=True)
    voice_url = models.URLField(verbose_name='语音消息URL',blank=True, null=True)
    status = models.SmallIntegerField(verbose_name="消息类型", choices=STATUS, default=STATUS_INIT)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = []
        verbose_name_plural = verbose_name = '消息'

