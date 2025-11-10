import random
import time
from typing import Dict, Optional, Any
from curl_cffi import requests  # 需安装：pip install curl-cffi
from faker import Faker  # 需安装：pip install faker

# 初始化随机数据生成器
fake = Faker()

# 模拟不同浏览器的 User-Agent 及对应请求头（关键：头部字段需与浏览器匹配）
BROWSER_HEADERS = {
    "chrome": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    },
    "firefox": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    },
    "safari": {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
    }
}

# 代理池示例（实际使用需维护有效代理）
PROXY_POOL = [
    # "http://username:password@ip:port",
    # "https://username:password@ip:port",
]


def get_random_browser_headers() -> Dict[str, str]:
    """随机选择浏览器及其对应的请求头"""
    browser = random.choice(list(BROWSER_HEADERS.keys()))
    headers = BROWSER_HEADERS[browser].copy()
    # 动态生成 Accept-Language（模拟不同地区用户）
    headers["Accept-Language"] = fake.language_code() + ";q=0.9," + fake.language_code() + ";q=0.8"
    return headers


def get_random_proxy() -> Optional[str]:
    """从代理池随机选择一个代理（无代理则返回 None）"""
    if not PROXY_POOL:
        return None
    return random.choice(PROXY_POOL)


def simulate_human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """模拟人类操作的随机延迟（避免高频请求）"""
    time.sleep(random.uniform(min_seconds, max_seconds))


def ordered_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """按浏览器参数顺序排序（部分网站检查参数顺序）"""
    # 示例：模拟 Chrome 浏览器常见参数排序（可根据目标网站调整）
    if not params:
        return {}
    sorted_keys = sorted(params.keys())
    return {k: params[k] for k in sorted_keys}


def browser_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    referer: Optional[str] = None,
    use_proxy: bool = False,
    session: Optional[requests.Session] = None,
    simulate_delay: bool = True
) -> requests.Response:
    """
    模拟浏览器 GET 请求的函数

    参数:
        url: 目标 URL
        params: 请求参数（字典）
        referer: Referer 头部（模拟从某个页面跳转）
        use_proxy: 是否使用代理
        session: 会话对象（复用可保持 Cookie）
        simulate_delay: 是否模拟请求前的人类延迟

    返回:
        请求响应对象
    """
    # 模拟人类操作延迟
    if simulate_delay:
        simulate_human_delay()

    # 初始化会话（复用会话保持 Cookie）
    if not session:
        session = requests.Session()

    # 随机浏览器头
    headers = get_random_browser_headers()

    # 动态设置 Referer（重要：模拟真实跳转来源）
    if referer:
        headers["Referer"] = referer
    else:
        # 若无指定，自动生成根域名作为 Referer（如 https://example.com -> https://example.com）
        parsed_url = requests.utils.urlparse(url)
        headers["Referer"] = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # 处理请求参数（排序模拟浏览器行为）
    ordered_params_dict = ordered_params(params) if params else None

    # 随机代理
    proxies = None
    if use_proxy:
        proxy = get_random_proxy()
        if proxy:
            proxies = {"http": proxy, "https": proxy}

    # 发送请求（关键：使用 curl_cffi 模拟浏览器 TLS 指纹）
    try:
        response = session.get(
            url,
            params=ordered_params_dict,
            headers=headers,
            proxies=proxies,
            verify=True,  # 验证 SSL 证书（模拟浏览器行为）
            impersonate=random.choice(["chrome110", "firefox102", "safari15"]),  # 模拟浏览器 TLS 指纹
            timeout=10  # 合理超时时间
        )
        # 随机小延迟（模拟浏览器接收响应后的处理时间）
        simulate_human_delay(0.1, 0.5)
        return response
    except Exception as e:
        print(f"请求失败: {e}")
        raise


# 示例用法
if __name__ == "__main__":
    # 初始化会话（保持 Cookie）
    session = requests.Session()

    # 第一次请求（模拟从首页进入）
    home_url = "https://example.com"
    home_response = browser_get(home_url, session=session)
    print(f"首页状态码: {home_response.status_code}")

    # 第二次请求（模拟从首页跳转到详情页，带 Referer）
    detail_url = "https://example.com/detail"
    detail_params = {"id": 123, "page": 1}
    detail_response = browser_get(
        detail_url,
        params=detail_params,
        referer=home_url,  # 明确 Referer 为首页
        session=session,
        use_proxy=False  # 如需代理可设为 True
    )
    print(f"详情页状态码: {detail_response.status_code}")
    print(f"详情页内容: {detail_response.text[:500]}")  # 打印部分内容