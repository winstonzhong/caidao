"""
Created on 2023年12月21日

@author: lenovo
"""

import os
import time

import cv2
from uiautomator2.xpath import XPath, XMLElement

from helper_hash import get_hash
from tool_env import bounds_to_rect
from tool_img import get_template_points, show, pil2cv2, cv2pil, b642cv2
from lxml import etree

import functools

import json

import pandas

from functools import cached_property

from tool_exceptions import (
    任务预检查不通过异常,
    达到最大重复次数异常,
    达到最大空白屏次数异常,
)

from tool_remote_orm_model import RemoteModel

from tool_wx_container import 解析器

import itertools

import tool_wx_df

import tool_static

import traceback

import tool_wx

import requests

import tool_env

import check_series_contains

# def execute_lines(job, lines, self=None):
#     if self is not None:
#         if self.matched:
#             try:
#                 exec(lines)
#                 return True
#             except Exception as e:
#                 print(f"error when executing:{self.id}:{e}")
#                 traceback.print_exc()
#     else:
#         exec(lines)
global_cache = {}

URL_TASK_QUEUE = f"https://{tool_env.HOST_TASK}"


def 拉取任务字典(task_key, 中继=False):
    return requests.get(f'{URL_TASK_QUEUE}/pull/{task_key}{"_" if 中继 else ""}').json()


def 如有任务转发中继(task_key):
    url = f"{URL_TASK_QUEUE}/pull/{task_key}?forward={task_key}_"
    return bool(requests.get(url).json())


def 上传结果字典(task_key, result_data):
    # return requests.post(f'{URL_TASK_QUEUE}/push', data={'result_key': task_key, 'result_data': result_data}).json()
    url = f"{URL_TASK_QUEUE}/push"

    data = {
        "result_key": task_key,
        "result_data": result_data,
    }

    # response = await requests_async.post(params.get('url'), data=data)

    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(data),
    )

    response.raise_for_status()
    return response.json()


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


class NoTemplatePopupException(Exception):
    pass


class DummyWatcher(object):
    def run(self, xml_content):
        return False


class XpathNotFoundException(Exception):
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

    def swipe(self, fromx, fromy, tox, toy):
        return self.adb.swipe((fromx, fromy), (tox, toy))

    def long_click(self, *a, **k):
        print(a, k)
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
        self.refresh()

    def parse_element(self, e):
        rtn = []
        for x in e.elem.xpath(".//*"):
            text = x.attrib.get("text") or ""
            desc = x.attrib.get("content-desc") or ""
            if text or desc:
                rtn.append(f"{text} {desc}")
        return rtn

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
            src = self.adb.match_file_in_robot_temp(url)
            self.adb.copy_file_to_download(src)

    @property
    def container_wx(self):
        return 解析器(xml=self.source)

    @property
    def df_wx(self):
        df = self.container_wx.上下文df
        df["已处理"] = False
        df["链接"] = None
        df.自己 = df.自己.fillna(False).astype(bool)
        return df

    def merge_wx_df(self, upper_page, lower_page):
        print("uppser page:")
        print(upper_page)
        print("lower page:")
        print(lower_page)

        rtn = tool_wx_df.合并上下两个df(上一页=upper_page, 当前页=lower_page, safe=True)
        if "自己" in rtn.columns:
            rtn.已处理 = rtn.已处理.fillna(False).astype(bool)
        else:
            rtn["已处理"] = False
        if "自己" in rtn.columns:
            rtn.自己 = rtn.自己.fillna(False).astype(bool)
        else:
            rtn["自己"] = False

        # rtn.已处理 = ~rtn.类型.isin(["图片","语音"])
        rtn["已处理"] = rtn["已处理"].where(
            rtn["已处理"], ~rtn["类型"].isin(["图片", "语音"])
        )
        rtn["新增"] = True

        return rtn

    @property
    def remote_fpath_wx_images(self):
        return "/sdcard/Pictures/WeiXin"

    @property
    def remote_fpath_temp(self):
        return "/sdcard/robot_temp"

    def clear_remote_wx_images(self):
        self.adb.clear_temp_dir(self.remote_fpath_wx_images)

    def download_wx_image(self, token=None):
        if tool_static.is_inner():
            fpath = self.adb.pull_lastest_file_until(
                base_dir=self.remote_fpath_wx_images, to_56T=True
            )
            return tool_static.路径到链接(fpath)
        else:
            """
            下载该文件到本地
            上传至56T
            源文件移动至robot临时目录且按照56T链接返回的文件名(可选touch)
            """
            fpath = self.adb.pull_lastest_file_until(
                base_dir=self.remote_fpath_wx_images, to_56T=False
            )
            url = tool_static.upload_file_by_path(fpath, token)
            fname = url.split("/")[-1]
            src = self.adb.get_latest_file(base_dir=self.remote_fpath_wx_images)
            self.adb.move_file_to_robot_temp(src, fname)
            return url

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


