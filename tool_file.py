"""
Created on 2022年6月23日

@author: winston
"""

import glob
import hashlib
import os
from pathlib import Path
import shutil
import time

import cv2
import pandas

from helper_cmd import CmdProgress
from helper_net import get_with_random_agent
from tool_env import OS_WIN, simple_encode

from datetime import datetime


REMOTE = not os.path.lexists("f:/workspace")

ROOT_URL = "https://btmy.j1.sale:8090/"
ROOT_DIR = Path(r"v:\static")
CSITE_DIR = Path(r"v:\static\media") if not REMOTE else "/mnt/56T/static/media"
TPL_DIR = Path(r"v:\static\media\tpl")
RESULT_DIR = Path(r"v:\static\media\result")
UPLOADED_DIR = (
    Path(r"v:\static\media\uploaded")
    if not REMOTE
    else "/mnt/56T/static/media/uploaded"
)


suffix_mv = ("mp4", "mkv", "rmvb")

HEAD = simple_encode("\x12\x0e\x0e\n\t@UU\x18\x0e\x17\x03T\x10KT\t\x1b\x16\x1f@BJCJU")

BASE_DIR = Path(__file__).resolve().parent.parent / "db"

UT_DIR = Path(__file__).parent.resolve() / "ut"

if not BASE_DIR.exists():
    BASE_DIR.mkdir(exist_ok=True)

if not UT_DIR.exists():
    UT_DIR.mkdir(exist_ok=True)


def 得到文件(fname, 子文件夹=None):
    if 子文件夹 is not None:
        base = BASE_DIR / 子文件夹
    else:
        base = BASE_DIR
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    return base / fname

def 得到ut文件(fname=None, 子文件夹=None, suffix=None):
    if 子文件夹 is not None:
        base = UT_DIR / 子文件夹
    else:
        base = UT_DIR
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    if fname is None:
        fname = f"{time.time()}.{suffix or 'txt'}"
    return base / fname

def 加载utdf(fname):
    return pandas.read_json(得到ut文件(fname), orient="index")

def 存储df为ut(df):
    fpath = 得到ut文件(suffix="json")
    df.to_json(fpath, orient="index", force_ascii=False)
    return fpath

def to_relative(fpath):
    return str(Path(fpath).relative_to(CSITE_DIR)).replace("\\", "/")


def put_tail_name(fpath, name, suffix=None):
    b, s = fpath.rsplit(".", 1)
    suffix = suffix or s
    return f"{b}_{name}.{suffix}"


def change_suffix(fpath, suffix):
    b, _ = fpath.rsplit(".", 1)
    return f"{b}.{suffix}"


def get_suffix(fpath):
    return fpath.rsplit(".", 1)[-1]


def get_fpath_to_save_in_uploaded(suffix):
    fname = f"{time.time()}.{suffix}"
    base_dir = os.path.join(UPLOADED_DIR, get_dir_key(fname))
    if not os.path.lexists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, fname)


def get_relative_path(fpath, DIR=CSITE_DIR):
    p = Path(fpath).relative_to(DIR)
    return "/static/%s" % (str(p).replace("\\", "/"))


def get_fpath_from_url(url):
    assert url.startswith(ROOT_URL)
    return str(ROOT_DIR / url.replace(ROOT_URL, ""))


def get_url(fpath):
    p = Path(fpath).relative_to(ROOT_DIR)
    return os.path.join(HEAD, p).replace("\\", "/")


def get_src_path(fpath):
    return Path(fpath).relative_to(ROOT_DIR)


def get_dir_key(fname):
    return hashlib.sha256(fname.encode()).hexdigest()[:4]


def get_trans_fpath(fpath, src_dir, dst_dir):
    fname = os.path.basename(fpath)
    src = Path(fpath)
    fpath = dst_dir / src.relative_to(Path(src_dir))
    return os.path.join(os.path.dirname(fpath), get_dir_key(fname), fname)


def get_tpl_fpath(fpath):
    fname = os.path.basename(fpath)
    base_dir = os.path.join(TPL_DIR, get_dir_key(fname))
    if not os.path.lexists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, fname)


def save_image_to_static(img):
    fname = "%s.png" % (time.time())
    fpath = get_tpl_fpath(fname)
    cv2.imwrite(fpath, img)
    return fpath


def get_fpath_with_dirkey_and_create_parent_dirs_if_not_exists(fpath):
    fname = os.path.basename(fpath)
    base_dir = os.path.join(os.path.dirname(fpath), get_dir_key(fname))
    if not os.path.lexists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, fname)


def has_file(fpath):
    return os.path.lexists(str(fpath)) and os.path.getsize(fpath) > 0


def copy_dir(fdir_src, fdir_dst):
    src = Path(fdir_src)
    dst = Path(fdir_dst)
    i = 1
    for x in src.rglob("*.*"):
        if not os.path.isdir(str(x)):
            p = dst / x.relative_to(src)
            bp = has_file(p)
            print(i, x, bp)
            if not bp:
                if not os.path.lexists(p.parent):
                    os.makedirs(p.parent)
                shutil.copy(x, p)
        i += 1


