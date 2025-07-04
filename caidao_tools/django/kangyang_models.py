import uuid
from django.db import models
from django.utils import timezone
from django.forms import model_to_dict
from caidao_tools.django.storage import MyStorage


# 用户数据来源
MEASURE_SOURCE_CHOICES = ((0, "用户输入数据"), (1, "智能手环"))


def get_uuid():
    return uuid.uuid1().hex


class AbstractUser(models.Model):
    """用户"""

    MALE_CODE = 0
    FEMALE_CODE = 1
    GENDER_CHOICE = (
        (MALE_CODE, "男性"),
        (FEMALE_CODE, "女性"),
    )
    name = models.CharField(max_length=64, verbose_name="用户名称", default="")
    open_id = models.CharField(
        max_length=64, verbose_name="微信Open ID", blank=True, null=True, unique=True
    )
    head_img = models.FileField(
        verbose_name="用户头像",
        max_length=200,
        storage=MyStorage,
        null=True,
        blank=True,
    )
    gender = models.SmallIntegerField(
        verbose_name="性别", choices=GENDER_CHOICE, blank=True, null=True
    )
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    data = models.TextField(verbose_name="用户授权信息", null=True, blank=True)
    phone = models.CharField(
        verbose_name="手机号", max_length=20, blank=True, null=True
    )
    email = models.CharField(
        verbose_name="邮箱地址", max_length=50, blank=True, null=True
    )
    birthday = models.DateTimeField(verbose_name="出生日期", null=True, blank=True)
    uuid = models.CharField(
        max_length=64, verbose_name="uuid", db_index=True, default=get_uuid
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]

    def __str__(self):
        return "[{self.open_id}]{self.name}".format(self=self)


class AbstractMsg(models.Model):
    """用户消息"""

    TYPES = (
        (0, "未知"),
        (1, "文本消息"),
        (2, "图片消息"),
        (3, "语音消息"),
        (4, "视频消息"),
        (5, "小程序卡片消息"),
        (6, "短视频消息"),
        (7, "坐标消息"),
        (8, "链接消息"),
        (8, "消息消息转发到客服"),
        (10, "事件推送消息"),
    )

    EVENTS = (
        (0, "无"),
        (1, "订阅"),
        (2, "取消订阅"),
        (3, "带场景值扫描事件"),
        (4, "上报地理位置"),
        (5, "点击菜单拉取消息"),
        (6, "点击菜单跳转链接"),
    )

    STATUS_INIT = 0
    STATUS_SYNCED = 200
    STATUS = (
        (STATUS_INIT, "初始化"),
        (STATUS_SYNCED, "已同步"),
    )
    user_id = models.PositiveIntegerField(verbose_name="用户ID")
    gh_id = models.CharField(
        max_length=50, verbose_name="公众号ID", blank=True, null=True
    )
    type = models.SmallIntegerField(verbose_name="消息类型", choices=TYPES, default=0)
    event = models.SmallIntegerField(verbose_name="事件", choices=EVENTS, default=0)
    content = models.TextField(verbose_name="内容", default="")
    raw_data = models.TextField(verbose_name="源数据", default="")
    status = models.SmallIntegerField(
        verbose_name="状态", choices=STATUS, default=STATUS_INIT
    )
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["status", "gh_id"]),
        ]

    @classmethod
    def 设置所有未同步消息为已同步(cls):
        print(
            cls.objects.filter(status=cls.STATUS_INIT).update(status=cls.STATUS_SYNCED)
        )

    @classmethod
    def 最早一条未同步消息(cls, gh_id=None, user_id=None):
        k = {
            k: v
            for k, v in (
                ("status", cls.STATUS_INIT),
                ("gh_id", gh_id),
                ("user_id", user_id),
            )
            if v is not None
        }
        return cls.objects.filter(**k).first()


