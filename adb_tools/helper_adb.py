'''
Created on 2023年11月24日
@author: lenovo
'''
# (base) PS C:\Users\lenovo> adb -s UJN0221118004154 tcpip 7001
# (base) PS C:\Users\lenovo> adb connect 192.168.0.148:7001
import glob
import os
import os
from pathlib import Path
import random
import re
from subprocess import TimeoutExpired
import subprocess
import time

import cv2
from django.utils.functional import cached_property
import numpy
import uiautomator2
from uiautomator2.xpath import XMLElement

from adb_tools import tool_devices
from adb_tools.common.exceptions import ElementNotFoundError, \
    NotNeedFurtherActions, TplNotFoundError
from adb_tools.tool_xpath import find_by_xpath, SteadyDevice
import helper_icmp
from helper_net import retry
from tool_cmd import 得到ADB连接状态
from tool_env import is_ipv4, is_string, bounds_to_center
from tool_file import get_suffix
from tool_img import bin2img, get_template_points, pil2cv2, to_gray, mask_to_img, \
    rgb_to_mono, cut_empty_margin
from tool_static import 得到一个不重复的文件路径, 路径到链接


# from base_adb import tool_devices
# from common.exceptions import ElementNotFoundError, TplNotFoundError, NotNeedFurtherActions
# from my_agent.settings import IMG_DIR, BASE_DIR, TMP_DIR
# from tool_rect import Rect
# from tool_xpath import find_by_xpath
def click_delay(self, delay=0.5):
    self.click()
    time.sleep(delay)


XMLElement.click_delay = click_delay


adb_exe = 'adb'

CUR_DIR = Path(__file__).resolve().parent

BASE_DIR = CUR_DIR.parent.parent

TMP_DIR = BASE_DIR / 'tmp' 

# ut_base_dir = f'{BASE_DIR}/ut'
if not TMP_DIR.exists():
    TMP_DIR.mkdir()


DEVICES = [
        {
        'ip': '192.168.0.148',
        'name': 'mate40',
        'port': '7001',
        'role': '测试',
        'id':'UJN0221118004154',
        'device_name': 'HWOCE-L',
        },

        {
        'ip': '192.168.0.115',
        'name': 'mate10',
        'port': '7002',
        'role': '测试2',
        'id':'D3H7N18126007114',
        'device_name': 'HWALP'
        },
        
        {
        'ip': '192.168.0.187',
        'name': 'honorv50',
        'port': '5556',
        'role': '测试3',
        'id': '8URDU19B26017523',
        },
        
        {
        'ip': '192.168.3.19',
        'name': 'honor60',
        'port': '6000',
        'role': '测试4',
        'id': 'A3KUVB1B18016880',
        },
    ]

DICT_DEVICES = {v.get('name'):v for v in DEVICES}

def wait_tobe_steady(adb, x, return_all=False, sleep_time=0.1):
    e = adb.find_xpath_safe(x).wait()
    while e is not None:
        time.sleep(sleep_time)
        new_e = adb.find_xpath_safe(x)
        new = new_e.wait()
        if new.info == e.info:
            return new if not return_all else new_e.all()
        else:
            e = new

def wait_to_disappear(adb, x, timeout=120):
    old = time.time()
    while time.time() - old < timeout:
        if adb.find_xpath_safe(x).wait() is None:
            return
    raise ValueError('timeout')


def scroll_to_most_left(adb, x):
    old = wait_tobe_steady(adb, x)
    while old is not None:
        adb.touch_center_move_right()
        new = wait_tobe_steady(adb, x)
        if new is None or new.info == old.info:
            break 
        old = new

def scroll_to_left(adb, l, wait=1000):
    b1 = l[-1].bounds
    b2 = l[0].bounds
    c1 = b1[2] - 100, b1[1]
    c2 = b2[0], b1[1]
    adb.swipe(c1, c2, wait)
    return c1[0] - c2[0]

def scroll_to_right(adb, l, wait=1000):
    b1 = l[-1].bounds
    b2 = l[0].bounds
    c1 = b1[2], b1[1]
    c2 = b2[0]+100, b1[1]
    adb.swipe(c2, c1, wait)
    return c2[0] - c1[0]

def scroll_to_bottom(adb, l, wait=1000):
    if len(l) > 1:
        b1 = l[-1].bounds
        b2 = l[0].bounds
        c1 = b1[0], b1[3] - 100
        c2 = b2[0], b2[3]
    else:
        b1 = l[-1].bounds 
        c1 = b1[0], b1[3]
        c2 = b1[0], b1[1]  
    
    # print(c1, c2)
    
    adb.swipe(c1, c2, wait)
    return c1[0] - c2[0]

def scroll_to_top(adb, l, wait=1000, max_span=None):
    b1 = l[-1].bounds
    b2 = l[0].bounds
    
    c1 = b1[0], b1[3] - 100
    c2 = b2[0], b2[3]
    span = c2[1] - c1[1]
    
    if max_span is not None and span >  max_span:
        delta = span - max_span
        c1 = c1[0], c1[1] - delta
    
    print(c2, c1, span)
    adb.swipe(c2, c1, wait)
    return span


def scroll_to_align(adb, l=None, duration=0.5, steps=None):
    if l is None:
        l = get_elements_safe_for_sure(adb, 
                              '//android.widget.LinearLayout[re:match(@resource-id, ".*/framesLayout")]',
                              # sleep_time=0.4,
                              )
    
    cx = adb.get_sys_width_height()[0] // 2
    b = l[-1].bounds
    y = b[1]-50
    x = min(b[2], cx*2 -200)
    print((x, y), (cx, y))
    adb.swipe((x, y), (cx, y), wait=500)
    # adb.ua2.swipe(x,y,cx,y, duration=duration, steps=steps)
    # adb.ua2.swipe_points([(x,y), (cx,y)])
    # adb.ua2.drag(x,y,cx,y, duration=duration)
    return x

    
def get_elements_safe(adb, x, force_not_empty=True):
    e = adb.find_xpath_safe(x)
    if force_not_empty:
        assert e.wait() is not None
    return e.all()

def get_elements_safe_for_sure(adb, x, sleep_time=0.1):
    return wait_tobe_steady(adb, x, return_all=True, sleep_time=sleep_time)

def to_info(l):
    return [x.info for x in l]

def get_all(adb, 
            xpath='//android.widget.TextView[re:match(@resource-id, ".*/text")]',
            fun_scroll=scroll_to_left,
            ):
    old = get_elements_safe(adb, xpath)
    while 1:
        for x in old:
            yield x
        fun_scroll(adb, old)
        new = get_elements_safe(adb, xpath)
        
        if to_info(new) != to_info(old):
            old = new
        else:
            break
        
        # if new[0].info != old[0].info:
        #     old = new
        # else:
        #     break

def is_element_wanted(adb, x, text):
    return getattr(x,'text') == text

def is_app_wanted(adb, x, text):
    return getattr(x,'text') == text and adb.has_same_icon()