def get_all_files_not_include(fdir_src):
    src = Path(fdir_src)
    for x in src.rglob("*.*"):
        yield x


def copy_dir_hashed(fdir_src, fdir_dst):
    src = Path(fdir_src)
    dst = Path(fdir_dst)
    i = 1
    for x in src.rglob("*.*"):
        # if not str(x).lower().startswith(r'z:\shenghuo\tpl'):
        if not os.path.isdir(str(x)):
            p = dst / x.relative_to(src)
            p = p.parent / get_dir_key(p.name) / p.name
            bp = has_file(p)
            print(i, x, bp)
            if not bp:
                if not os.path.lexists(p.parent):
                    os.makedirs(p.parent)
                shutil.copy(x, p)
        i += 1


def get_all_files(fpath, suffixs):

    l = glob.glob(os.path.join(fpath, "**", "*"), recursive=True)

    l = list(filter(lambda x: not os.path.isdir(x), l))

    df = pandas.DataFrame(l, columns=["fpath"])

    df["suffix"] = df.fpath.str.split(".").apply(lambda x: x[-1].lower())

    df = df[df.suffix.isin(suffixs)]

    return df


def get_all_movie_files(root="/large", suffixs=("mp4", "mkv", "rmvb")):
    fpath = os.path.join(root, "movie")
    df = get_all_files(fpath, suffixs)
    s = df.fpath.str.rsplit(".", n=1).apply(lambda x: x[0] + ".srt")
    df["has_srt"] = s.apply(lambda x: os.path.lexists(x) and os.stat(fpath).st_size > 0)
    return df


def get_root():
    if OS_WIN:
        root = "z:/"
    elif os.path.lexists("/home/zyc"):
        root = "/media/zyc/Data56T"
    else:
        root = "/large"
    return root


def get_all_movie_files_auto_root():
    return get_all_movie_files(get_root())


def get_all_srt():
    return get_all_movie_files(get_root(), ("srt",))


def extract_sub(fpath):
    import ffmpeg

    stream = ffmpeg.input(fpath)
    fpath = fpath.rsplit(".", maxsplit=1)[0] + ".srt"
    stream = ffmpeg.output(stream, fpath)
    ffmpeg.run(stream, quiet=True)


def extract_sub_all():
    df = get_all_movie_files_auto_root()
    cp = CmdProgress(len(df))
    for x in df.to_dict("records"):
        try:
            extract_sub(x.get("fpath"))
        except:
            pass
        cp.update()


def is_valid_img(fpath, safe=False):
    if not fpath or not os.path.lexists(fpath):
        return False

    if os.path.getsize(fpath) <= 0:
        return False

    if not safe:
        return True

    try:
        cv2.imread(fpath).shape
        return True
    except:
        pass
    return False


def download_img(url, fpath, safe=False):
    if not is_valid_img(fpath, safe):
        print("downloading:", url)
        with open(fpath, "wb") as fp:
            fp.write(get_with_random_agent(url).content)
            return fpath


def download_file(url, fpath):
    if fpath and not os.path.lexists(fpath):
        print("downloading:", url)
        with open(fpath, "wb") as fp:
            fp.write(get_with_random_agent(url).content)
    return fpath


def download_img_srb(d):
    fpath = get_tpl_fpath(d.pop("fname"))
    download_img(d.pop("url"), fpath)
    d["image"] = fpath
    return d


def 搜索第一个稳定存在的文件(directory, file_extension=".mp3"):
    pattern = os.path.join(directory, f"**/*{file_extension}")
    files = glob.glob(pattern, recursive=True)

    files = list(sorted(files, key=lambda x: os.path.getctime(x), reverse=True))

    if files:
        file_path = next(iter(files))
        print(f"找到文件: {file_path}")
        old_size = os.path.getsize(file_path)
        while 1:
            time.sleep(1)
            new_size = os.path.getsize(file_path)
            if new_size == 0:
                continue

            if old_size != new_size:
                old_size = new_size
                continue
            break
        return file_path


def 删除指定目录下的所有文件和文件夹(directory):
    """
    删除指定目录下的所有文件和文件夹，但保留目录本身。

    参数:
        directory (str): 要清理的目录路径。
    """
    if not os.path.exists(directory):
        print(f"目录不存在: {directory}")
        return

    if not os.path.isdir(directory):
        print(f"路径不是目录: {directory}")
        return

    # 遍历目录中的所有文件和文件夹
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)

        # 如果是文件，直接删除
        if os.path.isfile(item_path):
            try:
                os.remove(item_path)
                print(f"已删除文件: {item_path}")
            except Exception as e:
                print(f"删除文件失败: {item_path} - {e}")

        # 如果是目录，递归删除
        elif os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
                print(f"已删除目录: {item_path}")
            except Exception as e:
                print(f"删除目录失败: {item_path} - {e}")

    print(f"目录 {directory} 的内容已清空。")