class AbstractAddress(models.Model):
    user_id = models.PositiveIntegerField(verbose_name="用户ID", blank=True, null=True)
    name = models.CharField(
        verbose_name="收货人姓名", max_length=64, null=True, blank=True
    )
    phone = models.CharField(
        verbose_name="手机号", max_length=20, blank=True, null=True
    )
    area = models.CharField(
        verbose_name="省市地区", max_length=100, blank=True, null=True
    )
    address = models.CharField(
        verbose_name="详细地址", max_length=200, blank=True, null=True
    )
    is_default = models.BooleanField(verbose_name="是否默认地址", default=False)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = []


class AbstractProduct(models.Model):
    STATUS_FOR_SALE = 0
    STATUS_SOLD_OUT = 1
    STATUS_DELETE = 2
    TYPE_CHOICE = (
        (STATUS_FOR_SALE, "在售"),
        (STATUS_SOLD_OUT, "下架"),
        (STATUS_DELETE, "删除"),
    )
    name = models.CharField(
        verbose_name="产品描述", max_length=200, null=True, blank=True
    )
    price = models.DecimalField(
        verbose_name="价格", max_digits=6, decimal_places=2, default=0
    )
    stock = models.IntegerField(verbose_name="库存", default=0)
    weight = models.IntegerField(verbose_name="权重", default=0)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    enabled = models.BooleanField(verbose_name="可用", default=True)
    style = models.CharField(verbose_name="款式", max_length=200, null=True, blank=True)
    json_data = models.TextField(verbose_name="json数据", null=True, blank=True)
    app_id = models.PositiveIntegerField(verbose_name="应用ID", blank=True, null=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["stock"]),
        ]


class AbstractProductImg(models.Model):
    TYPE_SLIDE_SHOW = 0
    TYPE_DETAIL = 1
    TYPE_CHOICE = (
        (TYPE_SLIDE_SHOW, "轮播图"),
        (TYPE_DETAIL, "详情图片"),
    )
    product_id = models.PositiveIntegerField(
        verbose_name="产品ID", blank=True, null=True
    )
    img = models.FileField(
        verbose_name="图片", storage=MyStorage, null=True, blank=True
    )
    # img = models.FileField(verbose_name='图片', null=True, blank=True)
    seq = models.IntegerField(verbose_name="序号", default=0)
    type = models.SmallIntegerField(
        verbose_name="类型", choices=TYPE_CHOICE, default=TYPE_DETAIL
    )
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    enabled = models.BooleanField(verbose_name="可用", default=True)

    class Meta:
        abstract = True
        indexes = []


class AbstractOrder(models.Model):
    STATUS_INIT = 0
    STATUS_PAID = 1
    STATUS_DELIVERED = 2
    STATUS_RECEIVED = 3
    STATUS_COMPLETE = 4
    STATUS_BAD = -1
    TYPE_CHOICE = (
        (STATUS_INIT, "待付款"),
        (STATUS_PAID, "已付款"),
        (STATUS_DELIVERED, "已发货"),
        (STATUS_RECEIVED, "已收货"),
        (STATUS_COMPLETE, "已完成"),
        (STATUS_BAD, "废弃"),
    )
    order_sn = models.CharField(
        verbose_name="订单编号", max_length=40, null=True, blank=True
    )
    user_id = models.PositiveIntegerField(verbose_name="用户ID", blank=True, null=True)
    open_id = models.CharField(
        max_length=50, verbose_name="微信Open ID", blank=True, null=True, unique=True
    )
    external_uuid = models.CharField(
        max_length=32, verbose_name="外部uuid", blank=True, null=True
    )
    amount = models.DecimalField(
        verbose_name="订单金额", max_digits=6, decimal_places=2, default=0
    )
    address = models.CharField(
        verbose_name="详细地址", max_length=200, blank=True, null=True
    )
    status = models.SmallIntegerField(
        verbose_name="状态", choices=TYPE_CHOICE, default=STATUS_INIT
    )
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    is_gen_sn = models.BooleanField(verbose_name="是否需要生成sn", default=False)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["order_sn"]),
            models.Index(fields=["user_id", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["open_id"]),
        ]


