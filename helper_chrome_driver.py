"""
Created on 2024 Nov 10

@author: Winston
"""

import logging
import os


import base64
from io import BytesIO
import json
import re
import time
import selenium

from PIL import Image

from selenium.webdriver.common.by import By

from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

from selenium import webdriver
from selenium.webdriver.chrome.service import Service


from tool_env import OS_WIN

from selenium.webdriver.support.wait import WebDriverWait


selenium_logger = logging.getLogger("selenium")
# 创建一个空的日志处理器，它不会处理和输出任何日志
null_handler = logging.NullHandler()
# 将空的日志处理器添加到selenium的logger中
selenium_logger.addHandler(null_handler)


USER_DATA_DIR = "d:/google-chrome/Default"

if not OS_WIN:
    if os.path.lexists("/home/yka-003/"):
        DRIVER_PATH = "/home/yka-003/Downloads/chromedriver-linux64"
    else:
        DRIVER_PATH = "/big/download/bin/chromedriver"
else:
    DRIVER_PATH = r"D:\chrome_driver\chromedriver.exe"


# user_data_dir = 'd:/cache/google-chrome/Default'
# DRIVER_PATH = r'D:\soft\chromedriver\chromedriver.exe'


assert selenium.__version__ == "4.12.0"

# D:\google-chrome\Default\Default\Preferences
# chrome version:130.0.6723.92
fpath_preferences = os.path.join(USER_DATA_DIR, "Default/Preferences")


def replace_crash_report():
    with open(fpath_preferences, "rb") as fp:
        content = fp.read().decode("utf8")

    content = content.replace('"exit_type":"Crashed"', '"exit_type":"None"')

    with open(fpath_preferences, "wb") as fp:
        fp.write(content.encode("utf8"))


def get_driver(headless=True):
    chrome_options = Options()

    if headless:
        chrome_options.add_argument("--headless")

    chrome_options.add_argument("user-data-dir=%s" % USER_DATA_DIR)

    # chrome_options.add_argument("--incognito")  # 无痕模式

    chrome_options.add_argument("log-level=3")

    caps = {
        # 'browserName': 'chrome',
        # 'version': '',
        # 'platform': 'ANY',
        "goog:loggingPrefs": {"performance": "ALL"},  # 记录性能日志
    }

    driver = Chrome(
        desired_capabilities=caps, options=chrome_options, executable_path=DRIVER_PATH
    )

    driver.implicitly_wait(30)
    return driver


def get_driver_new(
    headless=True,
    implicitly_wait_seconds=5,
    driver_path=DRIVER_PATH,
    user_data_dir=USER_DATA_DIR,
):
    option = webdriver.ChromeOptions()
    if headless:
        option.add_argument("headless")
    option.add_argument("--log-level=3")
    option.add_argument("--start-maximized")
    option.add_argument("user-data-dir=%s" % user_data_dir)
    option.add_argument("no-sandbox")
    option.add_argument("disable-dev-shm-usage")
    option.add_argument("--disable-blink-features=AutomationControlled")
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-infobars")
    option.add_argument("--disable-popup-blocking")
    option.add_argument("--disable-default-apps")
    option.add_argument("--disable-plugins-discovery")
    option.add_experimental_option("excludeSwitches", ["enable-automation"])
    option.add_argument("----ignore-certificate-errors-spki-list")

    option.add_argument("--ignore-ssl-errors")
    option.add_experimental_option("detach", True)
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-gpu")
    option.add_argument("--disable-features=VizDisplayCompositor")
    option.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    # option.add_experimental_option('excludeSwitches', ['enable-logging'])
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(options=option, service=service)
    if implicitly_wait_seconds:
        driver.implicitly_wait(implicitly_wait_seconds)
    return driver


def get_driver_service(
    headless=True, implicitly_wait_seconds=5, port=9222, user_data_dir=USER_DATA_DIR
):
    option = webdriver.ChromeOptions()
    if headless:
        option.add_argument("headless")
    option.add_argument("--log-level=3")

    option.add_argument("--start-maximized")
    # option.add_argument('--incognito')

    option.add_argument("user-data-dir=%s" % user_data_dir)
    option.add_argument("no-sandbox")
    option.add_argument("disable-dev-shm-usage")
    option.add_argument("--disable-blink-features=AutomationControlled")
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-infobars")
    option.add_argument("--disable-popup-blocking")
    option.add_argument("--disable-default-apps")
    option.add_argument("--disable-plugins-discovery")
    option.add_experimental_option("excludeSwitches", ["enable-automation"])
    option.add_argument("----ignore-certificate-errors-spki-list")

    option.add_argument("--ignore-ssl-errors")
    option.add_experimental_option("detach", True)
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-gpu")
    option.add_argument("--disable-features=VizDisplayCompositor")
    option.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    service = Service(port=port)
    driver = webdriver.Chrome(options=option, service=service)

    if implicitly_wait_seconds:
        driver.implicitly_wait(implicitly_wait_seconds)

    return driver


