'''
Created on 2024年4月17日

@author: lenovo
'''
from adb_tools.helper_adb import BaseAdb


class WxAdb(BaseAdb):
    APP_INFO = {'package': 'com.tencent.mm', 'activity': '.ui.LauncherUI'}
    NAME = '微信'


    def search(self, text):
        e = self.find_xpath_safe('//android.widget.ImageView[@resource-id="com.tencent.mm:id/meb"]').wait()
        e.click()
        self.ua2.send_keys(text, True)
        self.find_xpath_safe(f'//android.widget.TextView[@text="{text}"]').wait().click()
        
    
                
    
class Wx2Adb(WxAdb):
    pass
