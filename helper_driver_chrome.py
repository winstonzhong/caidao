'''
Created on 2023 Nov 4

@author: Winston
'''

import json
import logging
import subprocess
import time

from pyquery.pyquery import PyQuery
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.wait import WebDriverWait


LOGGER.setLevel(logging.CRITICAL)

# r"""
# "chrome.exe" --remote-debugging-port=9222 --user-data-dir="d:\cache\google-chrome\default"
# """
# USER_DATA_DIR = r"d:\cache\google-chrome\default"

# DRIVER_PATH = r'D:\迅雷下载\chromedriver-win64\chromedriver-win64\chromedriver.exe'


class NavigateFailedError(Exception):
    pass

class BaseDriver(object):
    def __init__(self, 
                 headless=False, 
                 port=9222,
                 user_dir=r"d:\cache\google-chrome\default",
                 driver_path=r'F:\chromedriver-win64\chromedriver-win64\chromedriver.exe',
                 ):
        self.user_dir = user_dir
        self.driver_path = driver_path
        self.headless = headless
        self.port = port
        self.implicitly_wait = 5
        self.logs = None
        self.response = {}
    
    def start(self):
        self.open_browser()
        time.sleep(3)
        self.driver = self.get_driver_remote()
        self.prepare()
        
    
    @property
    def browser_start_cmd(self):
        return '''chrome.exe --enable-logging --remote-debugging-port={self.port} --user-data-dir="{self.user_dir}"'''.format(self=self)
    
    
    def open_browser(self):
        print('browser_start_cmd', self.browser_start_cmd)
        self.browser = subprocess.Popen(self.browser_start_cmd)

        
    
    def prepare(self):
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                           Object.defineProperty(navigator, 'webdriver', {
                             get: () => undefined
                           })
                         """
        })

    def get_request_pair_all(self, logs):
        for i in range(len(logs)-1, 0, -1):
            log = logs[i]
            logjson = json.loads(log["message"])["message"]
            if logjson['method'] == 'Network.responseReceived':
                params = logjson['params']
                requestUrl = params['response']['url']
                requestId = params['requestId']
                yield requestUrl, requestId
    
    def do_get_response_body(self, logs, url):
        for requestUrl, requestId in self.get_request_pair_all(logs):
            if requestUrl.startswith(url):
                return self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': requestId})
        return {}
    
    def wait_request_untill_finished_or_timeout(self, url, seconds_wait=10):
        old = time.time()
        while time.time() - old <= seconds_wait:
            self.logs = self.driver.get_log("performance")
            self.response = self.do_get_response_body(self.logs, url)
            if self.response is not None:
                return True
            time.sleep(1)
        return False
    
    @property
    def query(self):
        return PyQuery(self.response.get('body','')) 
        
    def get(self, url, seconds_wait=30):
        self.driver.get(url)
        return self.wait_request_untill_finished_or_timeout(url, seconds_wait)

    def get_safe(self, url):
        try:
            self.get(url)
        except Exception as e:
            print('error:', e)
        return False
    
    def get_driver_remote(self):
        options = Options()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
        options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})



        return webdriver.Chrome(options=options, executable_path=self.driver_path)
        
        
    
    # def get_chrome_service_driver(self):
    #     option = webdriver.ChromeOptions()
    #     if self.headless:
    #         option.add_argument('headless')
    #     option.add_argument("--log-level=3");
    #     option.add_argument("user-data-dir=%s" % USER_DATA_DIR)
    #     option.add_argument('no-sandbox')
    #     option.add_argument('disable-dev-shm-usage')
    #     option.add_argument("--disable-blink-features=AutomationControlled")
    #     option.add_argument("--disable-extensions")
    #     option.add_argument("--disable-infobars")
    #     option.add_argument("--disable-popup-blocking")
    #     option.add_argument("--disable-default-apps")
    #     option.add_argument("--disable-plugins-discovery")
    #     option.add_experimental_option('excludeSwitches', ['enable-automation'])
    #     option.add_argument('----ignore-certificate-errors-spki-list')
    #
    #     option.add_argument('--ignore-ssl-errors')
    #     option.add_experimental_option("detach", True)
    #     option.add_argument("--disable-extensions")
    #     option.add_argument("--disable-gpu")
    #     option.add_argument("--disable-features=VizDisplayCompositor")
    #     option.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
    #
    #     service = Service(port=self.port)
    #     driver = webdriver.Chrome(options=option, service=service)
    #     # driver.implicitly_wait(self.implicitly_wait)
    #     return driver
    
    # def get_driver(self):
    #     if self.driver is None:
    #         self.driver = self.get_chrome_service_driver()
    #     return self.driver

    def find(self, by, selector, method, wait_seconds=10):
        return WebDriverWait(self.driver, 
                             wait_seconds
                             ).until(lambda x: getattr(x, method)(by, selector))


    def find_element_css(self, selector, wait_seconds=10):
        # return WebDriverWait(self.driver, wait_seconds).until(lambda x: x.find_element(By.CSS_SELECTOR, selector))
        return self.find(By.CSS_SELECTOR, selector, method='find_element', wait_seconds=wait_seconds)

    def find_element_xpath(self, selector, wait_seconds=10):
        return self.find(By.XPATH, selector, method='find_element', wait_seconds=wait_seconds)


    def find_elements_css(self, selector, wait_seconds=10):
        return self.find(By.CSS_SELECTOR, selector, method='find_elements', wait_seconds=wait_seconds)

    def find_elements_xpath(self, selector, wait_seconds=10):
        return self.find(By.XPATH, selector, method='find_elements', wait_seconds=wait_seconds)


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
    def __init__(self, uid='65313910000000000200c253',
                 headless=False,
                 port=9222,
                 user_dir=r"c:\cache\google-chrome\default",
                 driver_path=None,
                 ):
        BaseDriver.__init__(self, headless, port, user_dir=user_dir, driver_path=driver_path)
        self.uid = uid
        
    def find_reply_root_user(self, user_id):
        try:
            s = 'div.list-container div.avatar a[href="/user/profile/%s"]' % user_id
            e = self.find_element_css(s)
            return e.find_element(By.XPATH, './/..//..')
        except TimeoutException:
            pass


    def get_reply_container_root(self, e_reply_root_user):
        return e_reply_root_user.find_element(By.XPATH, './/..//..')
    
    
    def click_expand_if_has_more_replies(self, e_reply_container_root):
        try:
            e = e_reply_container_root.find_element(By.CSS_SELECTOR, 'div.reply-container > div:nth-last-child(1)')
            if e.get_attribute('class') == 'show-more':
                e.click()
                time.sleep(1)
                return True
        except:
            pass
        return False
        
    def has_reply_of_user(self, e_reply_container_root, uid):
        l = list(filter(lambda x:x.get_attribute('href').endswith(uid),e_reply_container_root.find_elements(By.CSS_SELECTOR, 'div.reply-container div.avatar a')))
        return len(l) > 0
    
    def query_reply_of_user_and_expand_more_untill_end(self, e_reply_root_user, uid):
        r = self.get_reply_container_root(e_reply_root_user)
        while 1:
            if self.has_reply_of_user(r, uid):
                return True
            if not self.click_expand_if_has_more_replies(r):
                break
        return False
    
    def click_reply_icon(self, e):
        # e = e.find_element(By.XPATH, './/..//..').find_element(By.CSS_SELECTOR, 'div.reply.icon-container')
        e = e.find_element(By.CSS_SELECTOR, 'div.reply.icon-container')
        # e = e.find_element(By.XPATH, '//div[@class="reply icon-container"]')
        e.click()
        
    def input_comments(self, txt):
        self.find_element_css('input.comment-input').send_keys(txt)
        
    def submit_comments(self):
        e = self.find_element_css('button.submit')
        time.sleep(1)
        e.click()
    
    def move_to_last_comments(self):
        e = self.find_element_css('div.parent-comment:nth-last-child(1)')
        ActionChains(self.driver).move_to_element(e).perform()
        
    def is_last_comments(self):
        try:
            self.find_element_css('div.end-container', wait_seconds=1)
            return True
        except (TimeoutException, WebDriverException):
            pass
    
    def reply_text(self, user_id, txt):
        while 1:
            e = self.find_reply_root_user(user_id)
            if e is not None:
                if not self.query_reply_of_user_and_expand_more_untill_end(e, self.uid):
                    self.click_reply_icon(e)
                    self.input_comments(txt)
                    self.submit_comments()
                    return True
                print('already replied!')
                return False
            if self.is_last_comments():
                break
            self.move_to_last_comments()
            
            
        
        
        
        
        
    
        
        
        
    