class 基本爬虫(object):
    home_page = "https://www.toutiao.com"
    单例 = None
    default_driver_path = None
    default_user_data_dir = None

    def __init__(
        self,
        headless=False,
        driver=None,
        logs=None,
        implicitly_wait_seconds=0,
        driver_path=None,
        user_data_dir=None,
    ):
        # self.driver_path = driver_path or CONFIGS.get("driver_path")
        # self.user_data_dir = user_data_dir or CONFIGS.get("user_data_dir")

        self.driver_path = driver_path or self.default_driver_path
        self.user_data_dir = user_data_dir or self.default_user_data_dir

        self.headless = headless
        self.implicitly_wait_seconds = implicitly_wait_seconds

        self._driver = driver if driver is not None else self.get_driver()

        self._logs = logs

        self.网址变更时间 = 0
        self.go_homepage()

    @classmethod
    def base64_to_image(cls, base64_str):
        base64_data = re.sub("^data:image/.+;base64,", "", base64_str)
        byte_data = base64.b64decode(base64_data)
        image_data = BytesIO(byte_data)
        img = Image.open(image_data)
        return img

    @classmethod
    def 得到爬虫单例(cls):
        if cls.单例 is None:
            cls.单例 = cls()
        return cls.单例

    @classmethod
    def 清除单例(cls):
        if cls.单例 is not None:
            单例 = cls.得到爬虫单例()
            单例.quit()
            cls.单例 = None

    @classmethod
    def copy_driver(cls, pa):
        return cls(driver=pa.driver)

    def 是否停留在主页(self):
        url = self.driver.current_url
        return url and url.startswith(self.home_page)

    def 是否停留在分类榜单页面(self):
        url = self.driver.current_url
        return url and url.startswith(self.分类榜单页面)

    def 加载变化时间(self):
        return time.time() - self.网址变更时间

    def go_homepage(self):
        if not self.是否停留在主页():
            self.go(self.home_page)
        elif self.加载变化时间() > 5:
            self.driver.refresh()
        else:
            print("5秒内已完成打开主页")
            return
        print("========完成打开主页！========")

    def quit(self):
        self.driver.quit()

    @property
    def driver(self):
        return self._driver

    @driver.setter
    def driver(self, value):
        self._driver = value

    def get_driver(self):
        print("self.driver_path", self.driver_path)
        print("self.user_data_dir", self.user_data_dir)
        return get_driver_new(
            self.headless,
            self.implicitly_wait_seconds,
            driver_path=self.driver_path,
            user_data_dir=self.user_data_dir,
        )

    def go(self, url):
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                  """
            },
        )
        self.driver.get(url)
        WebDriverWait(self.driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        self.网址变更时间 = time.time()

    @property
    def logs(self):
        if self._logs is None:
            self._logs = self.driver.get_log("performance")
        return self._logs

    @logs.setter
    def logs(self, value):
        self._logs = value

    def 刷新日志(self):
        self.logs = self.driver.get_log("performance")

    def 得到所有网络请求的url以及请求id(self, logs):
        for i in range(len(logs) - 1, -1, -1):
            log = logs[i]
            logjson = json.loads(log["message"])["message"]
            if logjson["method"] == "Network.responseReceived":
                params = logjson["params"]
                try:
                    requestUrl = params["response"]["url"]
                    requestId = params["requestId"]
                    yield requestUrl, requestId
                except Exception as e:
                    print(e)
                    pass

    def 搜索请求(self, url):
        the_list = self.得到所有网络请求的url以及请求id(self.logs)
        the_list = filter(lambda x: x[0].startswith(url), the_list)
        return list(the_list)

    def get_content(self, request_id):
        try:
            response_body = self.driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id}
            )
            return response_body["body"]
        except Exception as e:
            print(e)

    def get_json(self, request_id):
        try:
            content = self.get_content(request_id)
            if content is not None:
                return json.loads(content)
        except Exception as e:
            print(e)

    def get_image(self, request_id):
        try:
            return self.base64_to_image(self.get_content(request_id))
        except Exception as e:
            print(e)

    def 得到所有json(self, url_starts_with):
        for t in self.搜索请求(url_starts_with):
            j = self.get_json(t[1])
            if j is not None:
                yield j

    def 移动到元素(self, e):
        ActionChains(self.driver).move_to_element(e).perform()

    def 得到最大页面高度(self):
        return self.driver.execute_script("return document.body.scrollHeight")

    def 滚动至浏览器底部(self):
        max_height = self.得到最大页面高度()
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        return self.得到最大页面高度() - max_height

    def find(self, by, selector, method, wait_seconds=10):
        return WebDriverWait(self.driver, wait_seconds).until(
            lambda x: getattr(x, method)(by, selector)
        )

    def find_element_css(self, selector, wait_seconds=10):
        # return WebDriverWait(self.driver, wait_seconds).until(lambda x: x.find_element(By.CSS_SELECTOR, selector))
        return self.find(
            By.CSS_SELECTOR, selector, method="find_element", wait_seconds=wait_seconds
        )

    def find_element_xpath(self, selector, wait_seconds=10):
        return self.find(
            By.XPATH, selector, method="find_element", wait_seconds=wait_seconds
        )

    def find_elements_css(self, selector, wait_seconds=10):
        return self.find(
            By.CSS_SELECTOR, selector, method="find_elements", wait_seconds=wait_seconds
        )

    def find_elements_xpath(self, selector, wait_seconds=10):
        return self.find(
            By.XPATH, selector, method="find_elements", wait_seconds=wait_seconds
        )

    def scroll_down(self, scroll_px=500):
        print("scroll down")
        self.driver.execute_script(f"window.scrollBy(0,{scroll_px})")

    def hover(self, s):
        e = self.find_element_css(s)
        ActionChains(self.driver).move_to_element(e).perform()
        return e

    def 切换回爬虫(self):
        window_handles = self.driver.window_handles
        if self.driver.current_window_handle != window_handles[0]:
            self.driver.switch_to.window(window_handles[0])
