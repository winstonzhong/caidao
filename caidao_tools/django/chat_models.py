from django.db import models, transaction
from django.apps import apps
all_models = apps.all_models


def get_model(app_name, model_name):
    """
    根据app名称, 模型名称返回model
    :param app_name: app名称
    :param model_name: 模型名称
    :return:
    """
    return all_models[app_name][model_name.lower()]


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

    RANKS = (
        (0, '不合格'),
        (1, '合格'),
        (2, '很好'),
    )
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    url = models.TextField(verbose_name='图片URL', null=True, blank=True)
    media_id = models.CharField(max_length=100, verbose_name='素材media_id', null=True, blank=True)
    raw_pic_tag = models.CharField(max_length=100, verbose_name='原图标签', default='')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    url_hq = models.TextField(verbose_name='高清图片URL', null=True, blank=True)
    media_id_hq = models.CharField(max_length=100, verbose_name='高清素材media_id', null=True, blank=True)
    rank = models.SmallIntegerField(verbose_name="合格程度", choices=RANKS, null=True, blank=True)
    reason = models.CharField(max_length=200, verbose_name='原因', null=True, blank=True)
    is_made_hq_img = models.BooleanField(verbose_name='是否制作高清图片', default=False)

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

    PLATFORM_OA = 0  # 微信公众号
    PLATFORM_MPWX = 1  # 微信小程序
    PLATFORM_CODES = (
        (PLATFORM_OA, '微信公众号'),
        (PLATFORM_MPWX, '微信小程序')

    )

    # 平台映射
    PLATFORM_MAP = {
        'web': PLATFORM_OA,
        'mp-weixin': PLATFORM_MPWX
    }
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

    platform = models.SmallIntegerField(verbose_name='平台', choices=PLATFORM_CODES, default=PLATFORM_OA)

    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True
        unique_together = ('open_id', 'platform', 'name')

    def __str__(self):
        return '[{self.open_id}]{self.name}'.format(self=self)


