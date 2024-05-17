'''
Created on 2024年4月17日

@author: lenovo
'''
import time

from adb_tools.common.exceptions import NoFriendError, NoGroupError
from adb_tools.helper_adb import BaseAdb, scroll_to_find, wait_tobe_steady



class WxAdb(BaseAdb):
    APP_INFO = {'package': 'com.tencent.mm', 'activity': '.ui.LauncherUI'}
    NAME = '微信'

    def search(self, text):
        e = self.find_xpath_safe('//android.widget.ImageView[@resource-id="com.tencent.mm:id/meb"]').wait()
        e.click()
        self.ua2.send_keys(text, True)
        self.find_xpath_safe(f'//android.widget.TextView[@text="{text}"]').wait().click()

    def enter_contact_page(self):
        """进入通讯录"""
        x_tab = '//android.widget.TextView[@text="通讯录"]'
        self.find_xpath_safe(x_tab).wait().click()

    def open_chat_view_with_friend(self, wx_id):
        """打开与指定好友的聊天窗口"""
        self.enter_contact_page()

        x_search = '//android.widget.RelativeLayout[@content-desc="搜索"]'
        self.click_untill_gone(x_search)

        x_input = '//android.widget.EditText[@text="搜索"]'
        e_input = self.find_xpath_safe(x_input)
        e_input.wait().click()
        e_input.set_text(wx_id)

        x_res1 = f'//android.widget.TextView[@text="微信号: {wx_id}"]'
        x_res2 = f'//android.widget.TextView[@text="最常使用"]/../../following-sibling::android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TableLayout/android.widget.TableRow/android.widget.TextView[re:match(@text, ".*||{wx_id}")]'
        x_res3 = f'//android.widget.TextView[@text="联系人"]/../../following-sibling::android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TableLayout/android.widget.TableRow/android.widget.TextView[re:match(@text, ".*||{wx_id}")]'
        x_res = f'{x_res1}|{x_res2}|{x_res3}'
        try:
            self.click_untill_gone(x_res)
        except ValueError:
            raise NoFriendError(wx_id)


    def open_chat_view_with_group(self, group_name):
        """打开与指定好友的聊天窗口"""

        x_search = '//android.widget.RelativeLayout[@content-desc="搜索"]'
        self.click_untill_gone(x_search)

        x_input = '//android.widget.EditText[@text="搜索"]'
        e_input = self.find_xpath_safe(x_input)
        e_input.wait().click()
        e_input.set_text(group_name)
        x_res2 = f'//android.widget.TextView[@text="最常使用"]/../../following-sibling::android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TableLayout/android.widget.TableRow/android.widget.TextView[@text="{group_name}"]'
        x_res3 = f'//android.widget.TextView[@text="群聊"]/../../following-sibling::android.widget.RelativeLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TableLayout/android.widget.TableRow/android.widget.TextView[@text="{group_name}"]'
        x_res = f'{x_res2}|{x_res3}'
        try:
            self.click_untill_gone(x_res)
        except ValueError:
            raise NoGroupError(group_name)


    def is_in_chat(self):
        return {k: v for k, v in self.ua2.current_app().items() if k != 'pid'} == self.APP_INFO

    def is_in_list(self):
        # resource-id="com.tencent.mm:id/plus_icon" class="android.widget.ImageView"
        # xpath = '//android.widget.ImageView[@resource-id="com.tencent.mm:id/plus_icon"]'
        # text="微信" resource-id="android:id/text1" class="android.widget.TextView" package="com.tencent.mm"
        xpath1 = '//android.widget.TextView[starts-with(@text, "微信")]'
        xpath2 = '//android.widget.TextView[starts-with(@text, "发现")]'
        # xpath2 = '//android.widget.ImageView[@content-desc="返回"]'
        return self.is_in_chat() and self.find_xpath_safe(xpath1).exists and self.find_xpath_safe(xpath2).exists

    def go_back_to_list(self):
        while 1:
            if self.is_in_list():
                break
            self.go_back()
            time.sleep(2)

    def send_message(self, text):
        # class="android.widget.EditText"
        # e = self.find_xpath_safe('//android.widget.EditText').wait()
        # e.click()
        # e._parent.send_text(text)
        # # text="发送" resource-id="com.tencent.mm:id/bql" class="android.widget.Button"
        # adb.find_xpath_safe('//android.widget.Button[@text="发送"]').wait().click()
        # # adb.go_back()

        x_input = '//android.widget.EditText'
        e_input = self.find_xpath_safe(x_input)
        e_input.wait()
        e_input.set_text(text)

        x_send = '//android.widget.Button[@text="发送"]'
        e_send = self.find_xpath_safe(x_send)
        e_send.wait()
        e_send.click()


    def send_file_mate10(self, fpath, suffix='pdf', file_type=None):
        """适配华为mate10; 文件选择调用系统插件, 需要做机型适配

        file_type: 图片, 音频, 视频, 文档
        """
        self.push_file_to_download(fpath,
                                   clean_temp=True,
                                   use_timestamp=False
                                  )
        # resource-id="com.tencent.mm:id/bjz" class="android.widget.ImageButton"
        self.find_xpath_safe('//android.widget.ImageButton[@resource-id="com.tencent.mm:id/bjz"]').wait().click()
        # xpath = 'resource-id="com.tencent.mm:id/a12" class="android.widget.TextView"'
        xpath = '//android.widget.TextView[@resource-id="com.tencent.mm:id/a12"]'
        # list(get_all(adb, xpath, fun_scroll=scroll_to_left))
        scroll_to_find(self, xpath, text='文件').click()
        # text="手机文件" resource-id="com.tencent.mm:id/nuw" class="android.widget.TextView"
        self.find_xpath_safe('//android.widget.TextView[@text="手机文件"]').wait().click()
        # text="选取" resource-id="com.tencent.mm:id/hr0" class="android.widget.Button"
        self.find_xpath_safe('//android.widget.Button[@text="选取"]').wait().click()

        # text="文档" resource-id="" class="com.google.android.material.chip.Chip"
        if file_type:
            e = self.find_xpath_safe(f'//com.google.android.material.chip.Chip[@text="{file_type}"]').wait()
            if e.attrib.get('checked') == 'false':
                e.click()
                e = wait_tobe_steady(self, x=f'//com.google.android.material.chip.Chip[@text="{file_type}"]')
                assert e.attrib.get('checked') == 'true'

        # resource-id="com.android.documentsui:id/date" class="android.widget.TextView"
        # wait_tobe_steady(adb, x='//android.widget.TextView[@resource-id="com.android.documentsui:id/date"]').click()

        # text="1708849818.4671543.pdf" resource-id="android:id/title" class="android.widget.TextView"
        xpath = f'//android.widget.TextView[re:match(@text, ".*\.{suffix}")][@resource-id="android:id/title"]'
        self.find_xpath_safe(xpath).wait()
        wait_tobe_steady(self, xpath).click()

        # adb.find_xpath_safe('//android.widget.TextView[@resource-id="com.android.documentsui:id/date"]').wait().click()
        # text="发送" resource-id="com.tencent.mm:id/hr2" class="android.widget.Button"
        self.find_xpath_safe('//android.widget.Button[@text="发送"]').wait().click()

    def is_in_session(self):
        """判断是否在聊天窗口"""
        x1 = '//android.widget.ImageButton[@content-desc="切换到按住说话"]'
        x2 = '//android.widget.ImageButton[@content-desc="切换到键盘"]'
        x = f'{x1}|{x2}'
        return self.find_xpath_safe(x).exists

class Wx2Adb(WxAdb):
    pass