class AbstractOrderDetail(models.Model):
    order_id = models.PositiveIntegerField(verbose_name="产品ID", blank=True, null=True)
    user_id = models.PositiveIntegerField(verbose_name="用户ID", blank=True, null=True)
    open_id = models.CharField(
        max_length=50, verbose_name="微信Open ID", blank=True, null=True, unique=True
    )
    product_name = models.CharField(verbose_name="产品描述", max_length=200, default="")
    product_img = models.TextField(
        verbose_name="图片", max_length=200, null=True, blank=True
    )
    quantity = models.IntegerField(verbose_name="数量", default=1)
    price = models.DecimalField(
        verbose_name="价格", max_digits=6, decimal_places=2, default=0
    )
    product_id = models.PositiveIntegerField(
        verbose_name="产品ID", blank=True, null=True
    )
    app_id = models.PositiveIntegerField(verbose_name="应用ID", blank=True, null=True)
    external_app_id = models.PositiveIntegerField(
        verbose_name="应用ID(外部)", blank=True, null=True
    )
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["order_id", "product_name"]),
            models.Index(fields=["user_id"]),
            models.Index(fields=["open_id"]),
        ]


class AbstractPatient(models.Model):
    """
    json字段说明:
        priority_disease 慢病/重点疾病
            - 示例: {"data":[{"name": "xxx", "raw_data":"text..."}]}

            - json字段说明:
                name: 名称

        allergy_history 过敏史
            - 示例: {"data":[{"name": "xxx"}]}
            - json字段说明:
                name: 名称

        contagion 传染病
            - 示例: {"data":[{"name": "xxx"}]}
            - json字段说明:
                name: 名称

        exposure_history 暴露史
            - 示例: {"data":[{"name": "xxx"}]}
            - json字段说明:
                name: 名称

        genetic_disease_history 遗传病史
            - 示例: {"data":[{"name": "xxx"}]}
            - json字段说明:
                name: 名称

        disability 残疾情况
            - 示例: {"data":[{"name": "xxx"}]}
            - json字段说明:
                name: 名称

        past_medical_history 既往史
            - 示例: {"data":[{"name": "疾病", "value": "肺炎","time": "2024-01-01 12:00:00"}], "raw_data":""}
            - json字段说明:
                name: 名称; 包含(疾病, 手术, 外伤, 输血)
                value: 值
                time: 时间

        vaccination_history 预防接种史
            - 示例: {"data":[{"name": "狂犬疫苗xxx","time": "2024-01-01 12:00:00"}], "raw_data":""}
            - json字段说明:
                name: 接种名称
                time: 时间

        family_medical_history 家族史
            - 示例: {"data":[{"name": "父亲", "value": ["高血压"]}], "raw_data":""}
            - json字段说明:
                name: 关系 (父亲, 母亲, 兄弟姐妹, 子女)
                value: 疾病名称
    """

    AUDIT_STATUS = (
        (0, "初始创建"),
        (1, "已获取用户基本信息"),
        (2, "已获取用户手机号"),
        (3, "已获取用户身份信息"),
    )
    USER_GENDER = ((0, "未知"), (1, "男性"), (2, "女性"))
    MARRIAGE = (
        (0, "未知"),
        (1, "未婚"),
        (2, "已婚"),
        (3, "离异"),
        (4, "不详"),
    )

    BLOOD_TYPES = (
        (0, "未知"),
        (1, "A"),
        (2, "B"),
        (3, "O"),
        (4, "AB"),
        (5, "不详"),
    )

    RH_BLOOD_TYPES = (
        (0, "未知"),
        (1, "RH 阴性"),
        (2, "RH 阳性"),
        (3, "不详"),
    )

    MATERNAL_RISK_LEVELS = (
        (0, "未知"),
        (1, "低风险"),
        (2, "一般风险"),
        (3, "较高风险"),
        (4, "高风险"),
        (5, "无"),
    )

    uuid = models.CharField(
        max_length=32, verbose_name="患者唯一id", db_index=True, default=get_uuid
    )
    head_img = models.FileField(
        verbose_name="用户头像", storage=MyStorage, null=True, blank=True
    )
    name = models.CharField(max_length=15, verbose_name="*姓名", null=True)
    name_pinyin = models.CharField(
        max_length=128,
        verbose_name="患者姓名拼音",
        db_index=True,
        blank=True,
        null=True,
    )
    pinyin_target = models.CharField(
        max_length=5,
        verbose_name="姓名首字母标记",
        db_index=True,
        blank=True,
        null=True,
    )
    gender = models.SmallIntegerField(
        choices=USER_GENDER, verbose_name="*性别", default=0
    )
    height = models.SmallIntegerField(
        verbose_name="*身高", help_text="单位：cm", blank=True, null=True
    )
    weight = models.DecimalField(
        verbose_name="*体重",
        help_text="单位：kg",
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )
    marriage = models.SmallIntegerField(
        verbose_name="*婚姻状况", choices=MARRIAGE, default=0
    )
    social_card = models.CharField(
        verbose_name="社保卡号", null=True, blank=True, max_length=100
    )
    social_card_num = models.CharField(
        verbose_name="社会保障号码", null=True, blank=True, max_length=200
    )
    health_card_num = models.CharField(
        verbose_name="电子健康卡号", null=True, blank=True, max_length=200
    )
    job = models.CharField(verbose_name="职业", max_length=32, blank=True, null=True)
    id_card = models.CharField(max_length=18, verbose_name="[身份证号]", null=True)
    birthday_date = models.DateField(null=True, blank=True, verbose_name="出生年月")
    phone = models.CharField(
        max_length=12, verbose_name="[手机号]", null=True, blank=True
    )
    city = models.CharField(max_length=32, verbose_name="城市", null=True, blank=True)
    country = models.CharField(
        max_length=32, verbose_name="国家", null=True, blank=True
    )
    province = models.CharField(
        max_length=32, verbose_name="省份", null=True, blank=True
    )
    active = models.BooleanField(
        default=True, help_text="隐式删除", verbose_name="激活/禁用"
    )
    address = models.CharField(
        max_length=255, verbose_name="地址", null=True, blank=True
    )

    allergy_history = models.TextField(
        verbose_name="过敏史", null=True, blank=True
    )  # 逗号分隔的过敏情况
    priority_disease = models.TextField(
        verbose_name="慢病/重点疾病", null=True, blank=True
    )  # 逗号分隔的疾病名称
    past_medical_history = models.TextField(
        verbose_name="既往病史简介", null=True, blank=True
    )  # json字符串
    contagion = models.TextField(
        verbose_name="传染病", null=True, blank=True
    )  # 逗号分隔的疾病名称: 肺结核, 肝炎, 其他
    exposure_history = models.TextField(
        verbose_name="暴露史", null=True, blank=True
    )  # 逗号分隔的名称: 化学品, 毒物, 射线
    family_medical_history = models.TextField(
        verbose_name="家族史", null=True, blank=True
    )  # json字符串
    genetic_disease_history = models.TextField(
        verbose_name="遗传病史", null=True, blank=True
    )  # 逗号分隔的字符串
    disability = models.TextField(
        verbose_name="残疾情况", null=True, blank=True
    )  # 逗号分隔的字符串: 类型 - 视力残疾, 听力残疾, 语言残疾, 肢体残疾, 智力残疾, 精神残疾, 其他残疾
    vaccination_history = models.TextField(
        verbose_name="预防接种史", null=True, blank=True
    )  # json字符串

    blood_type = models.SmallIntegerField(
        choices=BLOOD_TYPES, verbose_name="血型", default=0
    )
    rh_blood_type = models.SmallIntegerField(
        choices=RH_BLOOD_TYPES, verbose_name="RH血型", default=0
    )

    maternal_risk_level = models.SmallIntegerField(
        choices=MATERNAL_RISK_LEVELS, verbose_name="孕产妇风险等级", default=0
    )

    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    wx_user_id = models.PositiveIntegerField(
        verbose_name="微信用户ID", blank=True, null=True
    )
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    present_medical_history = models.TextField(
        verbose_name="现病史", null=True, blank=True
    )
    chief_complaint = models.TextField(verbose_name="主诉", null=True, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]


