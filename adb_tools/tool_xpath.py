'''
Created on 2023年12月21日

@author: lenovo
'''
import os
import time

from PIL import Image
from cached_property import cached_property
import cv2
from uiautomator2.xpath import XPath

from helper_hash import get_hash
from tool_env import bounds_to_rect
from tool_img import get_template_points, show, pil2cv2, cv2pil


class NoTemplatePopupException(Exception):
    pass


class DummyWatcher(object):
    def run(self, xml_content):
        return False

class DummyDevice(object):
    def __init__(self, fpath=None, adb=None, xml=None):
        if xml is None:
            with open(fpath, 'r', encoding='utf8') as fp:
                xml = fp.read()
        self.init(xml)
        self.adb = adb
        
    
    def init(self, source, wait_timeout=0.01):
        self.source = source
        self.settings = {'xpath_debug':False}
        self.watcher = DummyWatcher()
        self.wait_timeout = wait_timeout
        
            
    def dump_hierarchy(self):
        return self.source
    
    def __getattr__(self, name):
        pass
    
    def click(self, *a, **k):
        return self.adb.ua2.click(*a, **k)
    
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
    def __init__(self, adb, old_key = None):
        self.adb = adb
        max_try = 6
        for i in range(max_try):
            xml_dumped = adb.ua2.dump_hierarchy()
            key = get_hash(xml_dumped)
            if old_key != key and i < max_try - 1:
                print(f'waiting xml tobe steady:...{i}')
                old_key = key
                time.sleep(0.1)
            else:
                self.key = key
                self.init(xml_dumped, 0)
                break
        
    
    def find_xpath_safe(self, x):
        return find_by_xpath(self, x)    


    def click(self, *a, **k):
        return self.adb.ua2.click(*a, **k)
    
class TaskSnapShotDevice(SnapShotDevice):
    def __init__(self, adb, task, base_dir):
        adb.switch_app()
        SnapShotDevice.__init__(self, adb)
        self.img = adb.screen_shot()
        
        task.key = task.get_task_key(self)
        task_key_pre = task.pre_same_job_key
        self.task = task
        # print([task.key, task_key_pre])
        
        self.changed = task.key is None or task_key_pre is None or task_key_pre != task.key
        
        if self.changed:
            task.fpath_screenshot = os.path.join(base_dir , f'{task.id}.png')
            self.img = adb.screen_shot()
            cv2.imwrite(task.fpath_screenshot.path, self.img)
            
            task.fpath_xml = os.path.join(base_dir , f'{task.id}.xml')
            with open(task.fpath_xml.path, 'wb') as fp:
                fp.write(self.source.replace("'\\", '').encode('utf8'))
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
        self.adb.clear_temp_dir(base_dir='/sdcard/Pictures/WeiXin/')
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
            return (l[0][0], l[0][1], l[0][0]+w, l[0][1] + h)
    
    def match_xml(self, tpl):
        xml = tpl.xml.decode('utf8')
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
    '''
    >>> find_by_xpath(DummyDevice('ut/xiaoshipin/page.xml'), '//*[re:match(@text, "开启悬浮窗")][@index="0"]').exists
    True
    >>> find_by_xpath(DummyDevice('ut/xiaoshipin/page.xml'), '//*[re:match(@text, "开启悬浮窗")][@index="0"]').click()
    '''
    return XPath(adb_device)(xpath)     

def wait_jianyin_template_search_input_click_ready(adb_device):
    '''
    >>> wait_jianyin_template_search_input_click_ready(DummyDevice('ut/xiaoshipin/page.xml'))
    >>> wait_jianyin_template_search_input_click_ready(DummyDevice('ut/jianyin/page_input_click_ready.xml')) is not None
    True
    '''
    return find_by_xpath(adb_device, '//com.lynx.component.svg.UISvg/following-sibling::com.bytedance.ies.xelement.input.LynxInputView').wait()

def wait_jianyin_template_search_completed(adb_device):
    '''
    >>> wait_jianyin_template_search_completed(DummyDevice('ut/xiaoshipin/page.xml'))
    >>> wait_jianyin_template_search_completed(DummyDevice('ut/jianyin/page_search_finished.xml')) is not None
    True
    '''
    return find_by_xpath(adb_device, '//*[@text="筛选"]').wait()

def wait_jianyin_search_button_ready(adb_device):
    '''
    >>> wait_jianyin_search_button_ready(DummyDevice('ut/xiaoshipin/page.xml'))
    >>> wait_jianyin_search_button_ready(DummyDevice('ut/jianyin/page_input_click_ready.xml'))
    >>> wait_jianyin_search_button_ready(DummyDevice('ut/jianyin/page_search_button_ready.xml')).attrib['bounds']
    '[184,302][821,404]'
    '''
    x = find_by_xpath(adb_device, '//com.lynx.tasm.behavior.ui.LynxFlattenUI[@text="搜索"]/preceding-sibling::*')
    if x.wait() is not None:
        return x.all()[-1] 

def wait_jianyin_open_template_directly_buttopn(adb_device, timeout=None):
    '''
    >>> wait_jianyin_open_template_directly_buttopn(DummyDevice('ut/xiaoshipin/page.xml')) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    NoTemplatePopupException:
    >>> wait_jianyin_open_template_directly_buttopn(DummyDevice('ut/jianyin/page_tpl_direct_open.xml')) is not None
    True
    '''
    e = find_by_xpath(adb_device, '//android.widget.Button[@text="打开看看"]').wait(timeout=timeout)
    if e is None:
        raise NoTemplatePopupException
    return e

def click_if_jianyin_open_template_giveup_history_button_exists(adb_device):
    '''
    >>> click_if_jianyin_open_template_giveup_history_button_exists(DummyDevice('ut/xiaoshipin/page.xml'))
    >>> click_if_jianyin_open_template_giveup_history_button_exists(DummyDevice('ut/jianyin/page_giveup.xml'))
    True
    '''
    l = find_by_xpath(adb_device, '//*[@text="放弃"][@resource-id="com.lemon.lv:id/tvCancelResume"]').all()
    if len(l):
        l[0].click()
        return True
    

if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))
