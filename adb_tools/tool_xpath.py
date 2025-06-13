"""
Created on 2023年12月21日

@author: lenovo
"""

import os
import time

import cv2
from uiautomator2.xpath import XPath

from helper_hash import get_hash
from tool_env import bounds_to_rect
from tool_img import get_template_points, show, pil2cv2, cv2pil, b642cv2
from lxml import etree

import functools

import json

import pandas

from functools import cached_property


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

    # def long_click(self, x, y, duration: float = .5):
    #     pass

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

    def refresh(self, debug=False, wait_steady=True):
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


class 基本输入字段对象(object):
    def __init__(self, d):
        self.d = d

    @property
    def id(self):
        return self.d.get("id")


class 基本界面元素(基本输入字段对象):
    def __init__(self, d):
        super().__init__(d)
        self.matched = False

    @property
    def inverse(self):
        return self.d.get("inverse")

    @classmethod
    def from_dict(cls, d):
        if d.get("type") == 1:
            return Xml界面元素(d)
        else:
            return Screen界面元素(d)

    def match(self, job):
        raise NotImplementedError

    def execute(self, job, lines):
        if self.matched:
            try:
                exec(lines)
                return True
            except Exception as e:
                print(f"error when executing:{self.id}:{e}")


class Xml界面元素(基本界面元素):
    @property
    def xpath(self):
        return self.d.get("xpath")

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
    def __init__(self, d):
        super().__init__(d)
        self.tpls = [基本界面元素.from_dict(x) for x in d.get("tpls")]
        self.num_executed = 0
        self.num_conti_repeated = 0

    @property
    def lines(self):
        return self.d.get("lines")

    def execute(self, job):
        for tpl in self.tpls:
            if not tpl.matched:
                continue
            if tpl.execute(job, self.lines):
                self.num_executed += 1
                self.num_conti_repeated += bool(job.last_executed_block_id == self.id)
                job.last_executed_block_id = self.id
                return True

    def match(self, job):
        if not job.status and not self.only_when:
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


class 基本任务(基本输入字段对象):
    def __init__(self, fpath):
        if isinstance(fpath, str):
            assert os.path.exists(fpath)
            with open(fpath, "r", encoding="utf8") as fp:
                self.init(json.load(fp))
        elif isinstance(fpath, dict):
            self.init(fpath)
        else:
            raise ValueError(f"invalid type of fpath:{type(fpath)}")
        self.status = None
        self.last_executed_block_id = None

    def init(self, d):
        self.d = d
        self.blocks = [操作块(x) for x in self.d.get("blocks")]
        if self.d.get("device").get("is_windows"):
            self.device = Windows窗口设备(self.d.get("device"))
        else:
            self.device = SteadyDevice.from_ip_port(self.d.get("device").get("ip_port"))

    def 打开应用(self):
        script = f"am start -n {self.package}/{self.activity}"
        return self.device.adb.execute(script)

    def 关闭应用(self):
        script = f"am force-stop {self.package}"
        return self.device.adb.execute(script)

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

    def 执行操作块(self, block_id):
        self.match(block_id)
        block = next(filter(lambda b: b.id == block_id, self.blocks))
        block.execute(self)

    def match(self, block_id=None):
        self.device.snapshot(wait_steady=False)
        for block in self.blocks:
            if block_id is None or block.id == block_id:
                block.match(self)

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
            ["matched", "priority", "index"], ascending=[False, False, True]
        )

    def 执行任务(self, 单步=True):
        num_empty_repeated = 0
        while 1:
            self.match()
            df = self.get_df()
            print("job status:", self.status)
            print(df)

            tmp = df[df["matched"]]

            if not tmp[tmp.repeated >= tmp.max_num].empty:
                print("达到最大重复次数，停止执行")
                break

            匹配成功 = not tmp.empty

            if 匹配成功:
                self.执行操作块(tmp.iloc[0].id)
                num_empty_repeated = 0
            else:
                num_empty_repeated += 1
                if num_empty_repeated > self.max_empty:
                    print("达到最大空白屏次数，停止执行")
                    break

            if 单步:
                break

            if self.status == "完成" and not 匹配成功:
                break


class 任务快照设备(SteadyDevice):
    def __init__(self, ip_port, json):
        pass


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