class AbstractMedicalHistory(models.Model):
    CREATOR_TYPE_DOCTOR = 0  # 医生
    CREATOR_TYPE_PATIENT = 1  # 患者
    CREATOR_TYPE_SYS = 2  # 系统
    CREATE_TYPE_PATIENT_SYNC = 3  # 患者一键同步
    CREATOR_TYPE = (
        (CREATOR_TYPE_SYS, "系统自动生成"),
        (CREATOR_TYPE_PATIENT, "患者"),
        (CREATOR_TYPE_DOCTOR, "医生"),
        (CREATE_TYPE_PATIENT_SYNC, "患者一键同步"),
    )

    CATE_NORMAL = 0
    CATE_SUMMARY = 1
    CATE_MEASURE = 2
    CATE = (
        (CATE_NORMAL, "健康档案"),
        (CATE_SUMMARY, "健康小结"),
        (CATE_MEASURE, "健康测评"),
    )
    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    treatment_date = models.DateField(help_text="就诊时间", null=True, blank=True)
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    # platform_patient = models.ForeignKey(patient_user_platform,on_delete=models.SET_NULL,null=True)
    # platform = models.ForeignKey(Organization_Business_platform,on_delete=models.SET_NULL,null=True)
    treatment_hospital = models.CharField(
        max_length=32, help_text="就诊医院", blank=True, null=True
    )
    content = models.TextField(verbose_name="病情简介", blank=True, null=True)
    creator_type = models.SmallIntegerField(
        choices=CREATOR_TYPE, default=CREATOR_TYPE_SYS, help_text="创建人"
    )
    # creator = models.SmallIntegerField(choices=CREATOR_TYPE,default=1,help_text='创建人')
    # doctor_creator =models.ForeignKey(Doctor_User_WX,on_delete=models.DO_NOTHING,null=True)
    # content_edit_time = models.DateTimeField(verbose_name="病情简介编辑时间",null=True)
    diagnose_history = models.TextField(verbose_name="json保存会诊记录", null=True)
    # hospital_create_time = models.CharField(max_length=32, help_text='医院创建患者报告时间', null=True)
    diagnosis = models.TextField(verbose_name="诊断", default="")
    treat_advice = models.TextField(
        verbose_name="患者填写诊疗意见", default=""
    )  # 患者创建诊疗意见直接存入主表
    cate = models.SmallIntegerField(choices=CATE, default=0, help_text="类型")
    # channel_id = models.CharField(max_length=100,verbose_name='房间ID', default='')
    is_deleted = models.BooleanField(verbose_name="是否删除", default=False)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    data = models.JSONField(verbose_name="大模型生成的原始数据", null=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = verbose_name_plural = "健康小结"


class AbstractMedicalHistoryReport(models.Model):
    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    medical_history_id = models.PositiveIntegerField(
        verbose_name="健康小结ID", blank=True, null=True
    )
    url = models.URLField(verbose_name="文件地址", null=True, blank=True)
    data = models.TextField(verbose_name="识别结果", null=True, blank=True)
    is_deleted = models.BooleanField(default=False, help_text="是否删除")
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = verbose_name_plural = "报告识别"


class AbstractMedicalHistoryAttachment(models.Model):
    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    medical_history_id = models.PositiveIntegerField(
        verbose_name="健康小结ID", blank=True, null=True
    )
    attach_file = models.FileField(
        verbose_name="文件地址", storage=MyStorage, null=True, blank=True
    )
    is_deleted = models.BooleanField(default=False, help_text="是否删除")
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = verbose_name_plural = "病历附件表"


class AbstractTemperature(models.Model):
    """体温"""

    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    value = models.DecimalField(
        verbose_name="温度",
        help_text="单位: ℃",
        max_digits=3,
        decimal_places=1,
        default=0,
    )
    measure_time = models.DateTimeField(verbose_name="更新时间", default=timezone.now)
    source = models.SmallIntegerField(
        verbose_name="数据来源", choices=MEASURE_SOURCE_CHOICES, default=0
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = "体温记录"
        verbose_name_plural = verbose_name


class AbstractBreath(models.Model):
    """呼吸"""

    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    value = models.SmallIntegerField(
        verbose_name="呼吸", help_text="单位: 次/min", default=0
    )
    measure_time = models.DateTimeField(verbose_name="更新时间", default=timezone.now)
    source = models.SmallIntegerField(
        verbose_name="数据来源", choices=MEASURE_SOURCE_CHOICES, default=0
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = "呼吸记录"
        verbose_name_plural = verbose_name


class AbstractPulse(models.Model):
    """脉搏"""

    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    value = models.SmallIntegerField(
        verbose_name="脉搏", help_text="单位: 次/min", default=0
    )
    measure_time = models.DateTimeField(verbose_name="更新时间", default=timezone.now)
    source = models.SmallIntegerField(
        verbose_name="数据来源", choices=MEASURE_SOURCE_CHOICES, default=0
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = "脉搏记录"
        verbose_name_plural = verbose_name


class AbstractBloodPressure(models.Model):
    """血压"""

    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    systolic_pressure = models.SmallIntegerField(
        verbose_name="收缩压", help_text="单位: mmHg", default=0
    )
    diastolic_pressure = models.SmallIntegerField(
        verbose_name="舒张压", help_text="单位: mmHg", default=0
    )
    heart_rate = models.SmallIntegerField(
        verbose_name="心率", help_text="单位: 次/min", default=0
    )
    measure_time = models.DateTimeField(verbose_name="更新时间", default=timezone.now)
    source = models.SmallIntegerField(
        verbose_name="数据来源", choices=MEASURE_SOURCE_CHOICES, default=0
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = "血压记录"
        verbose_name_plural = verbose_name


class AbstractBloodOxygen(models.Model):
    """血氧"""

    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    value = models.DecimalField(
        verbose_name="血氧",
        help_text="单位: %",
        max_digits=4,
        decimal_places=2,
        default=0,
    )
    perfusion_index = models.DecimalField(
        verbose_name="灌注指数",
        help_text="单位: %",
        max_digits=4,
        decimal_places=2,
        default=0,
    )
    heart_rate = models.SmallIntegerField(
        verbose_name="心率", help_text="单位: 次/min", default=0
    )
    measure_time = models.DateTimeField(verbose_name="更新时间", default=timezone.now)
    source = models.SmallIntegerField(
        verbose_name="数据来源", choices=MEASURE_SOURCE_CHOICES, default=0
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = "血氧记录"
        verbose_name_plural = verbose_name


class AbstractBloodGlucose(models.Model):
    """血糖"""

    MEASURE_CONDITION_CHOICES = (
        (0, "空腹"),
        (1, "餐后两小时"),
        #
        # (1, '早餐后'),
        # (2, '午餐前'),
        # (3, '午餐后'),
        # (4, '晚餐前'),
        # (5, '晚餐后'),
        # (6, '睡前'),
        # (7, '随机'),
    )
    DRUG_USE_CHOICES = (
        (0, "用药前"),
        (1, "用药后"),
    )

    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    value = models.DecimalField(
        verbose_name="血糖",
        help_text="单位: mmol/L",
        max_digits=6,
        decimal_places=2,
        default=0,
    )
    measure_condition = models.SmallIntegerField(
        verbose_name="测量状态", choices=MEASURE_CONDITION_CHOICES, default=0
    )
    drug_use = models.SmallIntegerField(
        verbose_name="用药情况", choices=DRUG_USE_CHOICES, default=0
    )
    measure_time = models.DateTimeField(verbose_name="更新时间", default=timezone.now)
    source = models.SmallIntegerField(
        verbose_name="数据来源", choices=MEASURE_SOURCE_CHOICES, default=0
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = "血糖记录"
        verbose_name_plural = verbose_name


class AbstractUricAcid(models.Model):
    """尿酸"""

    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    value = models.SmallIntegerField(
        verbose_name="尿酸", help_text="单位: μmol/L", default=0
    )
    measure_time = models.DateTimeField(verbose_name="更新时间", default=timezone.now)
    source = models.SmallIntegerField(
        verbose_name="数据来源", choices=MEASURE_SOURCE_CHOICES, default=0
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = "尿酸记录"
        verbose_name_plural = verbose_name


class AbstractBMI(models.Model):
    """BMI"""

    open_id = models.CharField(
        max_length=50, verbose_name="Open ID", blank=True, null=True
    )
    patient_id = models.PositiveIntegerField(
        verbose_name="患者ID", blank=True, null=True
    )
    height = models.SmallIntegerField(
        verbose_name="身高", help_text="单位: cm", default=0
    )
    weight = models.DecimalField(
        verbose_name="体重",
        help_text="单位: kg",
        max_digits=6,
        decimal_places=2,
        default=0,
    )
    measure_time = models.DateTimeField(verbose_name="更新时间", default=timezone.now)
    source = models.SmallIntegerField(
        verbose_name="数据来源", choices=MEASURE_SOURCE_CHOICES, default=0
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["open_id"]),
        ]
        verbose_name = "BMI记录"
        verbose_name_plural = verbose_name


# IM
class AbstractRoom(models.Model):
    ROOM_CHANNEL_TYPE = ((1, "单聊"), (2, "群聊"))
    ROOM_STATUS = ((0, "已解散"), (1, "正常"))
    name = models.CharField(verbose_name="房间名称", max_length=50, null=True)
    code = models.CharField(
        verbose_name="房间唯一编码", max_length=100, default="", unique=True
    )
    channel_type = models.SmallIntegerField(
        verbose_name="房间类型", choices=ROOM_CHANNEL_TYPE, default=1
    )
    last_message_id = models.BigIntegerField(
        verbose_name="房间内最新消息的ID", default=0
    )
    out_time = models.BigIntegerField(verbose_name="到期时间", default=0)
    status = models.SmallIntegerField(
        verbose_name="房间状态", choices=ROOM_STATUS, default=1
    )
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["channel_type"]),
        ]
        verbose_name_plural = verbose_name = "房间"

    @classmethod
    def get_room_by_code(cls, code, to_dict=True):
        record, _ = cls.objects.get_or_create(code=code)
        if to_dict:
            return model_to_dict(record)
        else:
            return record


class AbstractRoomUser(models.Model):
    ROOM_ROLE_TYPE_KF = 1
    ROOM_ROLE_TYPE_PATIENT = 2
    ROOM_ROLE_TYPE = (
        (ROOM_ROLE_TYPE_KF, "客服机器人"),
        (ROOM_ROLE_TYPE_PATIENT, "患者"),
    )

    room_id = models.PositiveIntegerField(verbose_name="房间ID", blank=True, null=True)
    # role为ROOM_ROLE_TYPE_KF时, user_id为RobotKF表ID, role为ROOM_ROLE_TYPE_PATIENT时, 为Patient表的uuid
    user_id = models.CharField(verbose_name="用户id", max_length=64)
    role = models.SmallIntegerField(
        verbose_name="成员角色类型", choices=ROOM_ROLE_TYPE, default=1
    )
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["room_id"]),
            models.Index(fields=["role"]),
        ]
        verbose_name_plural = verbose_name = "房间成员"


class AbstractMessage(models.Model):
    MESSAGE_SENDER_TYPE_SERVER = 3
    MESSAGE_SENDER_TYPE = (
        (0, "unknown"),
        (1, "im系统"),
        (2, "用户"),
        (MESSAGE_SENDER_TYPE_SERVER, "业务服务器"),
    )
    MESSAGE_TYPE = (
        (1, "文本"),
        (2, "表情"),
        (3, "语音"),
        (4, "图片"),
        (5, "视频"),
        (6, "转诊"),
        (7, "预约服务"),
        (8, "自定义"),
        (9, "患者健康档案"),
        (10, "系统提示信息"),
        (11, "患者名片"),
        (12, "健康评估"),
        (13, "健康小结"),
        (14, "健康小结回复"),
    )
    MESSAGE_RECEIVER_TYPE = (
        (0, "unknown"),
        (1, "用户"),
        (2, "群组"),
    )
    MESSAGE_STATUS = ((0, "unknown"), (1, "正常"), (2, "已撤回"))
    room_id = models.PositiveIntegerField(
        verbose_name="当前消息所属房间ID", blank=True, null=True
    )
    content = models.CharField(verbose_name="消息内容", max_length=4094)
    sender_id = models.CharField(verbose_name="发送者ID", max_length=64)
    sender_type = models.SmallIntegerField(
        verbose_name="发送者类型", choices=MESSAGE_SENDER_TYPE, default=2
    )
    receiver_type = models.SmallIntegerField(
        verbose_name="接收者类型", choices=MESSAGE_RECEIVER_TYPE, default=1
    )
    type = models.SmallIntegerField(
        verbose_name="消息类型", choices=MESSAGE_TYPE, default=1
    )
    request_id = models.BigIntegerField(verbose_name="请求id", default=0)
    send_time = models.DateTimeField(verbose_name="发送时间", auto_now_add=True)
    status = models.SmallIntegerField(
        verbose_name="消息状态", choices=MESSAGE_STATUS, default=1
    )
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["room_id"]),
            models.Index(fields=["sender_id"]),
        ]
        verbose_name_plural = verbose_name = "消息"


class AbstractMessageRead(models.Model):
    message_id = models.PositiveIntegerField(
        verbose_name="消息ID", blank=True, null=True
    )
    room_id = models.PositiveIntegerField(verbose_name="房间ID", blank=True, null=True)
    user_id = models.CharField(verbose_name="用户id", max_length=64)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["message_id"]),
            models.Index(fields=["user_id"]),
        ]
        verbose_name_plural = verbose_name = "消息读取状态"


