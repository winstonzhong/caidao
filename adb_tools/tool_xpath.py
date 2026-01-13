"""
Created on 2023年12月21日

@author: lenovo
"""

import io
import os
import time

import cv2
from uiautomator2.xpath import XPath, XMLElement

from helper_hash import get_hash
from tool_env import bounds_to_rect
from tool_img import (
    get_template_points,
    show,
    pil2cv2,
    cv2pil,
    b642cv2,
    cv2jpg_b64,
    is_cv2_image,
    cv2_img_to_bytesio,
)
import image_hash_comparison
from lxml import etree

import tool_time

import functools

import json

import pandas

import numpy

import lxml

import tool_file

from functools import cached_property

import tool_pandas

from tool_exceptions import (
    任务预检查不通过异常,
    达到最大重复次数异常,
    达到最大空白屏次数异常,
    没有找到联系人异常,
)

from tool_remote_orm_model import RemoteModel

from tool_wx_container import 解析器, 获取3P列表详情, 获取列表详情

import itertools

import tool_wx_df

import tool_wx_df3

import tool_wx_df4

import tool_static

import traceback

import tool_wx

import requests

import tool_env

import check_series_contains

import tool_dict

import random

import re

from urllib.parse import urljoin

import tool_wx_groupname

from tool_wx_groupname import 随机生成低风险微信群名字

from douyin.tool_dy_score import (
    精确获取文本中的数字,
    计算评论价值评分,
    计算下一次运行等待秒数,
    计算视频价值评分,
)

from douyin import tool_dy_utils

from helper_task_redis2 import GLOBAL_REDIS

import helper_task_redis2

from mobans import tool_moban_configs

global_redis = GLOBAL_REDIS

global_cache = tool_dict.PropDict()

global_rom = tool_dict.PropDict()

全局缓存 = global_cache

全局队列 = global_redis

URL_TASK_QUEUE = f"https://{tool_env.HOST_TASK}"

namespaces = {"re": "http://exslt.org/regular-expressions"}


def 得到url(task_key, 中继=False):
    return f'{URL_TASK_QUEUE}/pull/{task_key}{"_" if 中继 else ""}'


def 在队列中是否有任务(task_key, 中继=False):
    url = f"{得到url(task_key, 中继)}?query_only=1"
    # print("在队列中是否有任务:", url)
    return bool(requests.get(url).json())


def 拉取任务字典(task_key, 中继=False):
    url = 得到url(task_key, 中继)
    print("拉取任务字典:", url)
    return requests.get(url).json()


def 如有任务转发中继(task_key):
    url = f"{URL_TASK_QUEUE}/pull/{task_key}?forward={task_key}_"
    return bool(requests.get(url).json())


def 上传结果字典(task_key, result_data):
    url = f"{URL_TASK_QUEUE}/push"
    print("上传结果字典:", url)

    data = {
        "result_key": task_key,
        "result_data": result_data,
    }

    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(data),
    )

    response.raise_for_status()
    return response.json()


def 回传结果到服务器(result_data, **paras):
    # paras = paras or {}
    return 上传结果字典(
        task_key="服务器回传结果队列", result_data={**result_data, **paras}
    )


def execute_lines(job, lines, self=None):
    if self is not None:
        if self.matched:
            exec(lines)
            return True
    else:
        exec(lines)


