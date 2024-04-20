'''
Created on 2023年12月21日

@author: lenovo
'''
import os

from PIL import Image
import cv2
from uiautomator2.xpath import XPath


class NoTemplatePopupException(Exception):
    pass


class DummyWatcher(object):
    def run(self, xml_content):
        return False

class DummyDevice(object):
    def __init__(self, fpath):
        # with open(fpath, 'r', encoding='utf8') as fp:
        #     self.source = fp.read()
        # self.settings = {'xpath_debug':False}
        # self.watcher = DummyWatcher()
        # self.wait_timeout = 0.01
        with open(fpath, 'r', encoding='utf8') as fp:
            self.init(fp.read())
        
    
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
        return True
    
class SnapShotDevice(DummyDevice):
    def __init__(self, adb):
        self.adb = adb
        self.init(adb.ua2.dump_hierarchy(), 0)
    
    def find_xpath_safe(self, x):
        return find_by_xpath(self, x)    
    
class TaskSnapShotDevice(SnapShotDevice):
    def __init__(self, adb, task, base_dir):
        adb.switch_app()
        SnapShotDevice.__init__(self, adb)
        task.fpath_xml = os.path.join(base_dir , f'{task.id}.xml')
        with open(task.fpath_xml.path, 'wb') as fp:
            fp.write(self.source.replace("'\\", '').encode('utf8'))
        task.fpath_screenshot = os.path.join(base_dir , f'{task.id}.jpeg')
        # cv2.imwrite(task.fpath_screenshot, adb.ua2.screenshot(format='opencv'))
        cv2.imwrite(task.fpath_screenshot.path, adb.screen_shot())
        task.save()

class TaskDumpedDevice(SnapShotDevice):
    def __init__(self, task):
        with open(task.fpath_xml.path, 'rb') as fp:
            self.init(fp.read().decode('utf8'), 0)
        self.img = Image.open(task.fpath_screenshot.path)
    
    def screenshot(self):
        return self.img
    
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
