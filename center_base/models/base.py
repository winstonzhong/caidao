import json

from django.db import models
from django.utils.functional import cached_property

from tool_gzip import gzip_decompress


DEVICE_PC = 0
DEVICE_HUAWEI_MATE10 = 1
DEVICE_HONOR_V50 = 2

DEVICE_CHOICES = (
    (DEVICE_PC, 'pc'),
    (DEVICE_HUAWEI_MATE10, 'huawei_mate10'),
    (DEVICE_HONOR_V50, 'honor_v50'),
)


class AbstractNote(models.Model):
    """笔记"""
    NOTE_STATUS_DEFAULT = 0
    NOTE_STATUS_PUSHED = 1
    NOTE_STATUS_NEED_REPLY = 2
    NOTE_STATUS_REPLIED = 3
    NOTE_STATUS_REPLY_FAILED = 4
    NOTE_STATUS_INVALID = 100
    NOTE_STATUS_DELETED = 200
    NOTE_STATUS_TOOMANY_REPLIES = 201
    NOTE_STATUS_DESC_TOO_LONG = 202

    NOTE_STATUS_CHOICES = (
        (NOTE_STATUS_DEFAULT, "初始状态"),
        (NOTE_STATUS_PUSHED, "已生成搭讪回复"),
        (NOTE_STATUS_NEED_REPLY, "待回复"),
        (NOTE_STATUS_REPLIED, "已回复"),
        (NOTE_STATUS_REPLY_FAILED, "回复失败"),
        (NOTE_STATUS_INVALID, "无效"),
        (NOTE_STATUS_DELETED, "删除"),
        (NOTE_STATUS_TOOMANY_REPLIES, "太多回复"),
        (NOTE_STATUS_DESC_TOO_LONG, "正文太长，疑似营销贴"),
        
    )

    NOTE_TYPE_UNKNOWN = 0
    NOTE_TYPE_NORMAL = 1
    NOTE_TYPE_VIDEO = 2
    NOTE_TYPE_CHOICES = (
        (NOTE_TYPE_UNKNOWN, '未知'),
        (NOTE_TYPE_NORMAL, '图文'),
        (NOTE_TYPE_VIDEO, '视频'),
    )

    note_type = models.SmallIntegerField(verbose_name="笔记类型", default=NOTE_TYPE_UNKNOWN, choices=NOTE_TYPE_CHOICES,
                                         db_index=True)
    source_note_id = models.CharField(max_length=50, verbose_name='笔记ID', default='', unique=True, db_index=True)
    title = models.CharField(max_length=50, verbose_name='笔记标题', default='')
    content = models.BinaryField(verbose_name='笔记内容',  blank=True, null=True)
    user_id = models.CharField(max_length=50, verbose_name='用户ID', default='')
    nickname = models.CharField(max_length=50, verbose_name='用户昵称', default='')
    liked_count = models.IntegerField(verbose_name="点赞数", default=0)
    reply_count = models.IntegerField(verbose_name="回复数", default=0)
    status = models.SmallIntegerField(verbose_name="状态", default=NOTE_STATUS_DEFAULT, choices=NOTE_STATUS_CHOICES,
                                      db_index=True)
    search_key = models.CharField(max_length=50, verbose_name='搜索词', default='', db_index=True)
    bin_data = models.BinaryField(null=True, blank=True,verbose_name="源数据")
    need_push = models.BooleanField(verbose_name='是否推送', default=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


    @cached_property
    def json(self):
        try:
            return json.loads(gzip_decompress(self.bin_data).decode('utf8'))
        except:
            return {}


class AbstractNoteImg(models.Model):
    """笔记图片"""
    url = models.TextField(verbose_name='图片url', default='')
    file_id = models.CharField(max_length=50, verbose_name='图片ID', default='', db_index=True)
    note_id = models.IntegerField(verbose_name="笔记ID", default=0, db_index=True)
    is_base_img = models.BooleanField(verbose_name='是否底图', default=False)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractNoteReplyImg(models.Model):
    """笔记回复图片"""

    STATUS_DEFAULT = 0
    STATUS_REPLIED = 1
    STATUS_REPLY_FAILED = -1
    STATUS_NOTE_RECORD_NOT_FOUND = -2
    STATUS_CHECK_PIC_ICON_FAIL = 101
    STATUS_CHECK_PIC_ALBUM_FAIL = 102
    STATUS_CHECK_CHECK_IS_IN_XHS = 201
    STATUS_CHECK_IS_IN_MY_HOME = 202
    STATUS_CHECK_HAS_SCAN_BTN = 203
    STATUS_CHECK_IS_IN_SCAN_PAGE = 204
    STATUS_CHECK_IS_IN_SCAN_PIC_SELECT_PAGE = 205
    STATUS_CHECK_HAS_IN_REPLY_PAGE = 206
    STATUS_CHECK_HAS_IMG_SELECT_BTN = 301
    STATUS_CHECK_IS_IN_PIC_SELECT_PAGE = 302
    STATUS_CHECK_HAS_NEXT_BTN = 303
    STATUS_CHECK_HAS_INPUT_POPUP = 401
    STATUS_CHECK_HAS_SUBMIT_BTN = 501
    STATUS_CHECK_IS_IN_NOTE_PAGE = 502

    STATUS_CHOICES = (
        (STATUS_DEFAULT, '未回复'),
        (STATUS_REPLIED, '已回复'),
        (STATUS_REPLY_FAILED, '回复失败'),
        (STATUS_NOTE_RECORD_NOT_FOUND, '未找到有效的笔记'),
        (STATUS_CHECK_PIC_ICON_FAIL, '打开文件管理器失败'),
        (STATUS_CHECK_PIC_ICON_FAIL, '打开图片集失败'),
        (STATUS_CHECK_CHECK_IS_IN_XHS, '进入小红书失败'),
        (STATUS_CHECK_IS_IN_MY_HOME, '打开左侧"我"的菜单失败'),
        (STATUS_CHECK_HAS_SCAN_BTN, '查找"扫一扫"按钮失败'),
        (STATUS_CHECK_IS_IN_SCAN_PAGE, '打开扫一扫页面失败'),
        (STATUS_CHECK_IS_IN_SCAN_PIC_SELECT_PAGE, '从相册中选择图片进行扫码失败'),
        (STATUS_CHECK_HAS_IN_REPLY_PAGE, '进入笔记主页失败'),
        (STATUS_CHECK_HAS_IMG_SELECT_BTN, '回帖查找图片选择按钮失败'),
        (STATUS_CHECK_IS_IN_PIC_SELECT_PAGE, '回帖进入选择图片页面失败'),
        (STATUS_CHECK_HAS_NEXT_BTN, '回帖预览图片打开失败'),
        (STATUS_CHECK_HAS_INPUT_POPUP, '回复文字弹出输入/回复框失败'),
        (STATUS_CHECK_HAS_SUBMIT_BTN, '发帖弹出输入/回复框失败'),
        (STATUS_CHECK_IS_IN_NOTE_PAGE, '发帖失败'),
    )

    status = models.SmallIntegerField(verbose_name="状态", default=STATUS_DEFAULT, choices=STATUS_CHOICES, db_index=True)
    img_id = models.IntegerField(verbose_name='图片id', default=0, blank=True, null=True)  # 废弃
    img_url = models.TextField(verbose_name='图片url', default='', blank=True, null=True)
    # reply_txt = models.CharField(verbose_name='回复内容', max_length=100, blank=True, null=True)
    reply_txt = models.TextField(verbose_name='回复内容', blank=True, null=True)
    at = models.CharField(max_length=100, verbose_name='@用户', blank=True, null=True)
    source_img_id = models.IntegerField(verbose_name="原图ID", default=0, db_index=True)
    note_id = models.IntegerField(verbose_name="笔记ID", default=0, db_index=True)
    device_id = models.SmallIntegerField(verbose_name="设备", default=DEVICE_HUAWEI_MATE10, choices=DEVICE_CHOICES,
                                         db_index=True)
    result_pic = models.FileField(verbose_name='回复结果截图', blank=True, null=True, upload_to='reply_screenshots/')
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractSearchKey(models.Model):
    """搜索关键词"""
    keyword = models.CharField(max_length=50, verbose_name='关键词', default='', db_index=True)
    is_on = models.BooleanField(verbose_name='是否启用', default=True, db_index=True)
    is_crawl_now = models.BooleanField(verbose_name='是否立即爬取', default=False, db_index=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    @classmethod
    def get_keywords(cls):
        return list(cls.objects.filter(is_on=True).values_list('keyword', flat=True))

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert=False, force_update=False, using=None,
                     update_fields=None)

    class Meta:
        abstract = True


class AbstractPlateformUser(models.Model):
    """平台用户表"""

    PLATEFORM_XHS = 0
    PLATEFORM_CHOICES = (
        (PLATEFORM_XHS, '小红书'),
    )

    plateform_id = models.SmallIntegerField(verbose_name="平台", default=PLATEFORM_XHS, choices=PLATEFORM_CHOICES,
                                            db_index=True)
    name = models.CharField(verbose_name='用户名', max_length=50, default='')
    source_user_id = models.CharField(verbose_name='平台用户ID', max_length=50, default='')
    device_id = models.SmallIntegerField(verbose_name="回帖设备", default=DEVICE_HUAWEI_MATE10, choices=DEVICE_CHOICES,
                                         db_index=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True


class AbstractNoteReply(models.Model):
    """笔记回复"""

    KEY_EXISTED = 0
    KEY_LIKE_COUNT = 1
    KEY_REPLY = 2
    KEY_CHOICES = (
        (KEY_EXISTED, '存在检查'),
        (KEY_LIKE_COUNT, '点赞数'),
        (KEY_REPLY, '回复点评')
    )

    volume_type = {
        KEY_EXISTED: 'latest',
        KEY_LIKE_COUNT: 'max',
        KEY_REPLY: 'count'
    }

    key = models.SmallIntegerField(verbose_name="平台", default=KEY_EXISTED, choices=KEY_CHOICES, db_index=True)
    note_id = models.IntegerField(verbose_name="笔记ID", default=0, db_index=True)
    source_reply_id = models.CharField(max_length=50, verbose_name='回复ID', default='', db_index=True)
    replier_id = models.IntegerField(verbose_name='评论者ID', null=True, blank=True)
    volume = models.IntegerField(verbose_name='数量', default=0)
    bin_data = models.BinaryField(verbose_name='数据', null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        abstract = True
