'''
Created on 2022年6月3日

@author: Administrator
'''
import platform

OS_WIN = platform.system() == 'Windows'


def is_chinese(ch):
    return '\u4e00' <= ch <= '\u9fff'


def has_chinese(line):
    for ch in line:
        if is_chinese(ch):
            return True
    return False
