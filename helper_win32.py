'''
Created on 2023年12月20日

@author: lenovo
'''
'''
Created on 2023年7月23日

@author: lenovo
'''
# def wait_window_open(game, hwnd, try_times=TRY_TIMES):
#     """根据句柄尝试获取窗口"""
#     time.sleep(WAIT_WINDOW_TIME)
#     # print('1111', win32gui.IsWindow(hwnd))
#
#     while not win32gui.IsWindow(game.__getattribute__(hwnd)) and try_times:
#         try_times -= 1
#         print(f'wait hwnd {hwnd}, times: {try_times}')
#         # print(f'wait hwnd {hwnd}')
#         time.sleep(WAIT_WINDOW_TIME)

import ctypes
import os
import subprocess
import time

from PIL import Image, ImageGrab
import psutil
import pywintypes
import win32api
import win32con
import win32gui
from win32process import GetWindowThreadProcessId
import win32process
import win32ui

from tool_rect import Rect


class InvalidHwnd(Exception):
    pass

class WindowNotFound(Exception):
    pass

class ScreenCopyFailed(Exception):
    pass

class MsgException(Exception):
    default_msg = '%s'
    code = 4000

    def __init__(self, msg=''):

        print(self.default_msg, msg)
        self.msg = self.default_msg % msg
        
        
class GetWindowError(MsgException):
    """获取窗口句柄失败"""
    default_msg = '%s'
    code = 4001


def find_process_id_by_name(process_name):
    process_ids = []
    for proc in psutil.process_iter():
        try:
            if proc.name() == process_name:
                process_ids.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return process_ids    

def get_current_cmd_pid():
    current_pid = os.getpid()
    current_proc = psutil.Process(current_pid)

    parent_proc = current_proc.parent()

    return parent_proc.pid


def get_main_window_handle_by_pid(pid):
    def callback(hwnd, hwnd_list):
        if win32gui.IsWindowVisible(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                parent_hwnd = win32gui.GetParent(hwnd)
                # print(win32gui.GetWindowText(hwnd))
                if parent_hwnd == 0:
                    hwnd_list.append(hwnd)
        return True

    hwnd_list = []
    win32gui.EnumWindows(callback, hwnd_list)
    return hwnd_list

def 置顶当前命令行窗口():
    pid = get_current_cmd_pid()
    hwnds = get_main_window_handle_by_pid(pid)
    SET_TOPMOST(hwnds[0])
    
    
def GET_RECT(hwnd):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return Rect(left, right, top, bottom)


def GET_RECT_ACCU(hwnd):
    try:
        f = ctypes.windll.dwmapi.DwmGetWindowAttribute
    except WindowsError:
        f = None
    if f:
        rect = ctypes.wintypes.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        f(ctypes.wintypes.HWND(hwnd),
          ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
          ctypes.byref(rect),
          ctypes.sizeof(rect)
          )
        return Rect(rect.left, rect.right, rect.top, rect.bottom)

def GET_CHILD_WINDOWS(hwnd):
    hWndList = []
    win32gui.EnumChildWindows(hwnd, lambda x, _: hWndList.append(x), None)
    return list(map(lambda hwnd:{
                    'clsname':win32gui.GetClassName(hwnd),
                    'title': win32gui.GetWindowText(hwnd),
                    'rect': GET_RECT(hwnd),
                    'hwnd':hwnd,
                    },
                    hWndList))

def FIND_CHILD_WINDOW(hwnd, clsname=None, title=None):
    for x in GET_CHILD_WINDOWS(hwnd):
        if clsname is None or clsname == x.get('clsname'):
            if title is None or title == x.get('title'):
                return x


def GET_WINDOWS(clsname=None, title=None, pid=None, visible=None, clsname_startswith=None, debug=False):
    hWndList = []  
    win32gui.EnumWindows(lambda hWnd, param: param.append(hWnd), hWndList)
    
    rtn = []
    for hwnd  in hWndList:
        if win32gui.IsWindow(hwnd):
            try:
                tmp_clsname = win32gui.GetClassName(hwnd)
            except pywintypes.error as e:
                raise GetWindowError(f'GetClassName, {e.strerror}, hwnd: {hwnd}')
            if (clsname is None or clsname == tmp_clsname) or (clsname_startswith is None or tmp_clsname.startswith(clsname_startswith)):
                if title is None or title == win32gui.GetWindowText(hwnd):
                    if pid is None or pid == GetWindowThreadProcessId(hwnd)[1]:
                        if visible is None or visible == win32gui.IsWindowVisible(hwnd):
                            if debug:
                                print([win32gui.GetWindowText(hwnd)], tmp_clsname, hwnd)
                            rtn.append(hwnd)
    if not rtn:
        raise WindowNotFound
    return rtn
    
def FIND_WINDOW(clsname=None, title=None, pid=None, visible=None):
    return GET_WINDOWS(clsname, title, pid, visible)[0]


def SET_TOPMOST(hwnd):
    rect = win32gui.GetWindowRect(hwnd)
    x = rect[0]
    y = rect[1]
    w = rect[2] - x
    h = rect[3] - y
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, x, y, w, h, 0)        



