'''
Created on 2024 Nov 10

@author: Winston
'''

import logging
import os

selenium_logger = logging.getLogger('selenium')
# 创建一个空的日志处理器，它不会处理和输出任何日志
null_handler = logging.NullHandler()
# 将空的日志处理器添加到selenium的logger中
selenium_logger.addHandler(null_handler)


from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

from selenium import webdriver
from selenium.webdriver.chrome.service import Service


from tool_env import OS_WIN


user_data_dir = 'd:/google-chrome/Default'

if not OS_WIN:
    DRIVER_PATH = "/big/download/bin/chromedriver"
else:
    DRIVER_PATH = r'D:\chrome_driver\chromedriver.exe'



user_data_dir = 'd:/cache/google-chrome/Default'
DRIVER_PATH = r'D:\soft\chromedriver\chromedriver.exe'

import selenium

assert selenium.__version__ == '4.12.0'

# D:\google-chrome\Default\Default\Preferences
# chrome version:130.0.6723.92
fpath_preferences = os.path.join(user_data_dir, 'Default/Preferences')
def replace_crash_report():
    with open(fpath_preferences, 'rb') as fp:
        content = fp.read().decode('utf8')
        
    content = content.replace('"exit_type":"Crashed"', '"exit_type":"None"')
    
    with open(fpath_preferences, 'wb') as fp:
        fp.write(content.encode('utf8'))
    


def get_driver(headless=True):
    chrome_options = Options()

    if headless:
        chrome_options.add_argument('--headless')

    chrome_options.add_argument(
        "user-data-dir=%s" % user_data_dir)

    # chrome_options.add_argument("--incognito")  # 无痕模式
    
    chrome_options.add_argument('log-level=3')
    
    caps = {
        # 'browserName': 'chrome',
        # 'version': '',
        # 'platform': 'ANY',
        'goog:loggingPrefs': {'performance': 'ALL'},   # 记录性能日志
    }

    driver = Chrome(desired_capabilities=caps,
                    options=chrome_options, executable_path=DRIVER_PATH)

    driver.implicitly_wait(30)
    return driver


def get_driver_new(headless=True, implicitly_wait_seconds=5):
    option = webdriver.ChromeOptions()
    if headless:
        option.add_argument('headless')
    option.add_argument("--log-level=3")
    option.add_argument("--start-maximized")
    option.add_argument("user-data-dir=%s" % user_data_dir)
    option.add_argument('no-sandbox')
    option.add_argument('disable-dev-shm-usage')
    option.add_argument("--disable-blink-features=AutomationControlled")
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-infobars")
    option.add_argument("--disable-popup-blocking")
    option.add_argument("--disable-default-apps")
    option.add_argument("--disable-plugins-discovery")
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    option.add_argument('----ignore-certificate-errors-spki-list')
    
    option.add_argument('--ignore-ssl-errors')
    option.add_experimental_option("detach", True)
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-gpu")
    option.add_argument("--disable-features=VizDisplayCompositor")
    option.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
    
    # option.add_experimental_option('excludeSwitches', ['enable-logging'])    
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(options=option, service=service)
    if implicitly_wait_seconds:
        driver.implicitly_wait(implicitly_wait_seconds)
    return driver

def get_driver_service(headless=True, 
                       implicitly_wait_seconds=5,
                       port=9222):
    option = webdriver.ChromeOptions()
    if headless:
        option.add_argument('headless')
    option.add_argument("--log-level=3")
    
    option.add_argument("--start-maximized")
    # option.add_argument('--incognito')
    
    option.add_argument("user-data-dir=%s" % user_data_dir)
    option.add_argument('no-sandbox')
    option.add_argument('disable-dev-shm-usage')
    option.add_argument("--disable-blink-features=AutomationControlled")
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-infobars")
    option.add_argument("--disable-popup-blocking")
    option.add_argument("--disable-default-apps")
    option.add_argument("--disable-plugins-discovery")
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    option.add_argument('----ignore-certificate-errors-spki-list')

    option.add_argument('--ignore-ssl-errors')
    option.add_experimental_option("detach", True)
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-gpu")
    option.add_argument("--disable-features=VizDisplayCompositor")
    option.set_capability("goog:loggingPrefs", {'performance': 'ALL'})


    service = Service(port=port)
    driver = webdriver.Chrome(options=option, service=service)
    
    if implicitly_wait_seconds:
        driver.implicitly_wait(implicitly_wait_seconds)
        
    return driver
    
