"""
Created on 2024年11月11日

@author: lenovo
"""

import os
import time

from tool_date import today
from helper_net import rget
import random
from tool_env import OS_WIN
import json
import string
import requests
import threading
from tool_img import to_buffer

BASE_URL_56T = "https://file.j1.sale/api/file"


if os.path.lexists("/data/data/com.termux"):
    BASE_DIR_56T = "/data/data/com.termux/files/home/file"

elif os.path.lexists("v:/file"):
    BASE_DIR_56T = "v:/file"
elif os.path.lexists("c:/home_zwd"):
    BASE_DIR_56T = "d:/file"
elif os.path.lexists("d:/file"):
    BASE_DIR_56T = "d:/file"
    BASE_URL_56T = "https://127.0.0.1:8000/media"
elif os.path.lexists("c:/file"):
    BASE_DIR_56T = "c:/file"
elif not OS_WIN:
    BASE_DIR_56T = "/mnt/56T/file"
else:
    BASE_DIR_56T = "/data/data/com.termux/files/home/file"


# BASE_DIR_56T = "v:/file" if OS_WIN else "/mnt/56T/file"
def is_inner():
    return BASE_DIR_56T == "/mnt/56T/file" and os.path.lexists(BASE_DIR_56T)


def upload_file(content, token, fname, project_name="default", keep_fname=False):
    assert fname, "fname is empty!!!"
    if not keep_fname:
        service_url = BASE_URL_56T
        url = None
    else:
        service_url = "https://file.j1.sale/api/set"
        url = f"{BASE_URL_56T}/{project_name}/{fname}"

    form_data = {"file": (fname, content)}
    data = {
        "project": project_name,
        "token": token,
        "url": url,
    }
    print("service_url:", service_url)
    try:
        response = requests.post(service_url, data=data, files=form_data)

        # print(f"响应状态码: {response.status_code}")
        # print(f"响应头部: {response.headers}")

        # 尝试解析 JSON
        data = response.json()
        # data = requests.post(service_url, data=data, files=form_data).json()
        result_url = data["data"].get("url")
        return f"""https://file.j1.sale{result_url}""" if result_url else data
    except requests.exceptions.JSONDecodeError as e:
        # JSON 解析失败时，打印真实的返回内容
        print("=" * 50)
        print("JSON 解析失败！服务器真实返回内容：")
        print("=" * 50)
        print(response.text)  # 核心：输出原始响应文本
        print("=" * 50)
        # 可以选择返回原始内容，或者抛出异常，根据你的需求调整
        return {
            "error": "JSON 解析失败",
            "status_code": response.status_code,
            "raw_response": response.text,
        }
    except Exception as e:
        # 捕获其他可能的异常（如网络错误、KeyError 等）
        print(f"其他错误发生: {str(e)}")
        raise  # 也可以根据需求返回自定义错误信息


def upload_file_by_path(fpath, token, project_name="default", keep_fname=False):
    with open(fpath, "rb") as f:
        content = f.read()
    return upload_file(
        content,
        token,
        fname=os.path.basename(fpath),
        project_name=project_name,
        keep_fname=keep_fname,
    )


def generate_password(length=8):
    password_characters = string.ascii_letters + string.digits + "_"
    password = [
        random.choice(string.ascii_uppercase),  # 大写字母
        random.choice(string.ascii_lowercase),  # 小写字母
        random.choice(string.digits),  # 数字
        random.choice("_"),  # 下划线
    ]
    password += random.choices(password_characters, k=length - len(password))
    random.shuffle(password)
    return "".join(password)


def 当前路径(base_dir=None, sub_dir=None):
    base_dir = BASE_DIR_56T if base_dir is None else base_dir
    if sub_dir is not None:
        base_dir = os.path.join(base_dir, sub_dir)
    fpath = os.path.join(base_dir, today())
    if not os.path.lexists(fpath):
        os.makedirs(fpath, exist_ok=True)
    return fpath


def 得到后缀(fpath=""):
    """
    >>> 得到后缀('aaa')
    ''
    >>> 得到后缀('aaa.jpg')
    'jpg'
    >>> 得到后缀('ccc.aaa.jpg')
    'jpg'
    >>> 得到后缀('.amr')
    'amr'
    """
    l = fpath.rsplit(".", maxsplit=1)
    return "" if len(l) < 2 else l[-1]