class 基本输入字段对象(object):
    # HOST_SERVER = os.getenv("HOST_SERVER", "crawler.j1.sale")
    HOST_SERVER = os.getenv("HOST_SERVER", "coco.j1.sale")

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
        return tool_env.replace_url_host(url, cls.HOST_SERVER)

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
        # from tool_remote_orm_model import RemoteModel

        # if self.matched:
        #     try:
        #         exec(lines)
        #         return True
        #     except Exception as e:
        #         print(f"error when executing:{self.id}:{e}")


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
            状态正确 = job.status == self.only_when
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
    # HOST_SERVER = os.getenv("HOST_SERVER", "crawler.j1.sale")
    # HOST_SERVER = os.getenv("HOST_SERVER", "coco.j1.sale")
    URL_TASK_PULL = "https://task.j1.sale/pull/{task_key}"
    URL_TASK_PUSH = "https://task.j1.sale/push"

    def __init__(self, fpath_or_dict, device_pointed=None):
        self.device_pointed = device_pointed
        super().__init__(fpath_or_dict)
        self.status = None
        self.last_executed_block_id = None
        self.cache = {}
        self.remote_obj = 0

    # @classmethod
    # def 是否已经匹配历史(cls, series, lst):
    #     return check_series_contains(series, lst)
    @classmethod
    def 队列拉取地址(cls, task_key):
        return cls.URL_TASK_PULL.format(task_key=task_key)

    @classmethod
    def 队列推送地址(cls):
        return cls.URL_TASK_PUSH

    @classmethod
    def 处理历史记录(cls, df, lst):
        tmp = df[~df.自己]
        i = check_series_contains.find_matching_i(tmp.唯一值, lst)
        if i is not None:
            # df['新增'] = True
            df.loc[tmp.index[:i], "已处理"] = True
            df.loc[tmp.index[:i], "新增"] = False
        return i is not None

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
        # print('==========================', self.paras)
        self._blocks = [操作块(x, self.paras) for x in self.d.get("blocks")]

        # device_pointed = self.device_pointed or self.d.get("device")
        # if device_pointed.get("is_windows"):
        #     self.device = Windows窗口设备(device_pointed)
        # else:
        #     self.device = SteadyDevice.from_ip_port(device_pointed.get("ip_port"))

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

    # @classmethod
    # def process_url(cls, url):
    #     return tool_env.replace_url_host(url, cls.HOST_SERVER)

    # def requests_get(self, url, 带串行号=True, **kwargs):
    #     obj = self.get_remote_obj(self.process_url(url), 带串行号=带串行号, **kwargs)
    #     return obj if obj.data else None

    # def requests_post(self, url, 带串行号=True, **kwargs):
    #     payload = {"设备串行号": self.device.adb.serialno} if 带串行号 else {}

    # def 刷新参数(self, paras):
    #     self.d["paras"] = paras
    #     for block in self._blocks:
    #         block.刷新参数(paras)

    def 打开应用(self):
        script = f"am start -n {self.package}/{self.activity}"
        # print(script)
        self.device.adb.execute(script)
        time.sleep(3)
        print(f"checking...:{self.package}/{self.activity}")
        if not self.device.adb.is_app_opened(self.package):
            self.device.adb.open_certain_app(
                package=self.package,
                activity=self.activity,
                stop=True,
            )

    def 关闭应用(self):
        script = f"am force-stop {self.package}"
        return self.device.adb.execute(script)

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

    @property
    def few_first(self):
        return self.d.get("few_first", False)

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
        while 1:
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
                    print("达到最大空白屏次数，停止执行")
                    raise 达到最大空白屏次数异常

            if 单步:
                break
        return executed


class 前置预检查任务(基本任务):
    pass


class 基本任务列表(抽象持久序列):
    def __init__(self, fpath_or_dict, device_pointed=None):
        self.device_pointed = device_pointed
        super().__init__(fpath_or_dict)

    def init(self, list_of_dict):
        self.jobs = [基本任务(d, self.device_pointed) for d in list_of_dict]

    # def 刷新参数(self, paras):
    #     for job in self.jobs:
    #         job.刷新参数(paras)

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
                for job in self.jobs:
                    num_executed += job.执行任务(单步=False)
            except 任务预检查不通过异常:
                pass
                # print('---------------')

            # print('=====================', num_executed)
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