def scroll_to_find(adb, xpath, text, fun_scroll=scroll_to_left, fun_match=is_element_wanted):
    for x in get_all(adb, xpath, fun_scroll):
        # if x.text == text:
        # print(x.info, x.text)
        if fun_match(adb, x, text):
            return x
        
def scroll_to_index(adb, xpath, index, fun_scroll=scroll_to_left, exclude=[]):
    s = set()
    for x in get_all(adb, xpath, fun_scroll):
        s.add(x.text)
        if x.text not in exclude and len(s) >= index:
            print('selected:', x.text)
            return x
        
 
def scroll_to_index_random(adb, 
                           xpath, 
                           end_index=100, 
                           fun_scroll=scroll_to_bottom, 
                           exclude=['渐渐放大',
                                    '模糊',
                                    ]):
    to_index = random.randint(0, end_index)
    print('to index:', to_index)
    return scroll_to_index(adb, xpath, to_index, fun_scroll=fun_scroll, exclude=exclude)

class NoFileDownloadedError(Exception):
    pass

class DummyTestException(Exception):
    pass

class SwitchOverviewError(Exception):
    pass


class ScreenShotEmpty(Exception):
    pass

class BaseAdb(object):
    # app_name = None
    # activity = None
    APP_INFO = {}
    timeout = 3
    INSTANCE_DICT = {}
    NAME = None
    # ICON = None

    
    DIR_CFG = Path(__file__).resolve().parent.parent.parent / 'adb_config'
    
    DIR_UPLOAD = '/sdcard/Download'
    
    DIR_TMP = '/sdcard/Download/temp'
    
    CAMERA_DIR = '/sdcard/DCIM/Camera'
    
    PICTURES_DIR = '/sdcard/Pictures'
    
    if not os.path.lexists(DIR_CFG):
        os.makedirs(DIR_CFG, exist_ok=True)
    
    def __str__(self):
        return self.ip_port
    
    @classmethod
    def get_all_jobs(cls):
        v =  list(filter(lambda x:x.startswith('job_'), dir(cls)))
        k = map(lambda x:f'{cls.NAME} - ' + (getattr(cls, x).__doc__ or '').strip(), v)
        v = map(lambda x:f'{cls.__name__}.{x}', v)
        return list(zip(v, k))
        

    
    def get_classname(self):
        return self.__class__.__name__
    
    def get_default_icon_name(self):
        return self.get_classname()
    
    @property
    def SYS_SCR_LOCK(self):
        return {'package': 'com.huawei.systemmanager',
         'activity': 'com.huawei.securitycenter.applock.password.LockScreenLaunchLockedAppActivity'}

    @property
    def APP_LAUNCH_LOCK(self):
        return {'package': 'com.huawei.systemmanager',
                'activity': 'com.huawei.securitycenter.applock.password.AuthLaunchLockedAppActivity',}

    @property
    def SYS_OVERVIEW(self):
        return {'package': 'com.huawei.android.launcher',
         'activity': '.unihome.UniHomeLauncher',}        

    def is_in_overview(self):
        xpath = '//android.widget.FrameLayout[re:match(@resource-id, ".*/task_view")]',
        return self.SYS_OVERVIEW == self.app_info and self.find_xpath_safe(xpath).exists

    def is_in_sys_scr_lock(self):
        return self.SYS_SCR_LOCK == self.app_info
    
    def is_in_app_launch_auth(self):
        return self.APP_LAUNCH_LOCK == self.app_info
    
    @property
    def fpath_icon(self):
        return CUR_DIR / f'icon_{self.get_default_icon_name().lower()}.png'
    
    def save_icon(self):
        cv2.imwrite(str(self.fpath_icon), self.get_icon())
        
    @cached_property
    def icon(self):
        return cut_empty_margin(rgb_to_mono(cv2.imread(str(self.fpath_icon)))) if self.fpath_icon.exists() else None 
    
    def get_icon(self):
        xpath = f'//android.widget.TextView[re:match(@resource-id, ".*/title")][@text="{self.NAME}"]/preceding-sibling::android.widget.ImageView'
        e = self.find_xpath_safe(xpath).wait()
        i = pil2cv2(e.screenshot())
        i = to_gray(i) > 250
        return mask_to_img(i)
    
    def has_same_icon(self):
        if self.icon is None:
            return True
        icon = cut_empty_margin(self.get_icon())
        if icon.shape != self.icon.shape:
            return False
        # return (icon !=self.icon)
        return (icon !=self.icon).sum() <= 100
    
    def clear_camera_dir(self):
        self.clear_temp_dir(base_dir=self.CAMERA_DIR)
        
    def get_latest_camera_file(self):
        return self.get_latest_file(base_dir=self.CAMERA_DIR)
    
    def pull_latest_camera_file(self, to_dir):
        return self.pull_lastest_file(to_dir, base_dir=self.CAMERA_DIR)
        
    def fix_jy_giveup_draft(self):
        # text="放弃" resource-id="com.lemon.lv:id/tvCancelResume" class="android.widget.TextView"
        # text="立即恢复" resource-id="com.lemon.lv:id/tvResumeNow" class="android.widget.Button"
        e1 = self.find_xpath_safe('//*[@text="放弃"]')
        e2 = self.find_xpath_safe('//*[@text="立即恢复"]')
        if e1.exists and e2.exists:
            e1.click()
            return True
        return False
         
    
    def fix_jy_update(self):
        e1 = self.find_xpath_safe('//android.widget.Button[re:match(@resource-id, ".*/btn_update_cancel")][@text="取消"]')
        e2 = self.find_xpath_safe('//android.widget.Button[re:match(@resource-id, ".*/btn_update_sure")][@text="更新"]')
        if e1.exists and e2.exists:
            e1.click()
            return True
        return False
    
    def fix_jy_no_in_jianji_tab(self):
        e1 = self.find_xpath_safe('//android.widget.TextView[re:match(@resource-id, ".*/tab_name")][@text="剪辑"]')
        if e1.exists:
            e1.click()
            return True
        return False
    
    def fix_db_update(self):
        # text="忽略" resource-id="com.larus.nova:id/tvDialogCancel" class="android.widget.TextView"
        # text="立即更新" resource-id="com.larus.nova:id/btnDialogConfirm" class="android.widget.TextView" 
        e1 = self.find_xpath_safe('//android.widget.TextView[re:match(@resource-id, ".*/tvDialogCancel")][@text="忽略"]')
        e2 = self.find_xpath_safe('//android.widget.TextView[re:match(@resource-id, ".*/btnDialogConfirm")][@text="立即更新"]')
        if e1.exists and e2.exists:
            e1.click()
            return True
        return False
    
    def fix_jy_come_gao(self):
        # resource-id="com.lemon.lv:id/ivClose" class="android.widget.ImageView"
        # text="去投稿" resource-id="com.lemon.lv:id/btnConfirm" class="android.widget.Button"
        e1 = self.find_xpath_safe('//android.widget.ImageView[re:match(@resource-id, ".*/ivClose")][@text=""]')
        e2 = self.find_xpath_safe('//android.widget.Button[re:match(@resource-id, ".*/btnConfirm")]')
        if e1.exists and e2.exists:
            e1.click()
            return True
        return False


    
    def get_all_fix_functions(self):
        return filter(lambda x:x.startswith('fix_'), dir(self))
        
    def try_to_fix_exceptions(self):
        for x in self.get_all_fix_functions():
            if getattr(self,x)():
                return True
        return False

        
    def go_back(self):
        self.ua2.keyevent('KEYCODE_BACK')

    def go_home(self):
        self.ua2.keyevent('KEYCODE_HOME')

    def volume_up(self):
        self.ua2.keyevent('KEYCODE_VOLUME_UP')

    def volume_down(self):
        self.ua2.keyevent('KEYCODE_VOLUME_DOWN')
    
    @classmethod
    def get_device_d_by_name(cls, name):
        d = DICT_DEVICES.get(name)
        for x in cls.get_devices_as_dict():
            if x.get('name') == d.get('device_name'):
                return x

    def __init__(self, device):
        if hasattr(device, 'device_id'):
            self.ip_port = device.device_id
        elif not device.get('ip') and device.get('id'):
            self.ip_port = device.get('id')
        else:
            self.ip_port = f'{device["ip"]}:{device["port"]}'
        self.device = device
        self.current_shot = None
        self.step_name = ''
        
        self.old_key = None
        self.current_key = None
        
    @property
    def ip(self):
        return self.ip_port.split(':', maxsplit=1)[0]
    
    
    @property
    def app_info(self):
        return {k:v for k, v in self.ua2.app_current().items() if k not in ('pid',)}

    @property
    def app_name(self):
        return self.APP_INFO.get('package')
    
    @property
    def activity(self):
        return self.APP_INFO.get('activity')

    def is_app_opened(self):
        return self.APP_INFO.get('package') == self.app_info.get('package')
            
    def is_app_main(self):
        return self.APP_INFO == self.app_info
        # d = self.ua2.app_current()
        # return d.get('package') == self.app_name and d.get('activity') == self.activity
    
    def remote_join(self, base_dir, fname):
        return os.path.join(base_dir, fname).replace('\\', '/')
    
    def get_files(self, base_dir='/sdcard/DCIM/Camera', ptn='*'):
        r = self.ua2.shell(f'ls -t {self.remote_join(base_dir, ptn)}')
        if r.exit_code == 0 and r.output:
            return list(map(lambda x:self.remote_join(base_dir, x), r.output.splitlines()))
        return []
    
    def get_files_safe(self, base_dir='/sdcard/DCIM/Camera', ptn='*'):
        old = None 
        while 1:
            new = self.get_files(base_dir, ptn)
            if new == old:
                return new
            print(f'waiting dir {base_dir}:', new, old)
            old = new
            time.sleep(1)
    
    
    def get_latest_file(self, base_dir='/sdcard/DCIM/Camera'):
        r = self.ua2.shell(f'ls -t {base_dir}')
        if r.exit_code == 0 and r.output:
            return f'{base_dir}/{r.output.splitlines()[0]}'
    
    def get_file_size(self, remote_fpath, is_file=True):
        r = self.ua2.shell(f'ls -lt  {remote_fpath}')
        i = 0 if is_file else 1
        if r.exit_code == 0 and r.output:
            l = r.output.splitlines()
            return int(re.split('\s+', l[i])[4]) if len(l) > i else None
            
    def get_latest_file_size(self, base_dir='/sdcard/DCIM/Camera'):
        return self.get_file_size(base_dir, is_file=False)
        # r = self.ua2.shell(f'ls -lt  {base_dir}')
        # if r.exit_code == 0 and r.output:
        #     l = r.output.splitlines()
        #     return int(re.split('\s+', l[i+1])[4]) if len(l) > i else None
        
    def pull_lastest_file(self, 
                          to_dir=TMP_DIR, 
                          base_dir='/sdcard/DCIM/Camera',
                          fpath = None,
                          ):
        src = self.get_latest_file(base_dir)
        if src:
            if fpath is None:
                if not os.path.lexists(to_dir):
                    os.makedirs(to_dir, exist_ok=True)
                dst = dst=os.path.join(to_dir, os.path.basename(src))
            else:
                dst = fpath
            self.ua2.pull(src, dst)
            print(dst)
            return dst
    
    
    def pull_file_safe(self, remote, local):
        old_size = None 
        while 1:
            new_size = self.get_file_size(remote)
            if new_size and new_size == old_size:
                self.ua2.pull(remote, local)
                return local  
            print(f'waiting {remote}:', new_size, old_size)
            old_size = new_size
            time.sleep(0.01)
        
    def pull_lastest_file_until(self, 
                                to_dir=TMP_DIR, 
                                base_dir='/sdcard/DCIM/Camera',
                                max_retry=100,
                                ):
        old_size = None 
        for i in range(max_retry):
            new_size = self.get_latest_file_size(base_dir)
            if new_size and new_size == old_size:
                fpath = self.pull_lastest_file(to_dir=to_dir, base_dir=base_dir)  
                if fpath is not None:
                    return fpath
            print(f'waiting file:{i}', new_size, old_size)
            old_size = new_size
            time.sleep(1)
        raise NoFileDownloadedError
    
    def pull_latest_picture_weixin(self,
                                   to_dir=TMP_DIR,
                                   base_dir='/sdcard/Pictures/WeiXin',
                                   max_retry=100,
                                   ):
        return self.pull_lastest_file_until(to_dir, base_dir, max_retry)
        
    def pull_lastest_file_to_local_tmp(self, base_dir='/sdcard/DCIM/Camera', tmp_dir=None):
        return self.pull_lastest_file(to_dir=TMP_DIR if tmp_dir is None else tmp_dir, base_dir=base_dir)
    
    def clear_temp_dir(self, base_dir=None):
        base_dir = base_dir or self.DIR_TMP
        self.ua2.shell(f'rm -rf {base_dir}')
        time.sleep(0.1)
        self.ua2.shell(f'mkdir {base_dir}')
        
    def clear_pdd_goods_dir(self):
        self.clear_temp_dir(base_dir='/sdcard/DCIM/Pindd/goods')
    
    def get_pdd_goods_jpgs(self):
        return self.get_files_safe(base_dir='/sdcard/DCIM/Pindd/goods', ptn='*.jpg')
    
    def pull_pdd_goods_jpgs(self):
        rtn = []
        for remote in self.get_pdd_goods_jpgs():
            local = self.pull_file_safe(remote, 得到一个不重复的文件路径(remote))
            rtn.append(路径到链接(local))
        return rtn
    
    def copy_file_to_temp(self, fpath, sleep_span=0.1):
        src = fpath
        suffix = os.path.basename(fpath).rsplit('.')[-1] 
        dst = f'{self.DIR_TMP}/{time.time()}.{suffix}'
        # print(src, dst)
        self.ua2.shell(f'cp {src} {dst}')
        time.sleep(sleep_span)
        self.broadcast(dst)
        
    def push_file_to_temp(self, 
                          src, 
                          sleep_span=0.1, 
                          clean_temp=False, 
                          use_timestamp=True,
                          base_dir=None,
                          ):
        
        base_dir = base_dir or self.DIR_TMP
        if clean_temp:
            self.clear_temp_dir(base_dir)
        
        if not use_timestamp:
            dst = f'{base_dir}/{os.path.basename(src)}'
        else:
            dst = f'{base_dir}/{time.time()}.{get_suffix(src)}'
        print(src, dst)
        print(self.push_file(src, dst))
        time.sleep(sleep_span)
        self.ua2.shell(f'touch {dst}')
        time.sleep(sleep_span)
        self.broadcast(dst)
        return dst
    
    def push_file_to_pictures(self,
                              src, 
                              sleep_span=0.1, 
                              use_timestamp=True):
        return self.push_file_to_temp(src, 
                                      sleep_span, 
                                      False, 
                                      use_timestamp, 
                                      self.PICTURES_DIR)
                
    def push_file_to_download(self, 
                              src, 
                              sleep_span=0.1, 
                              clean_temp=False, 
                              use_timestamp=True,
                              ):
        return self.push_file_to_temp(src, sleep_span, clean_temp, use_timestamp, base_dir='/sdcard/Download')
    
    def push_file_to_temp_all(self, files):
        self.clear_temp_dir()
        for x in files:
            self.push_file_to_temp(x, clean_temp=False, sleep_span=1)
        
    
    def copy_file_to_temp_all(self, files, sleep_span=0.1):
        self.clear_temp_dir()
        for fpath in files:
            self.copy_file_to_temp(fpath, sleep_span)

    def set_timeout(self, timeout):
        self.ua2.implicitly_wait(timeout)
        return self
    
    def touch_file(self, fpath):
        self.ua2.shell(f'touch {fpath}')
        self.ua2.keyevent('KEYCODE_HOME')
        time.sleep(1)
        self.open_filemanager()
        time.sleep(0.1)
        self.broadcast(fpath)
    
    def broadcast(self, fpath):
        cmd = f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{fpath}'
        return self.ua2.shell(cmd)


    @classmethod
    def get_device(cls, name):
        return list(filter(lambda x:x.get('name') == name, DEVICES))[0]


    @classmethod
    def get_instance_by_device(cls, name_device):
        return cls(cls.get_device(name_device))

    def search_ui_element(self, txt):
        return re.compile(f'<.*{txt}.*\r\n', re.M).findall(self.ua2.dump_hierarchy())
            
    @cached_property
    def ua2(self):
        obj = uiautomator2.connect(self.ip_port)
        obj.settings['wait_timeout'] = self.timeout
        obj.set_fastinput_ime()
        return obj

    def show_current_app(self):
        """查看当前打开的app信息, 为打开应用提供信息
            {'package': 'com.lemon.lv',
             'activity': 'com.vega.main.MainActivity',
             'pid': 10166}
        """
        return self.ua2.current_app()

    def show_all_apps(self):
        """
        查看所有的应用列表
        :return:
        """
        return self.ua2.app_list()

    def open_app(self, force_open=False, use_monkey=False):
        if force_open or not self.is_app_opened():
            self.ua2.app_start(self.app_name, activity=self.activity, stop=True, use_monkey=use_monkey)
        return self
    
    def Pdd打开url(self, url):
        self.ua2.shell(
            ['am', 'start', '-a', 'android.intent.action.VIEW', '-d', url, '-n', 'com.xunmeng.pinduoduo/activity.NewPageActivity'])
    
    def open_certain_app(self, 
                         package, 
                         activity, 
                         stop=False, 
                         use_monkey=False,
                         ):
        self.ua2.app_start(package, activity=activity, stop=stop, use_monkey=use_monkey)

    def close_certain_app(self, app_name):
        self.ua2.app_stop(app_name)

    def close_app(self):
        self.ua2.app_stop(self.app_name)
        return self
    
    def open_filemanager(self):
        d = {'package_name': 'com.huawei.filemanager',
         'activity': 'com.huawei.hidisk.filemanager.FileManager',
         'a2':'com.huawei.hidisk.view.activity.category.CategoryFileListActivity',
         'a3':'com.huawei.hidisk.view.activity.category.StorageActivity',
         }
        self.ua2.app_start(package_name=d.get('package_name'),
                           activity=d.get('activity'))
        self.ua2.app_start(package_name=d.get('package_name'), 
                           activity=d.get('activity'))
        return self

    def open_filemanager2(self):
        d = {'package_name': 'com.hihonor.filemanager',
         'activity': 'com.hihonor.honorcloud.filemanager.FileManager',
         'a2':'com.hihonor.honorcloud.view.activity.category.CategoryFileListActivity',
         'a3':'com.hihonor.honorcloud.view.activity.category.StorageActivity',
         }
        self.ua2.app_start(package_name=d.get('package_name'),
                           activity=d.get('activity'))
        self.ua2.app_start(package_name=d.get('package_name'),
                           activity=d.get('a3'))
        return self



    def save_page_content(self, path):
        content = self.page_content().encode('utf8')
        with open(path, 'wb') as fp:
            fp.write(content)

    def page_content(self, debug=False):
        content = self.ua2.dump_hierarchy()
        if debug:
            # print([content])
            # content = content.replace("'\\", '').encode('utf8')
            self.save_page_content('page.xml')
            # content = content.encode('utf8')
            # with open('page.xml', 'wb') as fp:
            #     fp.write(content)
        return content

    def get_page(self):
        content = self.ua2.dump_hierarchy()
        content = content.replace("'\\", '').encode('utf8')
        return content
    
    def show_page(self, fpath=None, show=True):
        import webbrowser
        fpath = BASE_DIR / 'page.xml' if fpath is None else fpath
        with open(fpath, 'wb') as fp:
            fp.write(self.get_page())
        if show:
            webbrowser.open(f'file:///{fpath}')
            
    
    def show_element(self, element):
        import webbrowser
        from lxml import etree
        fpath = BASE_DIR / 'elem.xml'
        xml = etree.tostring(element.elem, pretty_print=True)
        with open(fpath, 'wb') as fp:
            fp.write(xml)
        webbrowser.open(f'file:///{fpath}')
    

    def save_error_page(self, error_dir, page_name=None):
        import traceback
        if page_name:
            fname = page_name
        else:
            fname = f'{int(time.time())}'
        if not os.path.lexists(error_dir):
            os.makedirs(error_dir)
            
        error_path = f'{error_dir}/{fname}.xml'
        error_png = f'{error_dir}/{fname}.png'
        error_exc = f'{error_dir}/{fname}.txt'
        self.show_page(error_path, show=False)
        with open(error_exc, 'w') as fp:
            traceback.print_exc(file=fp)
        cv2.imwrite(error_png, self.ua2.screenshot(format='opencv'))
        return error_path, error_png, error_exc

    def push_files(self, fpaths, dst_dir='/storage/sdcard0/Pictures/Browser'):
        for fpath in fpaths:
            self.ua2.push(
                    src=fpath,
                    dst='%s/%s' % (dst_dir, os.path.basename(fpath)),
                )
            
    def push_files_glob(self, ptn, dst_dir='/storage/sdcard0/Pictures/Browser'):
        self.push_files(glob.glob(ptn), dst_dir)
    

    def  find_new(self, **kwargs):
        """
        :param kwargs:
            "text": (0x01, None),  # MASK_TEXT,
            "textContains": (0x02, None),  # MASK_TEXTCONTAINS,
            "textMatches": (0x04, None),  # MASK_TEXTMATCHES,
            "textStartsWith": (0x08, None),  # MASK_TEXTSTARTSWITH,
            "className": (0x10, None),  # MASK_CLASSNAME
            "classNameMatches": (0x20, None),  # MASK_CLASSNAMEMATCHES
            "description": (0x40, None),  # MASK_DESCRIPTION
            "descriptionContains": (0x80, None),  # MASK_DESCRIPTIONCONTAINS
            "descriptionMatches": (0x0100, None),  # MASK_DESCRIPTIONMATCHES
            "descriptionStartsWith": (0x0200, None),  # MASK_DESCRIPTIONSTARTSWITH
            "checkable": (0x0400, False),  # MASK_CHECKABLE
            "checked": (0x0800, False),  # MASK_CHECKED
            "clickable": (0x1000, False),  # MASK_CLICKABLE
            "longClickable": (0x2000, False),  # MASK_LONGCLICKABLE,
            "scrollable": (0x4000, False),  # MASK_SCROLLABLE,
            "enabled": (0x8000, False),  # MASK_ENABLED,
            "focusable": (0x010000, False),  # MASK_FOCUSABLE,
            "focused": (0x020000, False),  # MASK_FOCUSED,
            "selected": (0x040000, False),  # MASK_SELECTED,
            "packageName": (0x080000, None),  # MASK_PACKAGENAME,
            "packageNameMatches": (0x100000, None),  # MASK_PACKAGENAMEMATCHES,
            "resourceId": (0x200000, None),  # MASK_RESOURCEID,
            "resourceIdMatches": (0x400000, None),  # MASK_RESOURCEIDMATCHES,
            "index": (0x800000, 0),  # MASK_INDEX,
            "instance": (0x01000000, 0)  # MASK_INSTANCE,
        :return:
        """
        # print('kwargs', kwargs)
        return self.ua2(**kwargs)

    @retry(3)
    def exists(self, page_name='', **kwargs):
        if self.find_new(**kwargs).exists():
            return self
        else:
            time.sleep(0.1)
        raise ElementNotFoundError(f'查找元素失败: {kwargs}', page_name=page_name)

    def exists_no_retry(self, **kwargs):
        if self.find_new(**kwargs).exists():
            return True
        return False

    def exists_no_raise_exception(self, **kwargs):
        try:
            return self.exists(**kwargs)
        except ElementNotFoundError:
            return False


    @retry(3)
    def click_element(self, find_index=0, page_name='', **kwargs):
        """
        点击元素
        :param find_index: 根据kwargs返回多个结果时, 根据该索引位定位到具体元素
        :param kwargs: 查询条件
        :param page_name: 当前页面
        :return:
        """
        try:
            self.find_new(**kwargs)[find_index].click()
            return self
        except:
            raise ElementNotFoundError(f'查找元素失败: {kwargs}', page_name=page_name)

    @retry(3)
    def find_by_xpath(self, xpath):
        """根据xpath查找元素"""
        return self.ua2.xpath(xpath)

    @retry(3)
    def exists_by_find_xpath(self, xpath):
        return self.ua2.xpath(xpath).exists
    
    def find_xpath_safe(self, xpath):
        return find_by_xpath(self.ua2, xpath)

    def find_xpath_steady(self, xpath, old_key=None):
        sd = SteadyDevice(self, old_key)
        rtn = sd.find_xpath_safe(xpath)
        self.old_key = self.current_key
        self.current_key = sd.key
        return rtn
    
    def is_steady_not_changed(self):
        return self.current_key == self.old_key

    def click_and_input(self, txt, page_name='', **kwargs):
        """光标移动至输入框, 并输入内容"""
        try:
            el = self.find_new(**kwargs)
            el.click()
        except:
            raise ElementNotFoundError(f'查找元素失败: {kwargs}', page_name=page_name)
        el.send_keys(txt)

        return self

    def go_back_untill_prompt(self, x, num_retry=5):
        for i in range(num_retry):
            e = self.find_xpath_safe(x).wait()
            if e is not None:
                return True
            print(i, 'trying go back:', x)
            self.go_back()
        raise ValueError(x)
    
    def go_back_untill_gone(self, x, num_retry=5, no_wait=False):
        for i in range(num_retry):
            if not self.has_elements(x, no_wait):
                return 
            print(i, 'trying go back:', x)
            self.go_back()
            time.sleep(0.5)
        raise ValueError(x)
    
    def click_untill_gone(self, x, num_retry=5):
        clicked = False
        for i in range(num_retry):
            # self.find_xpath_safe(x).wait(timeout).click()
            e = self.find_xpath_safe(x).wait()
            if e is not None:
                self.do_click_element_top_center(e)
                clicked = True
            if self.find_xpath_safe(x).wait_gone() and clicked:
                return True
            print(i, 'retrying:', x)
        raise ValueError(x)
    
    def click_untill_prompt(self, x, y, num_retry=5):
        clicked = False
        for i in range(num_retry):
            e = self.find_xpath_safe(x).wait()
            if e is not None:
                self.do_click_element_top_center(e)
                clicked = True
            if self.find_xpath_safe(y).wait() and clicked:
                return True
            print(i, 'retrying:', x)
        raise ValueError(x)
    
    @classmethod
    def kill_adb_server(cls, encoding='utf8'):
        # f'{adb_exe} kill-server'
        cmd = 'taskkill /F /IM adb.exe'
        process = subprocess.Popen(cmd, 
                                    # encoding=encoding, 
                                   shell=True, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        return process.communicate() 
        
    
    @classmethod
    def reconnect(cls, ip_port, encoding='utf8'):
        process = subprocess.Popen(f'{adb_exe} connect {ip_port}', 
                                   encoding=encoding, 
                                   shell=True, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        return process.communicate() 
        
    
    def connect(self):
        return self.reconnect(self.ip_port)


    
    def 是否离线(self):
        return BaseAdb.is_offline(self.ip_port)
    
    
    def 重连设备(self):
        return BaseAdb.reconnect(self.ip_port)
    
    def 尝试重连设备(self, 最大重连次数=3):
        for i in range(最大重连次数):
            print('尝试重连设备:', i)
            try:            
                r = helper_icmp.IcmpScan.检测设备状态(self.ip)
            except OSError:
                r = False
            
            if not r:
                print(f'没有检测到设备存活：{self.ip}, 等待3秒。。。')
                time.sleep(3)
                continue
            
            r = BaseAdb.reconnect(self.ip_port)
            
            print(r)
            
            r = 得到ADB连接状态(r)
            
            if r == 10061:
                print(f'adb 连接不成功：{self.ip_port}')
                time.sleep(1)
                print('尝试关闭本机adb 服务')
                print(BaseAdb.kill_adb_server())
                time.sleep(3)
                continue
            elif r:
                print(f'未知错误：{r}， 等待3秒。。。')
                time.sleep(3)
                continue
            
            if BaseAdb.is_offline(self.ip_port):
                print(f'{self.ip_port} 离线，重启本地服务中。。。')
                print(BaseAdb.kill_adb_server())
                continue
            
            break



    
    @classmethod
    def start_scrcpy(cls, ip_port, encoding='utf8', shell=True, return_directly=False):
        process = subprocess.Popen(f'scrcpy -s {ip_port} --no-audio --always-on-top', 
                                   encoding=encoding, 
                                   shell=shell, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        return process.communicate() if not return_directly else process
    

    @classmethod
    def start_and_listen_scrcpy(cls, 
                                ip_port, 
                                encoding='utf8', 
                                ):
        
        cmd = f'scrcpy -s {ip_port} --no-audio --always-on-top'
        
        print(cmd)
        process = subprocess.Popen(cmd, 
                                   encoding=encoding, 
                                    shell=True, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        time.sleep(3)
        while 1:
            output = process.stdout.readline()
            if output:
                print(output)        
            
            # err = process.stderr.readline()
            # if err:
            #     print(err)        

            
            # rtn = process.wait(1)
            rtn = process.poll()
            # print('....')
            if rtn is not None:
                break
    
    def setup(self, encoding='utf8'):
        process = subprocess.Popen(f'{adb_exe} -s {self.device["id"]} tcpip {self.device["port"]}', 
                                   encoding=encoding, 
                                   shell=True, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        print(process.communicate())
        
        process = subprocess.Popen(f'{adb_exe} connect {self.ip_port}', 
                                   encoding=encoding, 
                                   shell=True, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        return process.communicate()
    
    def auto_init_wifi_connection(self):
        if not is_ipv4(self.ip_port):
            ip = self.ua2.wlan_ip
            port = 7080#random.randint(7006, 8006)
            self.init_wifi_connection(device_id=self.ip_port, ip=ip, port=port)
    
    @classmethod
    def init_wifi_connection(cls, index=None, ip=None, port=None, device_id=None):
        d = {}
        if index is not None:
            d.update(DEVICES[index])
            
        if device_id is not None:
            d['id'] = device_id
        
        if ip is not None:
            d.update(ip=ip)
            
        if port is not None:
            d.update(port=port) 
        cls(d).setup()
        
    @classmethod
    def init_wifi_my_mate10(cls, ip=None, port=None):
        cls.init_wifi_connection(1,ip=ip,port=port)
        
    def geo_fix(self):
        self.execute("emu geo fix 121.49612 31.24010")
        return self
    
    @property
    def location(self):
        return self.execute('dumpsys location')
    
    def test(self):
        print(self.execute("am start-activity -a com.android.settings/.Settings\$LocationSettingsActivity"))
            
    @property
    def cmd(self):
        return f'{adb_exe} -s {self.ip_port} shell'
    
    @property
    def pull(self):
        pass 
        
    
    # def push_fileobj(self, fileobj, dst="", mode=0o644):
    #     modestr = oct(mode).replace('o', '')
    #     pathname = '/upload/' + dst.lstrip('/')
    #     filesize = 0
    #     if isinstance(src, six.string_types):
    #         if re.match(r"^https?://", src):
    #             r = requests.get(src, stream=True)
    #             if r.status_code != 200:
    #                 raise IOError(
    #                     "Request URL {!r} status_code {}".format(src, r.status_code))
    #             filesize = int(r.headers.get("Content-Length", "0"))
    #             fileobj = r.raw
    #         elif os.path.isfile(src):
    #             filesize = os.path.getsize(src)
    #             fileobj = open(src, 'rb')
    #         else:
    #             raise IOError("file {!r} not found".format(src))
    #     else:
    #         assert hasattr(src, "read")
    #         fileobj = src
    #
    #     try:
    #         r = self.http.post(pathname,
    #                            data={'mode': modestr},
    #                            files={'file': fileobj}, timeout=300.0)
    #         if r.status_code == 200:
    #             return r.json()
    #         raise IOError("push", "%s -> %s" % (src, dst), r.text)
    #     finally:
    #         fileobj.close()
    
    @classmethod
    def get_devices(cls):
        process = subprocess.Popen(f'{adb_exe} devices -l', 
                                   encoding='utf8', 
                                   shell=True, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        return process.communicate()

    

    
    @property
    def devices(self):
        return self.get_devices()
        

    @classmethod
    def get_devices_as_dict(cls):
        return list(tool_devices.parse_devices(BaseAdb.get_devices()[0]))
    
    @classmethod
    def is_offline(cls, ip_port):
        l = cls.get_devices_as_dict()
        l = list(filter(lambda x:x.get('id') == ip_port, l))
        return l[0].get('offline') if  l else None
    
    
    @classmethod
    def get_devcie_ids(cls):
        return list(map(lambda x:x.get('id'), cls.get_devices_as_dict()))
    
    
    @classmethod
    def first_device(cls):
        return list(cls.get_devices_as_dict())[0]

    @classmethod
    def last_device(cls):
        return list(cls.get_devices_as_dict())[-1]
    
    @classmethod
    def from_ip_port(cls, ip_port):
        return cls({'id':ip_port})
    
    @classmethod
    def first_device_usb(cls):
        for d in cls.get_devices_as_dict():
            if not is_ipv4(d.get('id')):
                return d
    
    @classmethod
    def first_device_ip(cls):
        for d in cls.get_devices_as_dict():
            if is_ipv4(d.get('id')):
                return d
            
    @classmethod
    def first_device_name(cls, name):
        return list(filter(lambda x:x.get('name') == name, cls.get_devices_as_dict()))[0]
    
    @classmethod
    def first_device_model(cls, name):
        return list(filter(lambda x:x.get('model') == name, cls.get_devices_as_dict()))[0]
    
    
    @classmethod
    def first_adb_name(cls, name):
        return cls(cls.first_device_name(name))
    
    @classmethod
    def first_adb(cls):
        return cls(cls.first_device())


    @classmethod
    def last_adb(cls):
        return cls(cls.last_device())

    @classmethod
    def first_adb_usb(cls):
        d = cls.first_device_usb()
        return cls(d) if d else None

    @classmethod
    def first_adb_ip(cls):
        return cls(cls.first_device_ip())

    
    @classmethod
    def get_dids_include_wifi(cls, did):
        yield did
        for x in DEVICES:
            if x.get('id') == did:
                yield f'{x["ip"]}:{x["port"]}'
    
    @classmethod
    def is_device(cls, did, d):
        pass
    
    
    @classmethod
    def get_adb_by_device_id(cls, did):
        ids = cls.get_devcie_ids()
        for x in cls.get_dids_include_wifi(did):
            if x in ids:
                return cls({'id': x})
        raise ValueError
    
    @classmethod
    def get_adb_by_device_name(cls, name):
        d = cls.get_device_d_by_name(name=name)
        if d is not None:
            return cls(d)
        raise ValueError(f'not found devices:{name}')
    
    @classmethod
    def my_mate10(cls):
        return cls.get_adb_by_device_name(name='mate10')

    @classmethod
    def my_mate40(cls):
        return cls.get_adb_by_device_name(name='mate40')

    @classmethod
    def my_vivo(cls):
        return cls.first_adb_name('PD1616B')
    
    @classmethod
    def lq_honorv50(cls):
        return cls.get_adb_by_device_id(did='8URDU19B26017523')


    @classmethod
    def lq_honor60(cls):
        return cls.get_adb_by_device_id(did='A3KUVB1B18016880')
    

    
    def execute(self, script, encoding='utf8'):
        process = subprocess.Popen(self.cmd, 
                                   encoding=encoding, 
                                   shell=True, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        return process.communicate(input=script)
    
    def push_file(self, src, dst, encoding='utf8'):
        cmd = f'{adb_exe} -s {self.ip_port} push {src} {dst}'
        process = subprocess.Popen(cmd, 
                                   encoding=encoding, 
                                   shell=True, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        return process.communicate()

    def pull_file(self, src, dst, encoding='utf8'):
        cmd = f'{adb_exe} -s {self.ip_port} pull "{src}" "{dst}"'
        process = subprocess.Popen(cmd, 
                                   encoding=encoding, 
                                   shell=True, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE
                                   )
        return process.communicate()
    
    def move_files_to_tmp(self,
                          cmd='find / -name *.mp4 -type f -size +100M 2>&1 | grep -v "Permission denied"'
                          ):
        self.clear_temp_dir()
        r = self.execute(cmd)
        for i, x in enumerate(r[0].splitlines()):
            print(i, x)
            fname =os.path.basename(x)
            # fpath = os.path.join(self.DIR_TMP, fname)
            self.ua2.shell(f'mv "{x}" "{self.DIR_TMP}/{fname}"', stream=True)
        
    def move_temp_dir(self, to_dir='z:/movie'):
        print(self.pull_file(self.DIR_TMP, to_dir))
    
    def move_files_to_pc(self, 
                         cmd='find / -name *.mp4 -type f -size +100M 2>&1 | grep -v "Permission denied"', 
                         to_dir='z:/movie'):
        self.move_files_to_tmp(cmd)
        self.move_temp_dir(to_dir)
        self.clear_temp_dir()
        # r = self.execute(cmd)
        # for i, x in enumerate(r[0].splitlines()):
        #     print(i, x)
        #     fname =os.path.basename(x)
        #     fpath = os.path.join(to_dir, fname)
        #     if not os.path.lexists(fpath):
        #         self.ua2.pull(x, fpath)
        #     self.ua2.shell(f'rm -f "{x}"')
        
    def move_flac_to_pc(self):
        self.move_files_to_pc(cmd='find / -name *.flac 2>&1 | grep -v "Permission denied"')
            
    
    def dump(self):
        return self.execute('uiautomator dump')
    
    def screen_shot(self):
        return bin2img(self.execute(script=b'screencap -p', encoding=None)[0].replace(b'\r\n', b'\n'))
    
    def screen_shot_safe(self):
        img = self.screen_shot()
        if img is None:
            self.尝试重连设备(最大重连次数=3)
            img = self.screen_shot()
        if img is None:
            raise ScreenShotEmpty
        return img
    
    
    def save_screen_shot(self, chrop=False, img_dir=None):
        cv2.imwrite(str(img_dir / ('%d.png' % int(time.time()))), self.screen_shot(chrop=chrop))
    
    def find_template(self, img, img_shot=None):
        img_shot = img_shot if img_shot is not None else self.screen_shot()
        return get_template_points(img_shot, img)
    
    def has_template(self, img):
        return len(self.find_template(img)) > 0
    
    def do_click(self, x, y):
        self.execute(f'input tap {x} {y}')
        return self

    def do_touch_move(self, src, dst):
        a = self.ua2.touch.down(*src)
        time.sleep(0.5)
        a.move(*dst)

    def 特殊双击(self, x, y):
        self.execute(f'input tap {x} {y}&sleep 0.1;input tap {x} {y}&sleep 0.01;input tap {x} {y}')
        return self
        # self.do_click(x, y)
        # time.sleep(0.1)
        # self.ua2.double_click(x, y, 0.01)
    
    def do_dbclick(self, x, y):
        return self.特殊双击(x, y)
        # self.execute(f'input tap {x} {y}&sleep 0.1;input tap {x} {y}')
        # return self
    
    
    def do_double_click(self, x, y):
        self.ua2.double_click(x, y, 0.01)
    
    def do_click_element_top_center(self, e):
        return self.do_click(e.center()[0], e.rect[1]) if e is not None else None
    
    def swipe(self, start, end, wait=100):
        self.execute(f'input swipe {start[0]} {start[1]} {end[0]} {end[1]} {wait}')
        return self
    
    def do_longclick(self, x=None, y=None, duration=2000):
        if x is None or y is None:
            cx, cy = self.get_sys_center()
            x = x or cx
            y = y or cy
        self.swipe((x, y), (x, y), duration)

    # def get_sys_width_height(self):
    #     if self.current_shot is None:
    #         self.screen_shot()
    #     h,w = self.current_shot.shape[:2]
    #     return w, h

    def get_sys_width_height(self):
        w,h = self.ua2.window_size()
        return w, h
    
    @cached_property
    def sys_width_height(self):
        return self.get_sys_width_height()
    
    @cached_property
    def W(self):
        return self.sys_width_height[0]

    @cached_property
    def H(self):
        return self.sys_width_height[1]

    def get_sys_center(self):
        w, h = self.sys_width_height
        return w//2, h//2
    
    @cached_property
    def sys_center(self):
        return self.get_sys_center()

    def scroll_down(self,distance=200, duration=None, wait=None):
        w, h = self.get_sys_width_height()
        if wait is None:
            self.ua2.swipe(w // 2, h // 2, w // 2, (h // 2) - distance, duration=duration)
        else:
            self.swipe((w // 2, h // 2), (w // 2, (h // 2) - distance), wait=wait)
            
    
        
    
    def scroll_down_untill_prompt(self, x, distance=200, retry_num=5):
        for _ in range(retry_num):
            if self.find_xpath_safe(x).wait() is not None:
                break
            self.scroll_down(distance)
    

    def scroll_up(self,distance=200, duration=None):
        w, h = self.get_sys_width_height()
        self.ua2.swipe(w // 2, h // 2, w // 2, (h // 2) + distance, duration=duration)
        # self.swipe((w // 2, h // 2), (w // 2, (h // 2) - distance), wait=duration)

    
    def has_element(self, x, no_wait=False):
        e = self.find_xpath_safe(x)
        if no_wait:
            return len(e.all()) > 0
        return e.wait() is not None
    
    def has_elements(self, l, no_wait=False):
        if not is_string(l):
            for x in l:
                if self.has_element(x, no_wait):
                    return True
            return False
        return self.has_element(l, no_wait)
    
    def scroll_up_untill_prompt(self, x, distance=200, retry_num=5, no_wait=True):
        for _ in range(retry_num):
            # if self.find_xpath_safe(x).wait() is not None:
            if self.has_element(x, no_wait):
                break
            self.scroll_up(distance)

    
    def refresh(self):
        w, h = self.get_sys_width_height()
        return self.swipe((w//2, h//2-200), (w//2,h//2+200)) 

    def send_text(self, txt):
        self.execute(f'input text {txt}')
        return self
    
    def send_text_chinese(self, txt):
        self.execute(f'am broadcast -a ADB_INPUT_TEXT --es msg "{txt}"')
        return self
    
    @retry(3)
    def find(self, name):
        return self.INSTANCE_DICT.get(name)(self, name)
    
    def not_found(self, name):
        try:
            self.INSTANCE_DICT.get(name)(self, name)
            raise NotNeedFurtherActions
        except TplNotFoundError:
            return self
        
    def touch_center_move_left(self):
        old = time.time()
        x, y = self.get_sys_center()
        self.ua2.touch.down(x,y).move(0, y)
        print('swipe', time.time() - old)
    
    
    def 触摸高度四分之三位置滑动到二分之一(self, 不安全模式=False, duration=0.5):
        x = self.W // 2
        src=(x, self.H * 3 // 4)
        dst=(x, self.H//2)
        if 不安全模式:
            self.do_touch_move(src, dst)
        else:
            self.ua2.drag(src[0], src[1], dst[0], dst[1], duration=duration)
        
    
    def 触摸高度四分之一位置水平向左滑动(self, duration=0.5):
        x = self.W // 2
        src=(x, self.H * 1 // 4)
        dst=(0, self.H * 1 // 4)
        self.ua2.drag(src[0], src[1], dst[0], dst[1], duration=duration)
            
    
    def touch_center_move_right(self):
        old = time.time()
        x, y = self.get_sys_center()
        self.ua2.touch.down(x,y).move(x+x, y)
        print(time.time() - old)

    def scroll_center_move_left(self, wait=500):
        x, y = self.get_sys_center()
        self.swipe((x, y), (0, y), wait=wait)
        
    def scroll_center_move_right(self, wait=500):
        x, y = self.get_sys_center()
        self.swipe((x, y), (x+x, y), wait=wait)
        
    def scroll_center_move_up(self):
        x, y = self.get_sys_center()
        self.swipe((x, y), (x, 0), wait=500)

    def scroll_center_move_down(self):
        x, y = self.get_sys_center()
        self.swipe((x, y), (x, y+y), wait=500)
    
    def switch_overview(self):
        self.ua2.keyevent('KEYCODE_APP_SWITCH')

    def app_switch(self):
        self.ua2.keyevent('KEYCODE_APP_SWITCH')
        
    def enter(self):
        self.ua2.keyevent("KEYCODE_ENTER")
        
    def poweron(self):
        self.ua2.keyevent("KEYCODE_POWER")
        
    def unlock_screen(self, pwd):
        self.poweron()
        self.scroll_center_move_up()
        while 1:
            time.sleep(1)
            self.send_text(pwd)
            self.enter()
            if not self.is_in_sys_scr_lock():
                break

    def unlock_app(self, pwd):
        if self.is_in_app_launch_auth():
            self.ua2.click(0.8, 0.95)
            time.sleep(1)
            self.send_text(pwd)
            self.enter()

    @property
    def xpath_taskview(self):
        # resource-id="com.huawei.android.launcher:id/task_view" class="android.widget.FrameLayout"
        return '//android.widget.FrameLayout[re:match(@resource-id, ".*/task_view")]',
    
    def open_overview_and_scroll_to_most_left(self):
        self.switch_overview()
        scroll_to_most_left(self, self.xpath_taskview)
    
    @property
    def xpath_titleview(self):
        # resource-id="com.huawei.android.launcher:id/title" class="android.widget.TextView
        return '//android.widget.TextView[re:match(@resource-id, ".*/title")]'
    
    # def scroll_find_app(self, icon_match=False):
    #     e = scroll_to_find(self, 
    #                    xpath=self.xpath_titleview, 
    #                    text=self.NAME, 
    #                    fun_scroll=lambda *x:self.scroll_center_move_left(), 
    #                    fun_match=is_app_wanted if icon_match else is_element_wanted,
    #                    )
    #
    #     if e is None:
    #         e = scroll_to_find(self, 
    #                        xpath=self.xpath_titleview, 
    #                        text=self.NAME, 
    #                        fun_scroll=lambda *x:self.scroll_center_move_right(), 
    #                        fun_match=is_app_wanted if icon_match else is_element_wanted,
    #                        )
    #     return e

    def scroll_find_app(self, icon_match=False):
        fun_scrolls = (self.scroll_center_move_right, self.scroll_center_move_left)
        
        for fun_scroll in fun_scrolls:
            e = scroll_to_find(self, 
                           xpath=self.xpath_titleview, 
                           text=self.NAME, 
                           fun_scroll=lambda *x:fun_scroll(), 
                           fun_match=is_app_wanted if icon_match else is_element_wanted,
                           )
            if e is not None:
                return e
    
    def switch_app(self, icon_match=False):
        if not self.is_app_opened():
            self.switch_overview()
            e = self.scroll_find_app(icon_match)
            if e is not None:
                e.click()
            else:
                self.open_app()
                
    def is_close_center_horizontal(self, e):
        return numpy.isclose(bounds_to_center(e.bounds)[0],
                             self.sys_center[0],
                             atol=1,)
            
    
    def find_app(self, name):
        x = f'//*[@text="{name}"]'
        l = self.find_xpath_steady(x).all()
        # return l
        return l[0] if l else None
    
    def switch_app_steady_scroll(self, name, fun_scroll):
        e = self.find_app(name)
        while 1:
            if e is not None:
                print('found:', e)
                e.click()
                return True
            fun_scroll()
            e = self.find_app(name)
            if self.is_steady_not_changed():
                break
        return False
    
    def switch_app_steady(self, name):
        self.switch_overview()
        fun_scrolls = (self.scroll_center_move_right, )#self.scroll_center_move_left)
        
        for fun_scroll in fun_scrolls:
            if self.switch_app_steady_scroll(name, fun_scroll):
                return True
        return False
    
    def switch_app_steady_open_if_not_found(self, name, ):
        pass
            
    
    def choose_or_close(self, name):
        x = f'//*[@text="{name}"]'
        # e = self.find_xpath_safe(x).wait()
        e = wait_tobe_steady(self, x)
        if e is None:# or not self.is_close_center_horizontal(e):
            self.scroll_center_move_up()
        else:
            e.click()
            return True
        
    def switch_app_name(self, name, total=5):
        for i in range(total):
            self.switch_overview()
            print(f'find app:{name}:', f'{i+1}/{total}')
            if self.choose_or_close(name):
                return
            time.sleep(0.1)
        raise SwitchOverviewError
        
        