def FIND_WINDOW_GAME(ppid, clsname=None, title=None, pid=None, visible=1, clsname_startswith='SDL_app'):
    for hwnd in GET_WINDOWS(clsname, title, pid, visible, clsname_startswith):
        try:
            proc = psutil.Process(pid=GetWindowThreadProcessId(hwnd)[1])
            while 1:
                proc = proc.parent()
                if proc is None:
                    break
                if proc.pid == ppid:
                    return hwnd
        except Exception as e:
            print('error in find window game:', hwnd, e)

SLEEP_MAIN = 3
SLEEP_QR = 0.5

def GET_MAIN_PROCS(proc_name):
    rtn= []
    for i, proc in enumerate(psutil.process_iter()):
        # print([proc.name()])
        if proc.name().lower() == proc_name:# and proc.parent() is None:
            # print(i, proc)
            rtn.append(proc)
    return rtn

def START_NEW_MAIN(EXE):
    s = set(map(lambda x:x.pid, GET_MAIN_PROCS()))
    subprocess_popen(EXE)
    time.sleep(SLEEP_MAIN)
    s = set(map(lambda x:x.pid, GET_MAIN_PROCS())) - s
    # assert len(s) == 1
    print('main processed:', s)
    return s.pop()

def subprocess_popen(statement):
    p = subprocess.Popen(statement, shell=True, stdout=subprocess.PIPE)  # 执行shell语句并定义输出格式
    while p.poll() is None:  # 判断进程是否结束（Popen.poll()用于检查子进程（命令）是否已经执行结束，没结束返回None，结束后返回状态码）
        if p.wait() != 0:  # 判断是否执行成功（Popen.wait()等待子进程结束，并返回状态码；如果设置并且在timeout指定的秒数之后进程还没有结束，将会抛出一个TimeoutExpired异常。）
            print("命令执行失败，请检查设备连接状态")
            return False
        else:
            re = p.stdout.readlines()  # 获取原始执行结果
            result = []
            for i in range(len(re)):  # 由于原始结果需要转换编码，所以循环转为utf8编码并且去除\n换行
                res = re[i].decode('utf-8').strip('\r\n')
                result.append(res)
            return result


def SCREEN_GRAB(hwnd):
    try:
        rect= GET_RECT_ACCU(hwnd)
        return ImageGrab.grab((rect.left,
                               rect.top,
                               rect.right,
                               rect.bottom)
        )
    except Exception as e:
        print(e)

def get_width_and_height(hwnd):
    try:
        # left, top, right, bot = win32gui.GetWindowRect(hwnd)
        rect = GET_RECT_ACCU(hwnd)
        return rect.width, rect.height
    except:
        raise InvalidHwnd

def get_width_and_height_old(hwnd):
    try:
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        return right - left, bot - top
    except:
        raise InvalidHwnd


def SCREENSHOT(hwnd):
    # try:
    #     # left, top, right, bot = win32gui.GetWindowRect(hwnd)
    #     rect = GET_RECT_ACCU(hwnd)
    # except:
    #     raise InvalidHwnd
    #
    # # width = right - left
    # # height = bot - top
    # width = rect.width
    # height = rect.height
    
    width, height = get_width_and_height_old(hwnd)
    
    hWndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hWndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC,width,height)
    saveDC.SelectObject(saveBitMap)
    saveDC.BitBlt((0,0), (width,height), mfcDC, (0, 0), win32con.SRCCOPY)
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    if len(bmpstr) > 2:
        im_PIL = Image.frombuffer('RGB',(bmpinfo['bmWidth'],bmpinfo['bmHeight']),bmpstr,'raw','BGRX',0,1)
    else:
        im_PIL = None
        
    try:
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
    except win32ui.error as e:
        print(e)
    
    if im_PIL is None:
        raise ScreenCopyFailed
    return im_PIL