class AbstractUserLevel(models.Model):
    """等级"""
    DEFAULT_LEVEL_CODE = 0
    LEVEL_CODE = (
        (DEFAULT_LEVEL_CODE, "免费"),
        (1, "连续包月VIP"),
        (2, "季度VIP"),
        (3, "年度VIP"),
        (4, "终身VIP")
    )
    name = models.CharField(max_length=50, verbose_name='用户等级描述', default='')
    code = models.SmallIntegerField(verbose_name="用户等级", choices=LEVEL_CODE, default=DEFAULT_LEVEL_CODE)
    make_limit = models.IntegerField(verbose_name="制作次数", default=0)
    download_limit = models.IntegerField(verbose_name="高清图片下载次数", default=0)
    data = models.TextField(verbose_name='数据', default='')
    max_wait_time = models.IntegerField(verbose_name="最大等待时间", default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractTaskOrder(models.Model):
    """任务工单"""

    # 工单状态
    STATUS_INVALID = -1
    DEFAULT_STATUS = 0
    STATUS_WAITING = 1
    STATUS_IN_PROGRESS = 2
    STATUS_TO_BE_REVIEWED = 3
    STATUS_NEED_HQ_IMG = 4
    STATUS_COMPLETE = 100
    STATUS = (
        (DEFAULT_STATUS, '排队中'),
        (STATUS_WAITING, '等待处理'),
        (STATUS_IN_PROGRESS, '正在处理'),
        (STATUS_TO_BE_REVIEWED, '等待客服审核'),
        (STATUS_NEED_HQ_IMG, '需要制作高清图'),
        (STATUS_COMPLETE, '任务完成'),
        (STATUS_INVALID, '作废'),
    )

    # 未制作完成的工单
    UNPROCESSED_STATUS_LIST = [DEFAULT_STATUS, STATUS_WAITING, STATUS_IN_PROGRESS]

    # 已完成工单
    COMPLETED_STATUS_LIST = [STATUS_NEED_HQ_IMG, STATUS_COMPLETE]

    # 页面
    USER_INDEX = 1
    KF_INDEX = 2
    USER_RESULT = 3
    PAGE_ORDER_MAP = {
        USER_INDEX: [DEFAULT_STATUS, STATUS_WAITING, STATUS_IN_PROGRESS, STATUS_TO_BE_REVIEWED, STATUS_NEED_HQ_IMG, STATUS_COMPLETE],
        KF_INDEX: [STATUS_TO_BE_REVIEWED],
        USER_RESULT: [STATUS_NEED_HQ_IMG, STATUS_COMPLETE],
    }
    # 优先级
    DEFAULT_PRIORITY = 99  # 默认优先级
    VIEWED_AD = 1  # 已观看广告
    CLICK_BUY = 2  # 已点击购买
    CLICK_AD = 3  # 已点击广告

    PRIORITIES = (
        (DEFAULT_PRIORITY, '默认'),
        (VIEWED_AD, '已观看广告'),
        (CLICK_BUY, '已点击购买'),
        (CLICK_AD, '已点击广告'),
    )

    DEFAULT_PIC_MODE = 0
    PIC_MODES = (
        (DEFAULT_PIC_MODE, '原图'),
        (1, '轻度美颜'),
        (2, '极度美颜'),
    )
    
    HAIR_COLORS = (
        (0, "Ash Blonde"),
        (1, "Ash Brown"),
        (2, "Auburn"),
        (3, "Black"),
        (4, "Blonde"),
        (5, "Bronze"),
        (6, "Brunette"),
        (7, "Butterscotch"),
        (8, "Caramel"),
        (9, "Chestnut"),
        (10, "Copper"),
        (11, "Dark Auburn"),
        (12, "Dark Brown"),
        (13, "Dark Chestnut"),
        (14, "Dark Red"),
        (15, "Ginger"),
        (16, "Golden Blonde"),
        (17, "Honey Blonde"),
        (18, "Light Brown"),
        (19, "Light Red"),
        (20, "Mahogany"),
        (21, "Platinum Blonde"),
        (22, "Red"),
        (23, "Salt and Pepper (Gray)"),
        (24, "Sandy Blonde"),        
        ) 
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户", related_name='用户')
    # creator = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="创建者", related_name='创建者')
    # parent = models.ForeignKey('self', on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="来源工单", blank=True, null=True)

    status = models.SmallIntegerField(verbose_name='状态', choices=STATUS, default=DEFAULT_STATUS)
    priority = models.SmallIntegerField(verbose_name='优先级', choices=PRIORITIES, default=DEFAULT_PRIORITY)
    user_requirement = models.CharField(max_length=50, verbose_name='客户要求', default='')
    kf_requirement = models.CharField(max_length=50, verbose_name='客服填写要求', default='')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    wait_time = models.IntegerField(verbose_name='等待时间', default=0)
    user_level_code = models.SmallIntegerField(verbose_name='用户等级code', choices=AbstractUserLevel.LEVEL_CODE,
                                               default=AbstractUserLevel.DEFAULT_LEVEL_CODE)
    platform = models.SmallIntegerField(verbose_name='平台', choices=AbstractUser.PLATFORM_CODES,
                                        default=AbstractUser.PLATFORM_OA)

    pic_mode = models.SmallIntegerField(verbose_name='图像模式', choices=PIC_MODES, default=DEFAULT_PIC_MODE)
    is_downloaded = models.BooleanField(verbose_name='是否下载', default=False)
    hair_color = models.SmallIntegerField(verbose_name='发色', choices=HAIR_COLORS, default=3)

    class Meta:
        abstract = True


    @classmethod
    @transaction.atomic
    def complete_order(cls, order_id, task_pic_list):
        """
        完成图片制作后更新数据库操作
        1. 更新工单(TaskOrder)状态
        2. 更新工单图片(TaskPic)数据
        3. 更新工单图片关系表(TaskRelation)数据
        4. 扣减制作次数
        :param order_id: 工单表ID
        :param task_pic_list: 图片数据 [{media_id: "xxx"}]
        :return:
        """
        task_relation_model = get_model('task', 'TaskRelation')
        task_pic_model = get_model('task', 'TaskPic')
        user_quota_model = get_model('user', 'quota')
        order_record = cls.objects.get(id=order_id)
        order_record.status = cls.STATUS_COMPLETE
        order_record.save()
        user = order_record.user
        user_id = user.id

        # create_task_pic_list = []
        create_task_relation_list = []
        for task_pic_data in task_pic_list:
            insert_task_pic_data = {'user_id': user_id, 'url': task_pic_data['url']}
            task_pic_obj = task_pic_model.objects.create(**insert_task_pic_data)
            # print(task_pic_obj.id)
            # print(dir(task_pic_obj))
            # create_task_pic_list.append(task_pic_obj)

            insert_task_relation_data = {'order_id': order_id,
                                         'relation_id': task_pic_obj.id,
                                         'relation_type': task_relation_model.RELATIONS_TYPE_TASK_PIC
                                         }
            task_relation_obj = task_relation_model(**insert_task_relation_data)
            create_task_relation_list.append(task_relation_obj)

        # task_pic_model.objects.bulk_create(create_task_pic_list)
        task_relation_model.objects.bulk_create(create_task_relation_list)

        # quota_record = user_quota_model.objects.filter(user_id=user_id).last()
        # quota_record.left_num = max(0, quota_record.left_num - 1)
        # quota_record.save()

    @classmethod
    @transaction.atomic
    def update_hq_pics(cls, order_id, hq_img_media_id_dict):

        """
        制作高清图片后更新数据库操作
        1. 更新TaskOrder状态
        2. 更新结果图片的高清图片media_id
        3. 扣减Quota表高清图片制作次数
        :param order_id: 工单号
        :param hq_img_media_id_dict: 高清图片media_id字典{id: media_id}; id - TaskPic表记录的id; media_id: 临时素材库media_id
        :return:
        """
        # 更新taskorder
        order_record = cls.objects.get(id=order_id)
        order_record.status = cls.STATUS_COMPLETE
        order_record.save()
        user = order_record.user
        # 更新taskpic
        task_pic_records = user.taskpic_set.filter(id__in=list(hq_img_media_id_dict.keys()))
        for task_pic_record in task_pic_records:
            task_pic_id = task_pic_record.id
            task_pic_record.media_id_hq = hq_img_media_id_dict[task_pic_id]
            task_pic_record.is_made_hq_img = False
            task_pic_record.save()


        # 更新quota
        quota = user.quota_set.last()
        hq_img_num = len(hq_img_media_id_dict)
        # print('raw....', quota.hq_img_left_num)
        quota.hq_img_left_num = max(0, quota.hq_img_left_num - hq_img_num)
        # print('hq_img_num.....', hq_img_num, quota.hq_img_left_num)
        quota.save()


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
    TYPE_MSG = 0
    TYPE_VOICE_MSG = 1
    TYPES = (
        (TYPE_MSG, '文字消息'),
        (TYPE_VOICE_MSG, '语音文字消息')
    )
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    type = models.SmallIntegerField(verbose_name="消息内容", choices=TYPES, default=TYPE_MSG)
    content = models.TextField(verbose_name='内容', default="")
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractPic(models.Model):
    """用户图片"""
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    url = models.TextField(verbose_name='图片URL', null=True, blank=True)
    media_id = models.CharField(max_length=100, verbose_name='素材media_id', null=True, blank=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractQuota(models.Model):
    """用户制作额度表"""
    # user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False, verbose_name="用户")
    upper_limit = models.IntegerField(verbose_name="创作额度", default=0)
    left_num = models.IntegerField(verbose_name="剩余次数", default=0)
    hq_img_upper_limit = models.IntegerField(verbose_name="高清图片制作额度", default=0)
    hq_img_left_num = models.IntegerField(verbose_name="高清图片剩余制作次数", default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractOrder(models.Model):
    '''
    订单
    '''
    ORDER_STATUS_INIT = 0  # 待付款
    ORDER_STATUS_COMPLETE = 1  # 付款成功
    ORDER_STATUS_SETTLED = 2  # 已核算(作废)
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
    make_times = models.IntegerField(verbose_name="制作次数", default=0)
    total_days = models.IntegerField(verbose_name="总天数", default=0)
    status = models.SmallIntegerField(verbose_name="订单状态", default=0, choices=STATUS_CHOICE)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractOrderProduct(models.Model):
    """订单产品"""
    name = models.CharField(max_length=100, verbose_name='产品名称', default='')
    # product = models.ForeignKey(Product, verbose_name="产品", db_constraint=False, on_delete=models.DO_NOTHING)
    price = models.DecimalField(verbose_name="价格", max_digits=8, decimal_places=2, default=0)
    # order = models.ForeignKey(Order, verbose_name="订单", db_constraint=False, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


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

    class Meta:
        abstract = True


class AbstractPk(models.Model):
    """pk表"""
    creator_id = models.IntegerField(verbose_name="创建用户ID", default=0)
    name = models.CharField(max_length=100, verbose_name='名称', default="")
    description = models.CharField(max_length=200, verbose_name='中奖描述', default="")
    reward_count = models.IntegerField(verbose_name='中奖人数', default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractPkUser(models.Model):
    """pk参与用户表"""
    user_id = models.IntegerField(verbose_name="创建用户ID", default=0)  # 关联user表
    pic_id = models.IntegerField(verbose_name="图片ID", default=0)  # 关联pic表
    pk_id = models.IntegerField(verbose_name="PK ID", default=0)  # 关联pk表
    requirement = models.CharField(max_length=100, verbose_name='要求', default="")
    reward_code = models.CharField(max_length=50, verbose_name='兑奖码', default="")
    score = models.IntegerField(verbose_name='得分', default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractPkHelper(models.Model):
    """pk助力表"""
    pk_id = models.IntegerField(verbose_name="PK ID", default=0)  # 关联pk表
    user_id = models.IntegerField(verbose_name="创建用户ID", default=0)  # 关联user表
    helper_id = models.IntegerField(verbose_name="助力用户ID", default=0)  # 关联user表
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractUserScene(models.Model):
    """用户和场景的关联表"""
    user_id = models.IntegerField(verbose_name="用户ID", default=0)
    scene_id = models.IntegerField(verbose_name="场景ID", default=0)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True
        unique_together = [['user_id', 'scene_id']]


class AbstractPicJournalAccount(models.Model):
    """图片制作次数流水记录"""

    TYPE_PAY = 0
    TYPE_MAKE_PIC = 1
    TYPE_MAKE_HQ_PIC = 2
    TYPE_CHOICE = (
        (TYPE_PAY, '充值'),
        (TYPE_MAKE_PIC, '普通图片制作'),
        (TYPE_MAKE_HQ_PIC, '高清图片制作'),
    )
    user_id = models.IntegerField(verbose_name="用户ID", default=0)
    make_times = models.IntegerField(verbose_name="制作次数", default=0)
    type = models.SmallIntegerField(verbose_name="订单状态", default=0, choices=TYPE_CHOICE)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True

    @classmethod
    def insert_record(cls, user_id, make_times, type):
        """
        插入记录
        :param user_id: 用户ID
        :param make_times: 制作次数
        :param type: 类型(见定义中的类型值)
        :return:
        """
        data = {
            'user_id': user_id,
            'make_times': make_times,
            'type': type,
        }
        obj = cls.objects.create(**data)
        return obj

    @classmethod
    def get_total_make_times(cls, user_id):
        """
        获取指定用户可制作次数
        :param user_id:
        :return: 可制作次数
        """
        records = cls.objects.filter(user_id=user_id)
        return sum([record.make_times for record in records])