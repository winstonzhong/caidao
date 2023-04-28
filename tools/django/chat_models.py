from django.db import models


class AbstractTaskRelation(models.Model):
    """任务关联表"""
    RELATIONS_TYPE_PIC = 0
    RELATIONS_TYPE_MSG = 1
    RELATIONS_TYPE_SCENE_USER = 2
    RELATIONS_TYPE_TASK_PIC = 3
    RELATIONS_TYPE_SCENE_KF = 4
    RELATION_TYPE = (
        (RELATIONS_TYPE_PIC, "图片"),
        (RELATIONS_TYPE_MSG, "消息"),
        (RELATIONS_TYPE_SCENE_USER, "场景风格(客户填写)"),
        (RELATIONS_TYPE_SCENE_KF, "场景风格(客服填写)"),
        (RELATIONS_TYPE_TASK_PIC, "结果图片"),
    )
    order_id = models.IntegerField(verbose_name="任务工单ID", default=0)
    relation_id = models.IntegerField(verbose_name="关联表ID", default=0)
    relation_type = models.SmallIntegerField(verbose_name="关联数据类型", choices=RELATION_TYPE, default=RELATIONS_TYPE_PIC)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractTaskPic(models.Model):
    """结果图片"""
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    url = models.TextField(verbose_name='图片URL', null=True, blank=True)
    media_id = models.CharField(max_length=100, verbose_name='素材media_id', null=True, blank=True)
    raw_pic_tag = models.CharField(max_length=100, verbose_name='原图标签', default='')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    url_hq = models.TextField(verbose_name='高清图片URL', null=True, blank=True)
    media_id_hq = models.CharField(max_length=100, verbose_name='高清素材media_id', null=True, blank=True)

    class Meta:
        abstract = True