def 得到一个固定文件路径(相对路径, base_dir=BASE_DIR_56T):
    """
    >>> 得到一个固定文件路径('aaa/bbb') == f'{BASE_DIR_56T}/aaa/bbb'
    True
    >>> 得到一个固定文件路径('/aaa/bbb') == f'{BASE_DIR_56T}/aaa/bbb'
    True
    """
    相对路径 = 相对路径.replace("\\", "/")
    相对路径 = 相对路径[1:] if 相对路径.startswith("/") else 相对路径
    return os.path.join(base_dir, 相对路径).replace("\\", "/")


def 得到一个不重复的文件名(fpath):
    time.sleep(0.01)
    后缀 = 得到后缀(fpath)
    后缀 = f".{后缀}" if 后缀 else ""
    return f"{time.time():.6f}{random.random():.4f}{后缀}"


def 得到一个不重复的文件路径(fpath="", sub_dir=None, base_dir=None):
    return os.path.join(
        当前路径(base_dir=base_dir, sub_dir=sub_dir), 得到一个不重复的文件名(fpath)
    )


def 路径到链接(fpath, base_dir=BASE_DIR_56T):
    """
    >>> 路径到链接(f'{BASE_DIR_56T}/test/x.jpg')
    'https://file.j1.sale/api/file/test/x.jpg'
    """
    if OS_WIN:
        fpath = fpath.lower()
    # print(fpath, base_dir)

    return fpath.replace("\\", "/").replace(base_dir.replace("\\", "/"), BASE_URL_56T)


def 存储文件(content, suffix=None, 返回路径=False, base_dir=BASE_DIR_56T, fpath=None):
    if fpath is None:
        assert suffix, "suffix is empty!!!"
        fpath = 得到一个不重复的文件路径(f".{suffix}")
    print("保存文件:", fpath)
    with open(fpath, "wb") as fp:
        fp.write(content)
    print("保存完毕===========================")
    return 路径到链接(fpath, base_dir=base_dir) if not 返回路径 else fpath


def 存储图片到文件(img, suffix, 返回路径=False, base_dir=BASE_DIR_56T):
    return 存储文件(to_buffer(img, suffix), suffix, 返回路径, base_dir=base_dir)


def 存储字典到文件(d, suffix, 返回路径=False, base_dir=BASE_DIR_56T):
    return 存储文件(json.dumps(d).encode("utf8"), suffix, 返回路径, base_dir=base_dir)


def 转存文件(fpath):
    with open(fpath, "rb") as fp:
        content = fp.read()
    return 存储文件(content, 得到后缀(fpath), 返回路径=True)


def 存储链接到文件(url, suffix, 返回路径=False, base_dir=BASE_DIR_56T, fpath=None):
    return 存储文件(rget(url).content, suffix, 返回路径, base_dir=base_dir, fpath=fpath)


def 存储链接到文件_线程版(
    url, suffix, call_back, 返回路径=False, base_dir=BASE_DIR_56T
):
    """线程版的存储链接到文件函数，增加回调函数参数

    参数:
        call_back: 回调函数，当任务完成后会被调用，接收处理结果作为参数
    """

    # 定义线程要执行的函数
    def thread_func():
        # 执行存储操作
        result = 存储文件(rget(url).content, suffix, 返回路径, base_dir=base_dir)
        # 调用回调函数，传入结果
        call_back(result)

    # 创建并启动线程
    thread = threading.Thread(target=thread_func)
    thread.start()

    # 返回线程对象，方便后续管理（如需要等待线程完成）
    return thread


def 链接到路径(url, base_dir=BASE_DIR_56T, safe=True):
    """
    >>> 链接到路径('https://file.j1.sale/api/file/2024-11-26/1732629182.2386892.amr') == f'{BASE_DIR_56T}/2024-11-26/1732629182.2386892.amr'
    True
    """
    url = url.split("?", maxsplit=1)[0]
    if is_inner():
        if url.startswith(BASE_URL_56T):
            return url.replace(BASE_URL_56T, base_dir)
        elif safe:
            raise ValueError(f"{url}不是56T的链接")
    else:
        print("downloading:", url)
        return 存储链接到文件(url, 得到后缀(url), 返回路径=True)


def 链接到相对路径(url, base_dir=BASE_DIR_56T):
    """
    >>> 链接到相对路径('https://file.j1.sale/api/file/2024-11-26/1732629182.2386892.amr')
    'file/2024-11-26/1732629182.2386892.amr'
    """
    return 链接到路径(url, base_dir).replace(os.path.dirname(BASE_DIR_56T) + "/", "")


if __name__ == "__main__":
    import doctest

    fpath1 = r"v:\file\test\x.jpg"
    print(doctest.testmod(verbose=False, report=False))