def retrying(tries):
    """
    重试装饰器，允许指定重试次数

    参数:
        tries: 重试次数
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, tries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"尝试 {attempt}/{tries} 失败: {str(e)}")
                    if attempt < tries:
                        time.sleep(1)  # 避免立即重试
            raise last_exception  # 所有尝试均失败后抛出最后一个异常

        return wrapper

    return decorator


@retrying(3)
def 查询图片url(key):
    url = urljoin(tool_env.HOST_URL, "wx_msgs/img_query")
    return requests.get(url, params={"key": key}).json().get("url")


def 解析列表条目(e, debug=False):
    data_list = e.elem.xpath("//android.widget.ListView/android.widget.LinearLayout")

    assert data_list, "没有找到列表"

    top_nav = e.elem.xpath(
        '//android.view.ViewGroup/android.widget.RelativeLayout/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView[re:match(@text,"微信.*")][re:match(@content-desc,"")]/../../../../..',
        namespaces=namespaces,
    )

    assert top_nav, "没有找到顶部导航栏"

    rect_top_nav = bounds_to_rect(top_nav[0].attrib.get("bounds"))

    bottom_nav = e.elem.xpath(
        '//android.widget.LinearLayout/android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.TextView[@text="通讯录"][@content-desc=""]/../../..'
    )

    assert bottom_nav, "没有找到底部导航栏"

    rect_bottom_nav = bounds_to_rect(bottom_nav[0].attrib.get("bounds"))

    # print(rect_bottom_nav)

    rtn = []
    for i, x in enumerate(data_list):
        tmp = x.xpath(".//android.view.View")
        if not tmp:
            continue
        tmp = tmp[0]
        bounds = tmp.attrib.get("bounds")
        center_y = bounds_to_rect(bounds).center_y
        if debug:
            print(
                i,
                tmp.attrib.get("text"),
                bounds,
                center_y,
                center_y > rect_top_nav.bottom and center_y < rect_bottom_nav.top,
            )
        if center_y > rect_top_nav.bottom and center_y < rect_bottom_nav.top:
            rtn.append(tmp)
    return rtn


def 匹配列表中的第一个并点击(e, name, debug=False):
    el = 解析列表条目(e, debug=debug)
    for x in el:
        if x.attrib.get("text") == name:
            e._d.click(*bounds_to_rect(x.attrib["bounds"]).center)
            return True


class NoTemplatePopupException(Exception):
    pass


class DummyWatcher(object):
    def run(self, xml_content):
        return False


class XpathNotFoundException(Exception):
    pass


class 对齐历史到顶部异常(Exception):
    pass


class 同步消息到底部异常(Exception):
    pass


class DummyDevice(object):
    def __init__(self, fpath=None, adb=None, xml=None):
        if xml is None:
            with open(fpath, "r", encoding="utf8") as fp:
                xml = fp.read()
        self.init(xml)
        self.adb = adb

    def init(self, source, wait_timeout=0.01):
        self.source = source
        self.settings = {"xpath_debug": False}
        self.watcher = DummyWatcher()
        self.wait_timeout = wait_timeout

    def dump_hierarchy(self):
        return self.source

    def __getattr__(self, name):
        pass

    def click(self, *a, **k):
        return self.adb.ua2.click(*a, **k)

    def click_element(self, element, offset_x=0.5, offset_y=0.5, abs_x=0, abs_y=0):
        rect = bounds_to_rect(element.attrib["bounds"])
        if rect is not None:
            x, y = rect.offset(offset_x, offset_y)
            x += abs_x
            y += abs_y
            # print("clicking:", x, y)
            self.click(x, y)
        # self.click(*bounds_to_rect(element.attrib["bounds"]).center)

    def swipe(self, fromx, fromy, tox, toy):
        return self.adb.swipe((fromx, fromy), (tox, toy))

    def long_click(self, *a, **k):
        # print(a, k)
        # return self.adb.ua2.long_click(*a, **k)
        self.adb.do_longclick(*a)

    def move_to(self, *a, **k):
        print(a, k)

    def find_xpath_safe(self, x):
        return find_by_xpath(self, x)


class SnapShotDevice(DummyDevice):
    def __init__(self, adb):
        self.adb = adb
        self.init(adb.ua2.dump_hierarchy(), 0)

    def find_xpath_safe(self, x):
        return find_by_xpath(self, x)

    def screenshot(self):
        return self.img

    def crop_bounds(self, bounds):
        return bounds_to_rect(bounds).crop_img(pil2cv2(self.img))

    def show_bounds(self, bounds):
        show(self.crop_bounds(bounds))


class SteadyDevice(DummyDevice):
    def __init__(self, adb, old_key=None, need_screen=False, need_xml=True):
        self.adb = adb
        self.settings = {"xpath_debug": False}
        self.watcher = DummyWatcher()
        self.wait_timeout = 0
        self.key = None
        self.need_screen = need_screen
        self.need_xml = need_xml
        self.img = None
        self.source = None
        # self.容器列表 = []
        self.refresh()

    def parse_element(self, e):
        rtn = []
        e = e if isinstance(e, lxml.etree._Element) else e.elem
        for x in e.xpath(".//*"):
            text = x.attrib.get("text") or ""
            desc = x.attrib.get("content-desc") or ""
            if text or desc:
                rtn.append(f"{text} {desc}")
        return rtn

    def element2text(self, e):
        return " ".join([x.strip() for x in self.parse_element(e) if x.strip()])

    def print_results(self, results):
        records = []
        for e in results:
            records.append(self.parse_element(e))

        for i, x in enumerate(records):
            print("=" * 50)
            print(x)
            print("=" * 50)

    def widget_to_element(self, w):
        return XMLElement(w, XPath(self))

    def open_app_safe(self, package, activity):
        script = f"am start -n {package}/{activity}"
        # print(script)
        self.adb.execute(script)
        time.sleep(3)
        self.refresh()
        print("checking...:")
        if not self.find_xpath_all(f'//android.widget.TextView[@package="{package}"]'):
            self.adb.open_certain_app(
                package=package,
                activity=activity,
                stop=True,
            )

    def snapshot(self, wait_steady=False):
        if self.need_screen:
            self.img = self.adb.screenshot()
        self.refresh(wait_steady=wait_steady)

    @classmethod
    def from_ip_port(cls, ip_port=None):
        from adb_tools.helper_adb import BaseAdb

        adb = BaseAdb.first_adb() if ip_port is None else BaseAdb.from_ip_port(ip_port)
        return cls(adb)

    def 拷贝环境(self, other):
        self.key = other.key
        self.source = other.source

    def get_hash_key(self, xml):
        t = etree.fromstring(xml.encode("utf8"))
        e = t.xpath(
            '//node[@class="android.widget.FrameLayout"][@package="com.android.systemui"][@resource-id=""]'
        )
        if e:
            e = e[0]
            t.remove(e)
            # xml = t.tostring().decode('utf8')
            xml = etree.tostring(t, encoding="utf8").decode("utf8")
        key = get_hash(xml)
        return key

    def refresh(self, debug=True, wait_steady=False):
        if self.need_xml:
            old_key = None
            max_try = 6
            for i in range(max_try):
                xml_dumped = self.adb.ua2.dump_hierarchy()
                # key = get_hash(xml_dumped)
                key = self.get_hash_key(xml_dumped)
                if wait_steady and old_key != key and i < max_try - 1:
                    print(f"waiting xml tobe steady:...{i}") if debug else None
                    old_key = key
                    time.sleep(0.1)
                else:
                    self.key = key
                    self.source = xml_dumped
                    break

    def find_xpath_safe(self, x, wait=False, retries=3):
        for i in range(retries):
            e = find_by_xpath(self, x)
            if wait and not e.all():
                print(f"not found:{x}, retry {i}/{retries}")
                self.refresh()
            else:
                return e
        raise XpathNotFoundException(f"xpath not found:{x}")

    def find_xpath_all(self, x, wait=False, retries=3):
        return self.find_xpath_safe(x, wait, retries).all()

    def find_xpath_first(self, x, wait=False, retries=3):
        l = self.find_xpath_safe(x, wait, retries).all()
        return l[0] if l else None

    def find_xpath_last(self, x, wait=False, retries=3):
        l = self.find_xpath_safe(x, wait, retries).all()
        return l[-1] if l else None

    def has_xpath(self, x, wait=False, retries=3):
        return bool(self.find_xpath_safe(x, wait, retries).all())

    def send_keys(self, keys, clear=True):
        self.adb.ua2.send_keys(keys, clear)

    def 上传到下载目录(self, url, fname=None, clean_temp=True):
        if tool_static.is_inner():
            fpath = tool_static.链接到路径(url)
            return self.adb.push_file_to_download(
                fpath,
                fname=fname,
                clean_temp=clean_temp,
            )
        else:
            """
            根据url的文件名匹配robot temp下的文件
            并且将此文件拷贝至download目录
            """
            src = f"/sdcard/Download/{fname or os.path.basename(url)}"
            fpath = tool_static.存储链接到文件(
                url, suffix=None, 返回路径=True, fpath=src
            )
            print("src:", src)
            time.sleep(0.1)
            self.adb.broadcast(src)
            return src

    @property
    def container_wx(self):
        return 解析器(xml=self.source)

    # def 记录容器快照(self):
    #     self.容器列表.append(self.container_wx)

    @property
    def df_wx(self):
        return self.container_wx.上下文df

    def merge_wx_df(self, upper_page, lower_page):
        rtn = tool_wx_df.合并上下两个df(上一页=upper_page, 当前页=lower_page, safe=True)
        rtn["新增"] = True
        if "自己" not in rtn.columns:
            rtn["自己"] = False
        else:
            rtn.自己 = rtn.自己.fillna(False)
        return rtn

    @property
    def remote_fpath_wx_images(self):
        return "/sdcard/Pictures/WeiXin"

    @property
    def remote_fpath_temp(self):
        return "/sdcard/robot_temp"

    def clear_remote_wx_images(self):
        self.adb.clear_temp_dir(self.remote_fpath_wx_images)

    def 将手机文件上传56T(self, token=None, 手机端路径=None):
        手机端路径 = 手机端路径 or self.remote_fpath_wx_images
        if tool_static.is_inner():
            fpath = self.adb.pull_lastest_file_until(base_dir=手机端路径, to_56T=True)
            return tool_static.路径到链接(fpath)
        else:
            """
            下载该文件到本地
            上传至56T
            源文件移动至robot临时目录且按照56T链接返回的文件名(可选touch)
            """
            fpath = self.adb.pull_lastest_file_until(
                base_dir=手机端路径, to_56T=False, clear_tmp_dir=True
            )
            url = tool_static.upload_file_by_path(fpath, token)
            fname = url.split("/")[-1]
            src = self.adb.get_latest_file(base_dir=手机端路径)
            self.adb.move_file_to_robot_temp(src, fname)
            return url

    def download_wx_image(self, token=None):
        return self.将手机文件上传56T(
            token=token, 手机端路径=self.remote_fpath_wx_images
        )

    def 下载微信图片并返回链接和唯一码_内网(self):
        fpath = self.adb.pull_lastest_file_until(
            base_dir=self.remote_fpath_wx_images, to_56T=True
        )
        return tool_static.路径到链接(
            fpath
        ), image_hash_comparison.compute_noise_robust_hash_fpath(fpath)

    def 下载微信图片并返回链接和唯一码_外网(self, token):
        fpath = self.adb.pull_lastest_file_until(
            base_dir=self.remote_fpath_wx_images, to_56T=False, clear_tmp_dir=True
        )
        # print("fpath:", fpath)
        img_key = image_hash_comparison.compute_noise_robust_hash_fpath(fpath)
        url = 查询图片url(img_key)

        if url is None:
            url = tool_static.upload_file_by_path(fpath, token)
        return url, img_key

    def 下载微信图片并返回链接和唯一码(self, token):
        if tool_static.is_inner():
            return self.下载微信图片并返回链接和唯一码_内网()
        else:
            return self.下载微信图片并返回链接和唯一码_外网(token)

    def 点击并上传手机端文件(self, e, token, 手机端路径):
        # self.clear_remote_wx_images()
        self.adb.clear_temp_dir(手机端路径)
        e.click()
        time.sleep(1)
        return self.将手机文件上传56T(token, 手机端路径)

    def 点击并上传手机端微信图片(self, e, token):
        return self.点击并上传手机端文件(e, token, self.remote_fpath_wx_images)

    def cut_wx_df(self, df):
        tmp = df[df.自己]
        if not tmp.empty:
            return df.loc[tmp.index[-1] :].copy()
        return df

    @property
    def wx_session_name(self):
        data_list = self.find_xpath_all(
            "//android.view.ViewGroup//android.widget.TextView"
        )
        data_list = sorted(data_list, key=lambda x: x.center()[1])
        return data_list[0].attrib.get("text") if data_list else None

    def is_wx_group(self, name=None):
        name = name if name else self.wx_session_name
        return tool_wx.is_session_name(name)

    @property
    def wx_session_pair(self):
        name = self.wx_session_name
        return name, tool_wx.is_session_name(name)

    def 四重击(self, x, y):
        self.adb.do_double_click(x, y)
        self.adb.特殊双击(x, y)

    @property
    def xpath_更多信息_微信(self):
        return '//android.widget.ImageView[re:match(@text,"")][re:match(@content-desc,"聊天信息|更多信息")]'

    @property
    def 微信会话名称(self):
        x = f"{self.xpath_更多信息_微信}/../../../../..//android.widget.TextView"
        e = self.find_xpath_first(x)
        return e.text if e is not None else ""

    def 是否微信群聊(self):
        return tool_wx.is_session_name(self.微信会话名称)

    @property
    def 干净的微信会话名称(self):
        return tool_wx.clean_session_name(self.微信会话名称)


class 基本输入字段对象(object):
    def __init__(self, d):
        self.d = d

    @property
    def id(self):
        return self.d.get("id")

    @property
    def serialno(self):
        raise NotImplementedError

    @classmethod
    def process_url(cls, url):
        return tool_env.replace_url_host(url, tool_env.HOST_SERVER)

    def requests_get(self, url, 带串行号=True, **kwargs):
        obj = self.get_remote_obj(self.process_url(url), 带串行号=带串行号, **kwargs)
        return obj if obj.data else None

    def requests_post(self, url, 带串行号=True, **kwargs):
        payload = {"设备串行号": self.serialno} if 带串行号 else {}
        for key, value in kwargs.items():
            if isinstance(value, (dict, list)):
                payload[key] = json.dumps(value)
            else:
                payload[key] = value
        response = requests.post(self.process_url(url), data=payload)
        response.raise_for_status()


class 基本界面元素(基本输入字段对象):
    def __init__(self, d):
        super().__init__(d)
        self.matched = False

    @property
    def paras(self):
        return self.d.get("paras", {}) or {}

    @paras.setter
    def paras(self, v):
        self.d["paras"] = v

    @property
    def inverse(self):
        return self.d.get("inverse")

    @classmethod
    def from_dict(cls, d, paras=None):
        d["paras"] = paras or {}
        if d.get("type") == 1:
            return Xml界面元素(d)
        else:
            return Screen界面元素(d)

    def match(self, job):
        raise NotImplementedError

    def execute(self, job, lines):
        return execute_lines(job, lines, self)


class Xml界面元素(基本界面元素):
    @property
    def xpath(self):
        return self.d.get("xpath").format(**self.paras)

    def match(self, job):
        self.results = find_by_xpath(job.device, self.xpath).all()
        self.matched = (
            bool(self.results) if not self.inverse else not bool(self.results)
        )


class Screen界面元素(基本界面元素):
    @cached_property
    def img(self):
        return b642cv2(self.d.get("img"))


class Windows窗口设备(基本输入字段对象):
    def __init__(self, d):
        super().__init__(d)
        self.hwnd = 0

    @property
    def title(self):
        return self.d.get("title")

    @property
    def clsname(self):
        return self.d.get("clsname")

    def get_hwnd(self):
        import win32gui
        from helper_win32 import SEARCH_WINDOWS

        if not win32gui.IsWindow(self.hwnd):
            l = SEARCH_WINDOWS(title=self.title, clsname=self.clsname)
            self.hwnd = l[0] if l else 0
        return self.hwnd

    def snapshot(self, wait_steady=False):
        from helper_win32 import SCREENSHOT

        print(f"snapshot window:{self.get_hwnd()}")
        self.img = pil2cv2(SCREENSHOT(self.get_hwnd()))


class 操作块(基本输入字段对象):
    def __init__(self, d, paras):
        super().__init__(d)
        d["paras"] = paras
        self.tpls = [基本界面元素.from_dict(x, self.paras) for x in d.get("tpls")]
        self.num_executed = 0
        self.num_conti_repeated = 0

    def is_precheck(self):
        return not bool(self.tpls)

    def 清除重复计数器(self):
        self.num_conti_repeated = 0

    # def 刷新参数(self, paras):
    #     self.paras = paras
    #     for tpl in self.tpls:
    #         tpl.paras = paras

    @property
    def paras(self):
        return self.d.get("paras", {}) or {}

    @property
    def lines(self):
        return self.d.get("lines")

    def execute(self, job):
        for tpl in self.tpls:
            # print(tpl, tpl.matched, tpl.d)
            if not tpl.matched:
                continue
            if tpl.execute(job, self.lines):
                self.num_executed += 1
                self.num_conti_repeated += bool(job.last_executed_block_id == self.id)
                job.last_executed_block_id = self.id
                return True

    def match(self, job, ignore_status=False):
        if ignore_status or (not job.status and not self.only_when):
            状态正确 = True
        else:
            状态正确 = (job.status == self.only_when) or (self.only_when == "*")
        for tpl in self.tpls:
            if 状态正确:
                tpl.match(job)
            else:
                tpl.matched = False

    @property
    def matched(self):
        return any([tpl.matched for tpl in self.tpls])

    @property
    def priority(self):
        return self.d.get("priority")

    @property
    def only_when(self):
        return self.d.get("only_when") or ""

    @property
    def name(self):
        return self.d.get("name")

    @property
    def index(self):
        return self.d.get("index")

    @property
    def max_num(self):
        return self.d.get("max_num")


class 抽象持久序列(基本输入字段对象):
    def __init__(self, fpath_or_dict):
        if isinstance(fpath_or_dict, str):
            assert os.path.exists(fpath_or_dict)
            with open(fpath_or_dict, "r", encoding="utf8") as fp:
                self.init(json.load(fp))
        elif isinstance(fpath_or_dict, dict) or isinstance(fpath_or_dict, list):
            self.init(fpath_or_dict)
        else:
            raise ValueError(f"invalid type of fpath:{type(fpath_or_dict)}")

    def init(self, d):
        raise NotImplementedError

    def 执行任务(self, 单步=True):
        raise NotImplementedError


class 基本任务(抽象持久序列):
    URL_TASK_PULL = "https://task.j1.sale/pull/{task_key}"
    URL_TASK_PUSH = "https://task.j1.sale/push"
    持久对象 = None

    集成的队列任务数据 = {}

    def __init__(self, fpath_or_dict, device_pointed=None):
        self.device_pointed = device_pointed
        super().__init__(fpath_or_dict)
        self.status = None
        self.last_executed_block_id = None
        self.cache = tool_dict.PropDict()
        self.remote_obj = 0
        self.old_time = time.time()

    # @classmethod
    # def 推入总队列(cls, 队列名称, 队列数据):
    #     cls.集成的队列任务数据.setdefault(队列名称, []).append(队列数据)
    @property
    def 当前运行秒数(self):
        return round((time.time() - self.old_time), 0)

    def 推入数据队列(self, **kwargs):
        数据 = {
            k: v if not is_cv2_image(v) else cv2jpg_b64(v) for k, v in kwargs.items()
        }
        数据["串口号"] = self.串口号
        return global_redis.推入数据队列(数据)

    @classmethod
    def 队列拉取地址(cls, task_key):
        return cls.URL_TASK_PULL.format(task_key=task_key)

    @classmethod
    def 队列推送地址(cls):
        return cls.URL_TASK_PUSH

    def 获取设备相关队列名称(self, name):
        return f"{name}_{self.serialno}"

    @property
    def 队列名称(self):
        return (
            self.持久对象.队列名称
            if not self.持久对象.设备相关
            else self.获取设备相关队列名称(self.持久对象.队列名称)
        )

    @classmethod
    def 直接获取其他队列任务(cls, 队列名称):
        data_list = cls.集成的队列任务数据.setdefault(队列名称, [])
        global_cache.task_data = data_list.pop(-1) if data_list else None
        return global_cache.task_data

    def 直接获取任务(self):
        return self.直接获取其他队列任务(self.队列名称)

    def 拉取任务(self, task_key, 是否设备相关=True):
        task_key = task_key if not 是否设备相关 else self.获取设备相关队列名称(task_key)
        # print('task_key:', task_key)
        return 拉取任务字典(task_key)

    @classmethod
    def 处理历史记录(cls, df, lst):
        tmp = df[~df.自己]
        i = (
            check_series_contains.find_matching_i(tmp.唯一值, lst)
            if not tmp.empty
            else None
        )
        if i is not None:
            df.loc[tmp.index[:i], "已处理"] = True
            df.loc[tmp.index[:i], "新增"] = False
        return i is not None

    @property
    def 设备串行号(self):
        return self.device.adb.serialno

    def get_remote_obj(self, url, 带串行号=True, **kwargs):
        if 带串行号:
            设备串行号 = self.device.adb.serialno
        else:
            设备串行号 = None
        return RemoteModel(self.process_url(url), 设备串行号=设备串行号, **kwargs)

    @property
    def blocks(self):
        return list(filter(lambda x: not x.is_precheck(), self._blocks))

    @property
    def blocks_precheck(self):
        return list(filter(lambda x: x.is_precheck(), self._blocks))

    def init(self, d):
        self.d = d
        self._blocks = [操作块(x, self.paras) for x in self.d.get("blocks")]

    @cached_property
    def device(self):
        device_pointed = self.device_pointed or self.d.get("device")
        if device_pointed.get("is_windows"):
            return Windows窗口设备(device_pointed)
        else:
            return SteadyDevice.from_ip_port(device_pointed.get("ip_port"))

    @property
    def serialno(self):
        return self.device.adb.serialno

    @property
    def 串口号(self):
        return self.device.adb.serialno

    def 打开应用(self, package=None, activity=None):
        package = package or self.package
        activity = activity or self.activity
        script = f"am start -n {package}/{activity}"
        # print(script)
        self.device.adb.execute(script)
        time.sleep(3)
        if not self.device.adb.is_app_opened(package):
            self.device.adb.open_certain_app(
                package=package,
                activity=activity,
                stop=True,
            )

    def 切回应用(self):
        self.device.adb.ua2.app_start(self.package)

    def 关闭应用(self):
        script = f"am force-stop {self.package}"
        return self.device.adb.execute(script)

    def 输入(self, text, clear=True):
        self.device.send_keys(text, clear)

    @property
    def paras(self):
        return self.d.get("paras")

    @property
    def name(self):
        return self.d.get("name")

    @property
    def package(self):
        return self.d.get("package")

    @property
    def activity(self):
        return self.d.get("activity")

    @property
    def max_empty(self):
        return self.d.get("max_empty", 3)

    @property
    def wait_steady(self):
        return self.d.get("wait_steady", False)

    @wait_steady.setter
    def wait_steady(self, v):
        self.d["wait_steady"] = bool(v)

    @property
    def few_first(self):
        return self.d.get("few_first", False)

    @property
    def 最大执行秒(self):
        return self.d.get("最大执行秒", -1)

    def 执行操作块(self, block_id, ignore_status=False):
        self.match(block_id, ignore_status)
        block = next(filter(lambda b: b.id == block_id, self.blocks))
        # print('block is:', block, block.id)
        return block.execute(self)

    def 执行前置检查操作块(self, block_id=None):
        for block in self.blocks_precheck:
            if block_id is None or block.id == block_id:
                execute_lines(self, block.lines)

    def match(self, block_id=None, ignore_status=False):
        self.device.snapshot(wait_steady=self.wait_steady)
        for block in self.blocks:
            if block_id is None or block.id == block_id:
                block.match(self, ignore_status)

    def get_df(self):
        df = pandas.DataFrame(
            [
                {
                    "id": b.id,
                    "index": b.index,
                    "matched": b.matched,
                    "priority": b.priority,
                    "only_when": b.only_when,
                    "num": b.num_executed,
                    "repeated": b.num_conti_repeated,
                    "max_num": b.max_num,
                    "name": b.name,
                }
                for b in self.blocks
            ],
        )
        return df.sort_values(
            ["matched", "priority", "index" if not self.few_first else "num"],
            ascending=[False, False, True],
        )

    def 执行任务(self, 单步=True):
        num_empty_repeated = 0
        executed = 0
        最大执行秒 = self.最大执行秒
        old = time.time()

        while 1:
            executed_seconds = time.time() - old
            print("========================{},{}".format(executed_seconds, 最大执行秒))

            if 最大执行秒 > 0 and executed_seconds >= 最大执行秒:
                print("达到最大执行秒，停止执行:", executed_seconds, 最大执行秒)
                self.关闭应用()
                raise ValueError(f"达到最大执行秒异常:{executed_seconds} {最大执行秒}")

            if not self.blocks:
                self.status = "完成"

            if self.status == "完成":
                break

            self.match()
            df = self.get_df()
            print(f"job:{self.name} , status:{self.status}")
            print(df)

            tmp = df[df["matched"]]

            if not tmp[(tmp.repeated >= tmp.max_num) & (tmp.max_num > 0)].empty:
                print("达到最大重复次数，停止执行")
                raise 达到最大重复次数异常

            匹配成功 = not tmp.empty

            if 匹配成功:
                executed += bool(self.执行操作块(tmp.iloc[0].id))
                num_empty_repeated = 0
            else:
                num_empty_repeated += 1
                if num_empty_repeated > self.max_empty:
                    print(
                        "达到最大空白屏次数，停止执行:",
                        num_empty_repeated,
                        self.max_empty,
                    )
                    raise 达到最大空白屏次数异常
                else:
                    print("空白:", num_empty_repeated, self.max_empty)
                    time.sleep(0.5)

            if 单步:
                break
        return executed

    def 是否首次识别且最后一条为语音(self):
        if not self.cache.get("首次打开会话"):
            self.cache.update(首次打开会话=True)
            df = self.获得当前会话df()
            return not df.empty and df.iloc[-1].类型 == "语音"
        return False

    def 是否首次识别且新消息包含语音(self):
        if not self.cache.get("首次打开会话"):
            self.cache.update(首次打开会话=True)
            df = tool_wx_df.得到新消息部分df(self.获得当前会话df())
            return "语音" in df.类型.tolist()
        return False

    def 获得当前会话df(self):
        df = self.cache.get("当前")
        if df is None:
            df = self.device.df_wx
        return df

    def 是否容器底部被截断(self):
        el = self.device.container_wx.elements
        return el and el[-1].是否底部被截断()

    def 是否该类型处理完成(self, 类型, 是否缓存=False):
        df = self.获得当前会话df() if not 是否缓存 else self.cache.get("缓存")
        return df is None or df.empty or df[(df.类型 == 类型) & (~df.已处理)].empty

    def 处理日日常(self, last_keys):
        container_wx = self.device.container_wx
        容器key = container_wx.key
        容器未变化 = self.cache.get("容器key") == 容器key
        self.cache["容器key"] = 容器key

        self.cache["当前"] = 当前 = self.device.df_wx

        需向下翻页 = False

        是否已经匹配历史 = False

        if self.cache.get("语音转文字已点击"):
            print("oooooooooooooooooo转文字已点击oooooooooooooooooo")
            self.cache.update(语音转文字已点击=False)
            需向下翻页 = True

        elif self.cache.get("向下翻页中"):
            if self.是否容器底部被截断():
                print("++++++++++++++向下翻页不彻底++++++++++++++")
                需向下翻页 = True
            else:
                print("++++++++++++++向下翻页已经到底++++++++++++++")
                需向下翻页 = False
            self.cache.update(向下翻页中=False)

        elif not 容器未变化:
            print("~~~~~~~~~~~~~~~容器发生了变化~~~~~~~~~~~~~~~")
        else:
            print("!!!!!!!!!!!!!!!!容器无变化!!!!!!!!!!!!!!!!")

        if self.cache.get("缓存") is None or not 容器未变化:
            print("~~~~~~~~~~~~~~~容易变化, 或缓存为空的情况~~~~~~~~~~~~~~~")
            df = self.device.merge_wx_df(当前, self.cache.get("缓存"))
            是否已经匹配历史 = self.处理历史记录(df, last_keys)
            self.cache["缓存"] = df

        return 容器未变化, 需向下翻页, 是否已经匹配历史

    def 清除缓存并重置(self):
        self.cache.update(缓存=None)
        self.cache.update(cnt_up=0)

    def 完成(self):
        self.status = "完成"

    def 点击(self, el, offset_x=0.5, offset_y=0.5, abs_x=0, abs_y=0):
        if isinstance(el, tuple) or isinstance(el, list):
            self.device.click(*el)
        else:
            self.device.click_element(el, offset_x, offset_y, abs_x, abs_y)

    def 回退(self):
        self.device.adb.go_back()

    def 向下翻页(self, 模拟人工=False, 是否一半翻=False):
        # print("向下翻页", 模拟人工, 是否一半翻)
        self.device.adb.page_down(randomize=模拟人工, half=是否一半翻)

    def 向上翻页(self, 模拟人工=False, 是否一半翻=False):
        self.device.adb.page_up(randomize=模拟人工, half=是否一半翻)

    def 读取文件内容(self, fname):
        return tool_file.得到文件(fname, 当前目录=True).read_text()
        # with open(fname, "r") as fp:
        #     content = fp.read()
        # return content

    def 处理提示词(self, prompt):
        if prompt.strip().startswith("<!DOCTYPE html>"):
            return prompt
        return tool_env.remove_leading_whitespace(
            """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
        <meta charset="UTF-8">
        </head>
        <body>
        {prompt}
        </body>
        </html>
        """
        ).format(prompt=prompt)

    def 创建提示词(self, **kwargs):
        # prompt = self.paras.get("提示词")
        k = {
            **self.paras,
            **kwargs,
        }

        文件名 = k.get("文件名", None)
        if 文件名 is not None:
            with open(文件名, "r", encoding="utf8") as fp:
                k["提示词"] = fp.read()

        prompt = self.处理提示词(k.get("提示词"))
        历史记录 = k.pop("历史记录", None)
        if 历史记录 is not None and isinstance(历史记录, list):
            k["历史记录"] = "\n".join(历史记录)
        return prompt.format(**k)

    def 上传文件(self, content, suffix=".html", project_name="tmp"):
        return tool_static.upload_file(
            content, self.持久对象.TOKEN, suffix, project_name=project_name
        )

    def 创建提示词临时文件链接(self, **kwargs):
        # prompt = self.创建提示词(**kwargs)
        # return tool_static.upload_file(
        #     prompt, self.持久对象.TOKEN, ".html", project_name="tmp"
        # )
        return self.上传文件(self.创建提示词(**kwargs), ".html", project_name="tmp")

    @property
    def 微信容器(self):
        return self.device.container_wx

    @property
    def 微信df(self):
        容器 = self.微信容器
        df = 容器.上下文df
        df = tool_pandas.自动补齐后续缺失时间并自动加1秒(df)
        df["唯一值带时间"] = df.唯一值 + "-" + df.时间.astype("str")
        df["容器key"] = 容器.key
        return df
        # return tool_wx_df3.设置已处理(df, 全局缓存.最后历史时间)

    def 是否微信容器发生了变化(self):
        return (
            全局缓存.前容器唯一值 is None or 全局缓存.前容器唯一值 != self.微信容器.key
        )

    def 是否一半向下翻页(self):
        c = self.微信容器
        return (
            c.elements
            and c.elements[-1].是否底部触底()
            and c.elements[-1].是否非文本容器超长()
        )

    def 微信容器结束本轮(self, 标记的操作=None):
        全局缓存.最后执行动作 = 标记的操作
        全局缓存.前容器唯一值 = self.微信容器.key
        if 标记的操作 == "微信容器向下翻页":
            self.向下翻页(是否一半翻=self.微信容器.是否一半向下翻页())
        elif 标记的操作 == "微信容器向上翻页":
            self.向上翻页()

    def 微信容器向下翻页(self):
        self.微信容器结束本轮("微信容器向下翻页")
        全局缓存.向下翻页次数 += 1

    def 微信容器向上翻页(self):
        self.微信容器结束本轮("微信容器向上翻页")
        全局缓存.向上翻页次数 += 1

    def 存储调试df(self, df):
        fpath1 = f"/mnt/56T/tmp/{time.time()}_{random.random():.4f}.json"
        df.to_json(fpath1)
        print(fpath1)

    def 得到当前缓存页(self):
        df = self.微信df
        if 全局缓存.缓存页 is None:
            print("---------------------初始化当前缓存页")
            全局缓存.缓存页 = df
        elif not df.empty and (
            len(df) != len(全局缓存.缓存页)
            or 全局缓存.缓存页.容器key.iloc[0] != df.iloc[0].容器key
        ):
            print("---------------------更新当前缓存页")
            全局缓存.缓存页 = df
        return 全局缓存.缓存页

    def 得到历史页(self):
        会话名称 = self.device.干净的微信会话名称
        会话数据 = self.持久对象.数据.setdefault("会话列表", {}).get(会话名称)
        return (
            pandas.read_json(io.StringIO(会话数据))
            if 会话数据 is not None
            else pandas.DataFrame(columns=["原始时间", "唯一值", "时间", "图片key"])
        ).replace({None: numpy.nan})

    def 得到最后合法值(self, s: pandas.Series, default=None):
        last_valid_idx = s.last_valid_index()
        return s.loc[last_valid_idx] if last_valid_idx is not None else default

    def 初始化临时历史页(self):
        全局缓存.临时历史页 = pandas.DataFrame(
            columns=["原始时间", "唯一值", "时间", "图片key"]
        )
        历史页 = self.得到历史页()
        # last_valid_idx = 历史页["时间"].last_valid_index()
        # 全局缓存.最后历史时间 = (
        #     历史页.loc[last_valid_idx, "时间"]
        #     if last_valid_idx is not None
        #     else None
        # )
        全局缓存.最后历史时间 = self.得到最后合法值(历史页["时间"])
        全局缓存.向上翻页次数 = 0
        全局缓存.向下翻页次数 = 0

    def 存储历史页(self, df, name=None):
        会话名称 = self.device.干净的微信会话名称 if name is None else name
        self.持久对象.数据.setdefault("会话列表", {})[会话名称] = df.to_json()
        self.持久对象.save()

    def 清空历史(self, name=None):
        self.存储历史页(
            pandas.DataFrame(columns=["原始时间", "唯一值", "时间", "图片key"]), name
        )

    def 合并并存储历史页(self, df, name=None):
        历史页 = self.得到历史页()
        最后历史时间 = self.得到最后合法值(历史页["时间"])
        df = tool_pandas.将某列缺失时间向前补齐并每行自动加1秒(df, "时间")
        df = tool_wx_df3.截断已存储的历史部分(df, 最后历史时间, colname="时间")
        if not df.empty:
            df = tool_wx_df3.合并上下df(历史页, df)
            self.存储历史页(df, name)

    def 点击第一张未处理图片(self):
        df = self.得到当前缓存页()
        # # df = 全局缓存.临时历史页
        tmp = df[(df.类型 == "图片") & (~df.已处理)]
        if 全局缓存.最后历史时间 is not None:
            h = tmp[tmp.时间 <= 全局缓存.最后历史时间]
            if not h.empty:
                tmp = tmp.loc[h.index[-1] + 1 :]

        if not tmp.empty:
            self.device.click(*tmp.iloc[0].xy)
            全局缓存.最后图片index = tmp.index[0]
            全局缓存.最后图片信息 = tmp.index[0], tmp.iloc[0].容器key
            return True

    # def 处理并保存图片(self):
    #     url, img_key = self.下载微信图片并返回链接和唯一码()
    #     df = 全局缓存.临时历史页
    #     图片index, 容器key = 全局缓存.最后图片信息
    #     assert (
    #         图片index is not None and df.iloc[0].容器key == 容器key
    #     ), "图片处理错误, 容器不一致"
    #     df.loc[图片index, ["链接", "图片key", "已处理"]] = (url, img_key, True)

    def 处理并保存图片(self):
        url, img_key = self.下载微信图片并返回链接和唯一码()
        # df = 全局缓存.临时历史页
        # df = self.得到当前缓存页()
        df = 全局缓存.缓存页
        # df = 全局缓存.临时历史页
        图片index, 容器key = 全局缓存.最后图片信息
        assert (
            图片index is not None and df.loc[图片index].容器key == 容器key
        ), "图片处理错误, 容器不一致"
        df.loc[图片index, ["链接", "图片key", "已处理"]] = (url, img_key, True)

    # def 点击处理并上传图片(self, e):
    #     self.device.clear_remote_wx_images()
    #     e.click()
    #     time.sleep(1)
    #     self.处理并保存图片()

    def 保存并上传图片(self, e):
        self.device.clear_remote_wx_images()
        e.click()
        time.sleep(1)
        self.处理并保存图片()

    def 合并历史和当前页(self):
        # 历史页 = self.得到历史页()
        历史页 = 全局缓存.临时历史页
        当前页 = self.得到当前缓存页()
        当前页 = tool_pandas.将某列缺失时间向前补齐并每行自动加1秒(当前页, "时间")
        当前页 = tool_wx_df3.截断已存储的历史部分(
            当前页, 全局缓存.最后历史时间, colname="时间"
        )

        df = tool_wx_df3.合并上下df(历史页, 当前页)
        df = tool_pandas.将某列缺失时间向前补齐并每行自动加1秒(df, "时间")
        全局缓存.最后历史时间 = self.得到最后合法值(df["时间"], 全局缓存.最后历史时间)
        全局缓存.临时历史页 = df
        print("合并完成======================")
        print(df[["上下文", "时间", "原始时间"]])

    # def 处理当前同步流程(self, debug=False):
    #     if (
    #         not self.是否微信容器发生了变化()
    #         and 全局缓存.最后执行动作 == "微信容器向下翻页"
    #     ):
    #         print("最后结果======================")
    #         print(全局缓存.临时历史页)
    #         # raise 同步消息到底部异常
    #         return True
    #     else:
    #         self.合并历史和当前页(debug)
    #         if self.点击第一张未处理图片():
    #             self.微信容器结束本轮("点击图片")
    #         else:
    #             self.微信容器向下翻页()

    def 处理当前同步流程(self):
        if (
            not self.是否微信容器发生了变化()
            and 全局缓存.最后执行动作 == "微信容器向下翻页"
        ):
            return True
        else:
            if self.点击第一张未处理图片():
                self.微信容器结束本轮("点击图片")
            else:
                self.合并历史和当前页()
                self.微信容器向下翻页()

    @property
    def 最后一条未处理语音(self):
        df = self.微信df
        keys = 全局缓存.setdefault("处理过的语音列表", [])
        tmp = df[(df.类型 == "语音") & (~df.已处理) & (~df.唯一值带时间.isin(keys))]
        return tmp.iloc[-1] if not tmp.empty else None

    def 长按最后一条未处理语音(self):
        s = self.最后一条未处理语音
        if s is not None:
            self.device.long_click(*s.xy)
            全局缓存.setdefault("处理过的语音列表", []).append(s.唯一值带时间)
            return True

    def 是否已对齐(self):
        历史页 = self.得到历史页()
        当前页 = self.得到当前缓存页()
        return (
            not 历史页.empty and 当前页.原始时间.dropna().isin(历史页.原始时间).any()
        ) or (历史页.empty and 全局缓存.向上翻页次数 >= 3)

    def 处理历史对齐流程(self):
        if (
            not self.是否微信容器发生了变化()
            and 全局缓存.最后执行动作 == "微信容器向上翻页"
        ):
            return True

        if self.长按最后一条未处理语音():
            self.微信容器结束本轮("处理语音")
            return False

        if self.是否已对齐():
            return True
        self.微信容器向上翻页()

    def 下载微信图片并返回链接和唯一码(self):
        return self.device.下载微信图片并返回链接和唯一码(self.持久对象.TOKEN)

    def 点击并上传手机端文件(self, e, 手机端路径):
        return self.device.点击并上传手机端文件(e, self.持久对象.TOKEN, 手机端路径)

    def 点击并上传手机端微信图片(self, e):
        return self.device.点击并上传手机端微信图片(e, self.持久对象.TOKEN)

    def 生成随机微信群名称(self):
        return tool_wx_groupname.随机生成低风险微信群名字()

    def 是否聚焦(self, results):
        if not isinstance(results, list):
            results = [results]
        return sum([e.attrib.get("focused") == "true" for e in results]) > 0

    def 持久对象写入数据记录字典(self, d: dict):
        self.持久对象.写入数据记录字典(d)

    def 是否三人群(self, name):
        return tool_env.is_valid_upper_6chars(name)

    def 持久对象获取其他记录(self, name):
        return self.持久对象.获取其他记录(name)

    def 打开豆包(self):
        self.打开应用("com.larus.nova", "com.larus.home.impl.MainActivity")

    def 元素转字符串(self, e):
        return self.device.element2text(e)

    @property
    def 数据(self):
        return self.持久对象.配置数据

    def 获取设备屏幕截图url(self):
        img = self.device.adb.screen_shot()
        content = cv2_img_to_bytesio(img, ".jpg").getvalue()
        return self.上传文件(content, suffix=".jpg", project_name="tmp")

    def 获得豆包提示词(self, d):
        content, 直接使用 = tool_moban_configs.获得豆包提示词(d)
        if not 直接使用:
            url = self.上传文件(content)
            content = f"""请严格根据链接中的提示词执行:\n{url}"""
        print(f"输出的提示词:\n{content}\n")
        return content

    def 获得豆包提示词队列数据(self, d):
        return {
            "提示词": self.获得豆包提示词(d),
            "timestamp": str(time.time()),
            **self.传输队列字典,
        }

    # def 通过文件获取提示词(self, 文件名, **kwargs):
    #     return tool_moban_configs.得到系统提示词(文件名, **kwargs)

    @property
    def 剪贴板(self):
        return self.device.adb.ua2.clipboard

    @property
    def 返回队列(self):
        return f"豆包队列_{self.串口号}"

    @property
    def 返回队列_数据(self):
        return f"数据队列_{self.串口号}"

    def 获取最近n条历史(self, n=5):
        history = self.数据.数据记录.list[-n:]
        history = [
            f"{i+1}: {x.get('修正评论')}"
            for i, x in enumerate(history)
            if x and x.get("修正评论")
        ]
        history = "\n".join(history)
        return history

    @property
    def 传输队列字典(self):
        return {
            "返回队列": self.返回队列,
        }

    def 从返回队列中获取结果(self, 阻塞, 超时秒数=5 * 60):
        return 全局队列.拉出Redis(self.返回队列, 阻塞, 超时秒数)

    def 推入通用豆包任务队列(self, data: dict):
        d = self.获得豆包提示词队列数据(data)
        print("提示词字典:", d)
        全局队列.推入Redis("豆包队列", d)
        data.update(d)
        return d.get("timestamp")

    def 推入豆包图片识别队列(self, url: str):
        return self.推入通用豆包任务队列(
            {
                "类型": "提取图片信息_直接_详细",
                "url": url,
            }
        )

    def 调试推入阻塞测试(self, d):
        全局队列.推入Redis("豆包队列", d)
        print("===========================================")
        return 全局队列.拉出Redis(d.get("返回队列"), True, 5 * 60)

    def 推入通用豆包任务队列并阻塞获取结果(
        self, data: dict, 阻塞秒数=5 * 60, is_json=False
    ):
        ts = self.推入通用豆包任务队列(data)
        结果 = None
        while 1:
            d = self.从返回队列中获取结果(True, 阻塞秒数)
            if not d:
                break
            if d.get("timestamp") != ts:
                print("丢弃前期废弃结果:", d)
                continue
            # 结果 = d.get("结果") if d else None
            结果 = d.get("结果")
            break

        if 结果 and isinstance(结果, str) and is_json:
            try:
                结果 = json.loads(结果)
            except Exception as e:
                print("解析json失败", e, 结果)
                结果 = None

        return 结果

    def 识别图片信息(self, url):
        data = {
            "类型": "提取图片信息_直接",
            "url": url,
        }
        return self.推入通用豆包任务队列并阻塞获取结果(data)

    def 提取设备屏幕截图信息(self):
        return self.识别图片信息(self.获取设备屏幕截图url())

    def 根据模版提取设备屏幕截图信息(self):
        data = {
            "类型": "提取图片信息_模版",
            "视频截图": self.获取设备屏幕截图url(),
        }
        return self.推入通用豆包任务队列并阻塞获取结果(data)

    def 根据文字描述以及截图获取回复(self):
        c = self.device.find_xpath_first(
            '//androidx.viewpager.widget.ViewPager[@text=""][@content-desc="视频"]'
        )
        封面文字描述 = self.device.element2text(c)

        截图描述 = self.提取设备屏幕截图信息()

        文字描述 = "\n".join([封面文字描述, 截图描述])

        # data = {
        #     "类型": "主动评价模版_纯文字_串门",
        #     "封面文字描述": 文字描述,
        #     "合法": tool_dy_utils.has_interaction_keywords(文字描述),
        # }
        name = '抖音_数据爬虫'
        obj = self.持久对象.获取其他记录(name)
        data = {
            "类型": "主动评价模版_纯文字_串门_带数据",
            "content": 文字描述,
            "name": tool_dy_utils.从文本中提取用户名称(文字描述),
            "account_data": obj.数据.get('创作数据'),
            "合法": tool_dy_utils.has_interaction_keywords(文字描述),
        }


        self.数据.数据记录.enqueue(data)

        return (
            self.推入通用豆包任务队列并阻塞获取结果(data) if data.get("合法") else None
        )

    def 从截图获取回复(self, 模版名="主动评价模版_图文"):
        c = self.device.find_xpath_first(
            '//androidx.viewpager.widget.ViewPager[@text=""][@content-desc="视频"]'
        )
        封面文字描述 = self.device.element2text(c)
        全局缓存.数据记录字典 = {"页面内容": 封面文字描述}
        data = {
            "类型": 模版名,
            "封面文字描述": 封面文字描述,
            "历史回复": self.获取最近n条历史(5),
            "视频截图": self.获取设备屏幕截图url(),
        }
        print(data)
        data = self.获得豆包提示词队列数据(data)
        print(data)
        全局队列.推入Redis("豆包队列", data)
        d = 全局队列.拉出Redis(self.返回队列, True, 5 * 60)
        结果 = d.get("结果") if d else None
        return 结果

    def 从截图获取回复_串门(self):
        return self.从截图获取回复(模版名="主动评价模版_图文_串门")

    def 从剪贴板获取回复(self):
        history = self.获取最近n条历史(5)

        data = {
            "类型": "获取视频内容",
            "url": tool_dy_utils.提取链接(self.剪贴板)[0],
            **self.传输队列字典,
        }
        全局队列.推入Redis("豆包队列", data)
        d = 全局队列.拉出Redis(self.返回队列, True, 5 * 60)
        print(d)
        视频内容 = d.get("结果") if d else None

        if tool_dy_utils.是否无内容(视频内容):
            return None

        data = {
            "类型": "主动评价模版",
            "视频内容": 视频内容,
            "历史回复": history,
            "返回队列": self.返回队列,
        }
        print(data)
        全局队列.推入Redis("豆包队列", data)
        d = 全局队列.拉出Redis(self.返回队列, True, 5 * 60)
        结果 = d.get("结果") if d else None

        if tool_dy_utils.是否无内容(结果):
            return None
        return 结果

    def 组装评论数据并变更任务状态(self, 结果):
        print("获得的回复结果:", 结果)
        if not 结果:
            self.status = "结束本轮"
            self.持久对象.变更间隔秒数(间隔秒数=1)
            return False
        else:
            全局缓存.数据记录字典 = {}
            全局缓存.数据记录字典["原始评论"] = 结果
            print("---------------------------------")
            全局缓存.数据记录字典["修正评论"] = 修正评论 = (
                tool_env.对豆包回复进行所有的必要处理(结果)
            )
            print(修正评论)
            print("---------------------------------")
            全局缓存.数据记录字典["合法"] = tool_env.has_valid_result(修正评论)
            self.数据.数据记录.enqueue(全局缓存.数据记录字典)
            if 全局缓存.数据记录字典["合法"]:
                self.status = "开始评论"
                return True
            else:
                self.status = "结束本轮"
                self.持久对象.变更间隔秒数(间隔秒数=1)
                return False

    # def 组装评论数据并变更任务状态(self, 结果):
    #     print("获得的回复结果:", 结果)
    #     if not 结果:
    #         # self.status = "结束本轮"
    #         # self.持久对象.变更间隔秒数(间隔秒数=1)
    #         return False
    #     else:
    #         全局缓存.数据记录字典 = {}
    #         全局缓存.数据记录字典["原始评论"] = 结果
    #         print("---------------------------------")
    #         全局缓存.数据记录字典["修正评论"] = 修正评论 = (
    #             tool_env.对豆包回复进行所有的必要处理(结果)
    #         )
    #         print(修正评论)
    #         print("---------------------------------")
    #         全局缓存.数据记录字典["合法"] = tool_env.has_valid_result(修正评论)
    #         # self.数据.数据记录.enqueue(全局缓存.数据记录字典)
    #         if 全局缓存.数据记录字典["合法"]:
    #             self.status = "开始评论"
    #             return True
    #         else:
    #             self.status = "结束本轮"
    #             self.持久对象.变更间隔秒数(间隔秒数=1)
    #             return False

    def 根据文字描述以及截图获取回复并组装结果且改变任务状态(self):
        return self.组装评论数据并变更任务状态(self.根据文字描述以及截图获取回复())

    def 根据字典数据获取回复并组装结果且改变任务状态(self, d: dict):
        结果 = self.推入通用豆包任务队列并阻塞获取结果(d)
        d["原始"] = 结果
        d["修正"] = 结果 = tool_env.对豆包回复进行所有的必要处理(结果)
        d["合法"] = tool_env.has_valid_result(结果)
        self.数据.数据记录.enqueue(d)
        return d["原始"] if d["合法"] else None

    def 获取微信会话管理器(self, name, update=True):
        m = self.数据.get_session_df_manager(name)
        if update:
            m.append(self.device.df_wx)
        return m

    def 更新微信会话(self, d):
        m = self.获取微信会话管理器(d.pop("session_name"), update=False)
        df = m.df
        index = d.pop("index")
        keys = list(d.keys())
        values = list(d.values())
        df.loc[index, keys] = values
        m.save()

    @property
    def 微信会话管理器(self):
        return self.获取微信会话管理器(self.device.微信会话名称, update=True)
        # name = self.device.微信会话名称
        # m = self.数据.get_session_df_manager(name)
        # m.append(self.device.df_wx)
        # return m

    def 清除当前会话历史(self):
        m = self.微信会话管理器
        m.df = pandas.DataFrame()
        m.save()

    @property
    def 微信会话df(self):
        return self.微信会话管理器.df

    @property
    def 微信会话history(self):
        return tool_wx_df4.转历史(self.微信会话管理器.df)

    # 提交数据并阻塞等待结果
    def 获取微信会话回复数据(self):
        return 全局队列.提交数据并阻塞等待结果(
            self.返回队列_数据,
            history=self.微信会话history,
            sys_prompt=tool_moban_configs.得到系统提示词("起号运营人设_系统提示词"),
        )

    # @property
    # def 微信会话df_未处理(self):
    #     df = self.微信会话df
    #     return df[~df.已处理]

    # @property
    # def 微信会话df_未处理_图片(self):
    #     df = self.微信会话df_未处理
    #     return df[(df.类型 == "图片") & (~df.自己)]

    # @property
    # def 微信会话df_未处理_图片_第一张(self):
    #     # df = self.微信会话df_未处理_图片
    #     df = self.微信会话df
    #     df = df[(df.类型 == "图片") & (~df.自己) & (~df.已处理)]
    #     return df.iloc[0] if len(df) > 0 else None

    def 处理微信会话第一张未处理图片(self):
        # 第一张未处理图片 = self.微信会话df_未处理_图片_第一张
        session_name = self.device.微信会话名称
        df = self.微信会话df
        df = df[(df.类型 == "图片") & (~df.自己) & (~df.已处理)]
        第一张未处理图片 = df.iloc[0] if len(df) > 0 else None

        if 第一张未处理图片 is not None:
            全局缓存.处理图片 = {
                "index": 第一张未处理图片.name,
                "session_name": session_name,
            }
            self.点击(第一张未处理图片.xy)
            return True
        else:
            全局缓存.pop("处理图片", None)

    @property
    def 微信会话df_未识别_图片_第一张(self):
        df = self.微信会话df
        df = df[(df.类型 == "图片") & (~df.自己) & (pandas.isna(df.内容))]
        return df.iloc[0] if len(df) > 0 else None

    def 识别微信会话所有图片(self):
        # 第一张未识别图片 = self.微信会话df_未识别_图片_第一张
        m = self.微信会话管理器
        df = m.df

        df = df[(df.类型 == "图片") & (~df.自己) & (pandas.isna(df.内容))]

        全局缓存.setdefault("识别图片表", {})

        df = df[~df.图片key.isin(全局缓存.识别图片表.keys())]

        for i in range(len(df)):
            ts = self.推入豆包图片识别队列(df.iloc[i].链接)
            全局缓存.识别图片表[df.iloc[i].图片key] = ts

        for i in range(len(全局缓存.识别图片表)):
            d = self.从返回队列中获取结果(阻塞=False)
            if d is not None:
                print("识别结果:", d)
                ts = d.get("timestamp")
                图片key = {v: k for k, v in 全局缓存.识别图片表.items()}.get(ts)
                if 图片key is not None:
                    print("图片key:", 图片key)
                    tmp = m.df
                    index = tmp[tmp.图片key == 图片key].index

                    if m.df["内容"].dtype != object:
                        m.df["内容"] = m.df["内容"].astype(object)

                    m.df.loc[index, ["内容"]] = d.get("结果")
                    m.save()
                    全局缓存.识别图片表.pop(图片key)
            time.sleep(1)
        return len(全局缓存.识别图片表)

        # 第一张未识别图片 = df.iloc[0] if len(df) > 0 else None

        # if 第一张未识别图片 is not None:
        #     全局缓存.setdefault('识别图片列表', []).append(
        #         {'index':第一张未识别图片.name,
        #          'time': time.time(),
        #          }
        #         )
        #     m.df.loc[第一张未识别图片.name, ["内容"]] = ''
        #     m.save()
        # self.点击(第一张未识别图片.xy)
        # return True

    # def 处理并保存图片(self):
    #     url, img_key = self.下载微信图片并返回链接和唯一码()
    #     # df = 全局缓存.临时历史页
    #     # df = self.得到当前缓存页()
    #     df = 全局缓存.缓存页
    #     # df = 全局缓存.临时历史页
    #     图片index, 容器key = 全局缓存.最后图片信息
    #     assert (
    #         图片index is not None and df.loc[图片index].容器key == 容器key
    #     ), "图片处理错误, 容器不一致"
    #     df.loc[图片index, ["链接", "图片key", "已处理"]] = (url, img_key, True)

    # def 存储图片缓存到本地数据库(self):
    #     if 全局缓存.处理图片 and 全局缓存.处理图片.get("链接"):
    #         m = self.微信会话管理器
    #         loc = 全局缓存.处理图片["index"]
    #         s = m.df.loc[loc]
    #         print(s, s.to_dict())
    #         assert (
    #             not s.已处理
    #             and s.类型 == "图片"
    #             and pandas.isna(s.链接)
    #             and pandas.isna(s.图片key)
    #         ), s
    #         m.df.loc[loc, ["链接", "图片key", "已处理"]] = (
    #             全局缓存.处理图片["链接"],
    #             全局缓存.处理图片["图片key"],
    #             True,
    #         )
    #         m.save()
    #         全局缓存.pop("处理图片")

    # def 点击保存图片_上传_并缓存链接和唯一码(self, e):
    #     self.device.clear_remote_wx_images()
    #     e.click()
    #     time.sleep(1)
    #     url, img_key = self.下载微信图片并返回链接和唯一码()
    #     全局缓存.处理图片.update(链接=url, 图片key=img_key)

    # 点击保存图片_上传_并缓存链接和唯一码

    def 点击保存图片_上传_并存储链接和唯一码(self, e):
        self.device.clear_remote_wx_images()
        e.click()
        time.sleep(1)
        url, img_key = self.下载微信图片并返回链接和唯一码()
        全局缓存.处理图片.update(链接=url, 图片key=img_key, 已处理=True)
        self.更新微信会话(全局缓存.处理图片)
        全局缓存.pop("处理图片", None)


class 前置预检查任务(基本任务):
    pass


class 基本任务列表(抽象持久序列):
    def __init__(self, fpath_or_dict, device_pointed=None, 持久对象=None):
        self.device_pointed = device_pointed
        基本任务.持久对象 = 持久对象
        super().__init__(fpath_or_dict)

    def init(self, list_of_dict):
        self.jobs = [基本任务(d, self.device_pointed) for d in list_of_dict]

    def 执行任务(self, 单步=False):
        global_cache.clear()
        main_job = self.jobs[-1]
        global_cache.update(main_job.paras)
        if 单步:
            return main_job.执行任务(单步=单步)
        else:
            num_executed = 0

            try:
                main_job.执行前置检查操作块()
                if global_cache.不执行前置任务:
                    jobs = self.jobs[-1:]
                else:
                    jobs = self.jobs
                for job in jobs:
                    num_executed += job.执行任务(单步=False)
            except 任务预检查不通过异常:
                pass
            except Exception as e:
                print(e)
                main_job.关闭应用()
                raise e

            return num_executed > 0


class TaskSnapShotDevice(SnapShotDevice):
    def __init__(self, adb, task, base_dir):
        adb.switch_app()
        SnapShotDevice.__init__(self, adb)
        self.img = adb.screen_shot()

        task.key = task.get_task_key(self)
        task_key_pre = task.pre_same_job_key
        self.task = task
        # print([task.key, task_key_pre])

        self.changed = (
            task.key is None or task_key_pre is None or task_key_pre != task.key
        )

        if self.changed:
            task.fpath_screenshot = os.path.join(base_dir, f"{task.id}.png")
            self.img = adb.screen_shot()
            cv2.imwrite(task.fpath_screenshot.path, self.img)

            task.fpath_xml = os.path.join(base_dir, f"{task.id}.xml")
            with open(task.fpath_xml.path, "wb") as fp:
                fp.write(self.source.replace("'\\", "").encode("utf8"))
            task.save()

    def perform_operation_of_template(self):
        tpl = self.task.tpl_result
        rect = self.task.rect
        if rect is not None and tpl.op:
            getattr(self, tpl.op)(rect)
        #     self.task.status = self.task.PRODUCED_RECORD
        # else:
        #     self.task.status = self.task.EMPTY_RECORD
        # self.task.save()

    def CLICK(self, rect):
        self.adb.do_click(rect.center_x, rect.center_y)

    def DBCLICK(self, rect):
        self.adb.do_double_click(rect.center_x, rect.center_y)

    def LONGCLICK(self, rect):
        self.adb.do_longclick(rect.center_x, rect.center_y, duration=1000)

    def CLEAR_PICTURES_WEIXIN_AND_CLICK(self, rect):
        self.adb.clear_temp_dir(base_dir="/sdcard/Pictures/WeiXin/")
        self.CLICK(rect)

    def NONE(self, rect):
        pass


class TaskDumpedDevice(SnapShotDevice):
    def __init__(self, task):
        self.init(task.xml, 0)
        self.img = cv2pil(task.img)
        self.adb = task.job.adb


class TaskExecuteDevice(SnapShotDevice):
    def __init__(self, task):
        self.init(task.xml, 0)
        self.mask = task.mask

    def match_image(self, tpl):
        l = get_template_points(self.mask, tpl.mask, threshold=0.8)
        if l:
            h, w = tpl.mask.shape[:2]
            return (l[0][0], l[0][1], l[0][0] + w, l[0][1] + h)

    def match_xml(self, tpl):
        xml = tpl.xml.decode("utf8")
        e = self.find_xpath_safe(xml).wait()
        return e.bounds

    # def __getattr__(self, name):
    #     pass
    #
    # def __getattribute__(self, item):
    #     """属性拦截器"""
    #     if item != 'find_xpath_safe':
    #         print('item', item)
    #         self.step_name = item
    #     return object.__getattribute__(self, item)


def find_by_xpath(adb_device, xpath):
    """
    >>> find_by_xpath(DummyDevice('ut/xiaoshipin/page.xml'), '//*[re:match(@text, "开启悬浮窗")][@index="0"]').exists
    True
    >>> find_by_xpath(DummyDevice('ut/xiaoshipin/page.xml'), '//*[re:match(@text, "开启悬浮窗")][@index="0"]').click()
    """
    return XPath(adb_device)(xpath)


def wait_jianyin_template_search_input_click_ready(adb_device):
    """
    >>> wait_jianyin_template_search_input_click_ready(DummyDevice('ut/xiaoshipin/page.xml'))
    >>> wait_jianyin_template_search_input_click_ready(DummyDevice('ut/jianyin/page_input_click_ready.xml')) is not None
    True
    """
    return find_by_xpath(
        adb_device,
        "//com.lynx.component.svg.UISvg/following-sibling::com.bytedance.ies.xelement.input.LynxInputView",
    ).wait()


def wait_jianyin_template_search_completed(adb_device):
    """
    >>> wait_jianyin_template_search_completed(DummyDevice('ut/xiaoshipin/page.xml'))
    >>> wait_jianyin_template_search_completed(DummyDevice('ut/jianyin/page_search_finished.xml')) is not None
    True
    """
    return find_by_xpath(adb_device, '//*[@text="筛选"]').wait()


def wait_jianyin_search_button_ready(adb_device):
    """
    >>> wait_jianyin_search_button_ready(DummyDevice('ut/xiaoshipin/page.xml'))
    >>> wait_jianyin_search_button_ready(DummyDevice('ut/jianyin/page_input_click_ready.xml'))
    >>> wait_jianyin_search_button_ready(DummyDevice('ut/jianyin/page_search_button_ready.xml')).attrib['bounds']
    '[184,302][821,404]'
    """
    x = find_by_xpath(
        adb_device,
        '//com.lynx.tasm.behavior.ui.LynxFlattenUI[@text="搜索"]/preceding-sibling::*',
    )
    if x.wait() is not None:
        return x.all()[-1]


def wait_jianyin_open_template_directly_buttopn(adb_device, timeout=None):
    """
    >>> wait_jianyin_open_template_directly_buttopn(DummyDevice('ut/xiaoshipin/page.xml')) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    NoTemplatePopupException:
    >>> wait_jianyin_open_template_directly_buttopn(DummyDevice('ut/jianyin/page_tpl_direct_open.xml')) is not None
    True
    """
    e = find_by_xpath(adb_device, '//android.widget.Button[@text="打开看看"]').wait(
        timeout=timeout
    )
    if e is None:
        raise NoTemplatePopupException
    return e


def click_if_jianyin_open_template_giveup_history_button_exists(adb_device):
    """
    >>> click_if_jianyin_open_template_giveup_history_button_exists(DummyDevice('ut/xiaoshipin/page.xml'))
    >>> click_if_jianyin_open_template_giveup_history_button_exists(DummyDevice('ut/jianyin/page_giveup.xml'))
    True
    """
    l = find_by_xpath(
        adb_device, '//*[@text="放弃"][@resource-id="com.lemon.lv:id/tvCancelResume"]'
    ).all()
    if len(l):
        l[0].click()
        return True


if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
