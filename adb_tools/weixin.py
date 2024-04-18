'''
Created on 2024年4月17日

@author: lenovo
'''
from adb_tools.helper_adb import BaseAdb




class WxAdb(BaseAdb):
    # app_name = 'com.tencent.mm'
    # activity = '.ui.LauncherUI'
    INFO = {'package': 'com.tencent.mm',
     'activity': '.ui.LauncherUI'}
    NAME = '微信'



class Wx2Adb(WxAdb):
    pass