class AbstractChannel(models.Model):
    ActiveType = ((0, "无效"), (1, "有效"))
    name = models.CharField(verbose_name="ws channel句柄", max_length=255)
    user_id = models.CharField(verbose_name="用户id", max_length=64)
    is_active = models.SmallIntegerField(
        choices=ActiveType, default=0, help_text="有效状态"
    )
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        abstract = True
        indexes = []
        verbose_name_plural = verbose_name = "通道"


class AbstractRobotKF(models.Model):
    name = models.CharField(verbose_name="姓名", max_length=50)

    class Meta:
        abstract = True
        indexes = []
        verbose_name_plural = verbose_name = "客服机器人"


class AbstractSn(models.Model):
    sn = models.CharField(verbose_name="注册码", max_length=64, default="")
    order_id = models.PositiveIntegerField(verbose_name="订单ID", blank=True, null=True)
    uuid = models.CharField(max_length=32, verbose_name="uuid", blank=True, null=True)
    external_uuid = models.CharField(
        max_length=32, verbose_name="外部uuid", blank=True, null=True
    )

    class Meta:
        abstract = True
        indexes = [models.Index(fields=["sn"]), models.Index(fields=["external_uuid"])]
        verbose_name_plural = verbose_name = "注册码"


class AbstractApp(models.Model):
    name = models.CharField(verbose_name="应用名称", max_length=30)
    external_app_id = models.CharField(verbose_name="app id", max_length=30)

    class Meta:
        abstract = True
        indexes = []
        verbose_name_plural = verbose_name = "应用"
