# -*- coding: UTF-8 -*-
"""
@File        :exceptions.py
@Author      : Li Qiang
@Date        : 2023-12-15 12:19 
@Description : 
@lists 内容概览
  - 
"""


class ElementNotFoundError(Exception):

    def __init__(self, msg, page_name=None):
        self.msg = msg
        self.page_name = page_name


class TplNotFoundError(Exception):
    pass


class NotNeedFurtherActions(Exception):
    pass


class SubmitFailError(Exception):

    def __init__(self, msg):
        self.msg = msg