class AbstractTaskOrder(models.Model):
    """任务工单"""
    STATUS_INVALID = -1
    DEFAULT_STATUS = 0
    STATUS_WAITING = 1
    STATUS_IN_PROGRESS = 2
    STATUS_TO_BE_REVIEWED = 3
    STATUS_COMPLETE = 4
    STATUS = (
        (DEFAULT_STATUS, '排队中'),
        (STATUS_WAITING, '等待处理'),
        (STATUS_IN_PROGRESS, '正在处理'),
        (STATUS_TO_BE_REVIEWED, '等待客服审核'),
        (STATUS_COMPLETE, '任务完成'),
        (STATUS_INVALID, '作废'),
    )
    UNPROCESSED_STATUS_LIST = [DEFAULT_STATUS, STATUS_WAITING, STATUS_IN_PROGRESS]  # 未制作完成的工单
    USER_INDEX = 1
    KF_INDEX = 2
    USER_RESULT = 3
    PAGE_ORDER_MAP = {
        USER_INDEX: [DEFAULT_STATUS, STATUS_WAITING, STATUS_IN_PROGRESS, STATUS_TO_BE_REVIEWED],
        KF_INDEX: [STATUS_TO_BE_REVIEWED],
        USER_RESULT: [STATUS_COMPLETE],
    }

    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户", related_name='用户')
    # creator = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="创建者", related_name='创建者')
    # parent = models.ForeignKey('self', on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="来源工单", blank=True, null=True)

    status = models.SmallIntegerField(verbose_name='状态', choices=STATUS, default=DEFAULT_STATUS)
    user_requirement = models.CharField(max_length=50, verbose_name='客户要求', default='')
    kf_requirement = models.CharField(max_length=50, verbose_name='客服填写要求', default='')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractScene(models.Model):
    """场景风格"""
    name = models.CharField(max_length=20, verbose_name='模板ID', default='')
    keyword = models.CharField(max_length=50, verbose_name='关键词', default='')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractPushTask(models.Model):
    """推送任务"""
    AUTO_REPLY = 1
    TYPES = (
        (AUTO_REPLY, '自动回复'),
    )
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    type = models.SmallIntegerField(verbose_name='状态', choices=TYPES, default=AUTO_REPLY)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractTaskPicDownload(models.Model):
    """结果图片下载记录"""
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    url = models.TextField(verbose_name='图片URL/media_id', default='')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractUserLevel(models.Model):
    """等级"""
    DEFAULT_LEVEL_CODE = 0
    LEVEL_CODE = (
        (DEFAULT_LEVEL_CODE, "普通用户"),
        (1, "VIP用户")
    )
    name = models.CharField(max_length=50, verbose_name='用户等级描述', default='')
    code = models.SmallIntegerField(verbose_name="用户等级", choices=LEVEL_CODE, default=DEFAULT_LEVEL_CODE)
    make_limit = models.IntegerField(verbose_name="制作次数", default=0)
    download_limit = models.IntegerField(verbose_name="下载次数", default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractUser(models.Model):
    """用户"""
    MALE_CODE = 0
    FEMALE_CODE = 1
    GENDER_CHOICE = (
        (MALE_CODE, "男性"),
        (FEMALE_CODE, "女性"),
    )
    TYPE_USER = 0
    TYPE_KF = 1
    TYPES = (
        (TYPE_USER, '客户'),
        (TYPE_KF, '客服'),
    )
    name = models.CharField(max_length=50, verbose_name='用户名称', default='')
    open_id = models.CharField(max_length=50, verbose_name='微信Open ID', blank=True, null=True, unique=True)
    # referral = models.ForeignKey('self', on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="推荐人", blank=True, null=True)
    # level = models.ForeignKey(UserLevel, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户等级", blank=True, null=True)
    amount = models.DecimalField(verbose_name='用户余额', max_digits=10, decimal_places=2, default=0)
    is_signed_eula = models.BooleanField(verbose_name="是否签署用户协议", default=False)
    head_img = models.TextField(verbose_name='用户头像', default="")
    gender = models.SmallIntegerField(verbose_name='性别', choices=GENDER_CHOICE, default=MALE_CODE)
    user_data = models.TextField(verbose_name='用户数据', default="")  # 获取的公众号用户信息原数据

    activation = models.IntegerField(verbose_name='活跃度', default=0)
    last_checkin_at = models.DateTimeField(verbose_name='签到时间', null=True)
    type = models.SmallIntegerField(verbose_name='用户类型', choices=TYPES, default=TYPE_USER)

    expired_at = models.DateTimeField(verbose_name='过期时间', null=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractWithdraw(models.Model):
    """体现申请单"""
    WITHDRAW_STATUS_INIT = 0

    STATUS_CHOICE = (
        (WITHDRAW_STATUS_INIT, '审核中'),
        ('1', '审核通过'),
        ('2', '拒绝'),
        ('3', '作废'),

    )
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    status = models.SmallIntegerField(verbose_name="申请单状态", choices=STATUS_CHOICE, default=WITHDRAW_STATUS_INIT)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractMsg(models.Model):
    """用户消息"""
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    content = models.TextField(verbose_name='内容', default="")
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractPic(models.Model):
    """用户图片"""
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    url = models.TextField(verbose_name='图片URL', default='')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractQuota(models.Model):
    """用户制作额度表"""
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    upper_limit = models.IntegerField(verbose_name="额度", default=0)
    used_num = models.IntegerField(verbose_name="使用次数", default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class AbstractOrder(models.Model):
    '''
    订单
    '''
    ORDER_STATUS_INIT = 0  # 代付款
    ORDER_STATUS_COMPLETE = 1  # 付款成功
    ORDER_STATUS_CANCELLED = -1  # 作废
    STATUS_CHOICE = (
        (ORDER_STATUS_INIT, "待付款"),
        (ORDER_STATUS_COMPLETE, "付款成功"),
        (ORDER_STATUS_CANCELLED, "作废")
    )
    wx_out_trade_no = models.CharField(max_length=50, verbose_name='微信订单号', default='')
    # user = models.ForeignKey(User, verbose_name="用户", db_constraint=False, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=100, verbose_name='订单名称', default='')
    amount = models.DecimalField(verbose_name='订单总金额', max_digits=8, decimal_places=2, default=0)
    total_days = models.IntegerField(verbose_name="总天数", default=0)
    status = models.SmallIntegerField(verbose_name="订单状态", default=0, choices=STATUS_CHOICE)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class AbstractOrderProduct(models.Model):
    """订单产品"""
    name = models.CharField(max_length=100, verbose_name='产品名称', default='')
    # product = models.ForeignKey(Product, verbose_name="产品", db_constraint=False, on_delete=models.DO_NOTHING)
    price = models.DecimalField(verbose_name="价格", max_digits=8, decimal_places=2, default=0)
    # order = models.ForeignKey(Order, verbose_name="订单", db_constraint=False, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class AbstractProduct(models.Model):
    '''
    产品
    '''
    name = models.CharField(max_length=100, verbose_name='产品名称', default="")
    days = models.IntegerField(verbose_name="天数", default=0)
    price = models.DecimalField(verbose_name="价格", max_digits=8, decimal_places=2, default=0)
    # level = models.ForeignKey(UserLevel, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户等级", null=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)