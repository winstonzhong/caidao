'''
Created on 2023 Nov 4

@author: Winston
'''

import logging

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.wait import WebDriverWait


LOGGER.setLevel(logging.CRITICAL)

r"""
"chrome.exe" --remote-debugging-port=9222 --user-data-dir="d:\cache\google-chrome\default"
"""


USER_DATA_DIR = r"d:\cache\google-chrome\default"

DRIVER_PATH = r'D:\迅雷下载\chromedriver-win64\chromedriver-win64\chromedriver.exe'

def get_driver_service(executable_path, headless=False, host='127.0.0.1', port=9222):
    chrome_options = Options()

    if headless:
        chrome_options.add_argument('--headless')

    chrome_options.add_argument("--log-level=3");

    # chrome_options.add_argument(
    #     "user-data-dir=%s" % USER_DATA_DIR)

    # chrome_options.add_argument("--incognito")  # 无痕模式
    caps = {
        # 'browserName': 'chrome',
        # 'version': '',
        # 'platform': 'ANY',
        'goog:loggingPrefs': {'performance': 'ALL'},  # 记录性能日志
    }

    chrome_options.add_argument('no-sandbox')
    chrome_options.add_argument('disable-dev-shm-usage')
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-plugins-discovery")
    # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_argument('----ignore-certificate-errors-spki-list')

    chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    # 设置 set_capability  desired_capabil 在4版本中取消了 替代的是 set_capability
    # option.set_capability("goog:loggingPrefs", {'performance': 'ALL'})

    # driver = Chrome(desired_capabilities=caps,
    #                 options=chrome_options, executable_path=DRIVER_PATH)

    # 不显示图片
    # prefs = {
    #     'profile.default_content_setting_values': {
    #         'images': 2,
    #     }
    # }
    # chrome_options.add_experimental_option('prefs', prefs)


    chrome_options.add_experimental_option("debuggerAddress", f"{host}:{port}")
    driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)
    driver.implicitly_wait(30)
    return driver

def get_driver_new_service(headless=False, port=9222):
    option = webdriver.ChromeOptions()
    if headless:
        option.add_argument('headless')
    option.add_argument("--log-level=3");
    option.add_argument("user-data-dir=%s" % USER_DATA_DIR)
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
    # 设置 set_capability  desired_capabil 在4版本中取消了 替代的是 set_capability
    option.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
    # caps = DesiredCapabilities.CHROME
    # caps['goog:loggingPrefs'] = {'performance': 'ALL'}

    service = Service(port=port)
    driver = webdriver.Chrome(options=option, service=service)
    driver.implicitly_wait(5)
    return driver

def get_driver_new(headless=False):
    option = webdriver.ChromeOptions()
    if headless:
        option.add_argument('headless')
    option.add_argument("--log-level=3");
    option.add_argument("user-data-dir=%s" % USER_DATA_DIR)
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
    # 设置 set_capability  desired_capabil 在4版本中取消了 替代的是 set_capability
    option.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
    # caps = DesiredCapabilities.CHROME
    # caps['goog:loggingPrefs'] = {'performance': 'ALL'}

    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(options=option, service=service)
    # 设置自动下载文件的设置
    # driver = webdriver.Chrome(options=option)
    # driver.get('https://www.baidu.com')
    driver.implicitly_wait(5)
    return driver


class BaseDriver(object):
    def __init__(self, headless=False, port=9222):
        self.headless = headless
        self.port = port
        self.implicitly_wait = 5
        self.driver = self.get_chrome_service_driver()
    
    
    def get_chrome_service_driver(self):
        option = webdriver.ChromeOptions()
        if self.headless:
            option.add_argument('headless')
        option.add_argument("--log-level=3");
        option.add_argument("user-data-dir=%s" % USER_DATA_DIR)
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
    
        service = Service(port=self.port)
        driver = webdriver.Chrome(options=option, service=service)
        driver.implicitly_wait(self.implicitly_wait)
        return driver
    
    def get_driver(self):
        if self.driver is None:
            self.driver = self.get_chrome_service_driver()
        return self.driver

    def find_element_css(self, selector, wait_seconds=10):
        return WebDriverWait(self.driver, wait_seconds).until(lambda x: x.find_element(By.CSS_SELECTOR, selector))

    def scroll_down(self, scroll_px=500):
        print('scroll down')
        self.driver.execute_script(f'window.scrollBy(0,{scroll_px})')

    def hover(self, s):
        e = self.find_element_css(s)
        ActionChains(self.driver).move_to_element(e).perform()
        return e

        
    def quit(self):
        self.driver.quit()

class SrbDriver(BaseDriver):
    def find_reply_root_user(self, user_id):
        try:
            s = 'div.list-container div.avatar a[href="/user/profile/%s"]' % user_id
            return self.find_element_css(s,wait_seconds=3)
        except TimeoutException:
            pass
    
    def click_reply_icon(self, e):
        e = e.find_element(By.XPATH, './/..//..').find_element(By.CSS_SELECTOR, 'div.reply.icon-container')
        e.click()
        
    def input_comments(self, txt):
        self.find_element_css('input.comment-input').send_keys(txt)
        
    def submit_comments(self):
        self.find_element_css('button.submit').click()
    
    def move_to_last_comments(self):
        e = self.find_element_css('div.parent-comment:nth-last-child(1)')
        ActionChains(self.driver).move_to_element(e).perform()
        
    def is_last_comments(self):
        try:
            self.find_element_css('div.end-container', wait_seconds=3)
            return True
        except TimeoutException:
            pass
    
    def reply_text(self, user_id, txt):
        while 1:
            e = self.find_reply_root_user(user_id)
            if e is not None:
                self.click_reply_icon(e)
                self.input_comments(txt)
                self.submit_comments()
                return True
            if self.is_last_comments():
                break
            self.move_to_last_comments()
            
            
        
        
        
        
        
    
        
        
        
    