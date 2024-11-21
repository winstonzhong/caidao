# -*- coding: UTF-8 -*-
"""
@File        :tool_wechat.py
@Author      : Li Qiang
@Date        : 2023-03-01 15:18
@Description : 微信接口
@lists 内容概览
  - OffiAccount 微信公众号操作

使用说明
"""
import hashlib
import os

from io import BytesIO
import sys
# project_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')
# sys.path.append(project_path)
import json
import requests
import logging
import time

from requests import Request, Session
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client import BaseWeChatClient
from wechatpy.client.api import WeChatMessage
from wechatpy.client.api.base import BaseWeChatAPI


from caidao_tools.mp_weixin.expire_dict import BiasExpireDict

# 微信代理服务器地址


KF_ACCOUNTS_EXPIRED_TIME = 3600  # 客服信息缓存时间(单位:秒)
WEIXIN_PROXY_SERVER_ADDR = ''
logger = logging.getLogger(__name__)
kf_account_data = BiasExpireDict(expire=KF_ACCOUNTS_EXPIRED_TIME, bias=1)


# APP_ID = os.getenv('APP_ID', "123")
# APP_SECRET = os.getenv('APP_SECRET', "123")
# APP_ID_MP_WEIXIN = os.getenv('APP_ID_MP_WEIXIN', "123")
# APP_SECRET_MP_WEIXIN = os.getenv('APP_SECRET_MP_WEIXIN', "123")

def get_img_to_memory(url, fname='1.png'):
    """获取图片url, 并保存至内存中读取,
    本方法是为了构建和open方法创建的file-object对象, 用于requests函数上传文件使用, 所以需要指定一个name属性, 供requests调用时读取.
    """
    resp = requests.get(url)
    f = BytesIO()
    f.write(resp.content)
    f.seek(0)
    f.name = fname
    return f


def replace_url(url, is_replace=False):
    if is_replace:
        url = url.replace('https://api.weixin.qq.com', WEIXIN_PROXY_SERVER_ADDR)
    return url


def request(self, method, url,
            params=None, data=None, headers=None, cookies=None, files=None,
            auth=None, timeout=None, allow_redirects=True, proxies=None,
            hooks=None, stream=None, verify=None, cert=None, json=None):
    """
    复写request, 对所有request请求做拦截操作, 如url替换, 代理修改等
    Constructs a :class:`Request <Request>`, prepares it and sends it.
    Returns :class:`Response <Response>` object.

    :param method: method for the new :class:`Request` object.
    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary or bytes to be sent in the query
        string for the :class:`Request`.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param json: (optional) json to send in the body of the
        :class:`Request`.
    :param headers: (optional) Dictionary of HTTP Headers to send with the
        :class:`Request`.
    :param cookies: (optional) Dict or CookieJar object to send with the
        :class:`Request`.
    :param files: (optional) Dictionary of ``'filename': file-like-objects``
        for multipart encoding upload.
    :param auth: (optional) Auth tuple or callable to enable
        Basic/Digest/Custom HTTP Auth.
    :param timeout: (optional) How long to wait for the server to send
        data before giving up, as a float, or a :ref:`(connect timeout,
        read timeout) <timeouts>` tuple.
    :type timeout: float or tuple
    :param allow_redirects: (optional) Set to True by default.
    :type allow_redirects: bool
    :param proxies: (optional) Dictionary mapping protocol or protocol and
        hostname to the URL of the proxy.
    :param stream: (optional) whether to immediately download the response
        content. Defaults to ``False``.
    :param verify: (optional) Either a boolean, in which case it controls whether we verify
        the server's TLS certificate, or a string, in which case it must be a path
        to a CA bundle to use. Defaults to ``True``. When set to
        ``False``, requests will accept any TLS certificate presented by
        the server, and will ignore hostname mismatches and/or expired
        certificates, which will make your application vulnerable to
        man-in-the-middle (MitM) attacks. Setting verify to ``False``
        may be useful during local development or testing.
    :param cert: (optional) if String, path to ssl client cert file (.pem).
        If Tuple, ('cert', 'key') pair.
    :rtype: requests.Response
    """
    url = replace_url(url)
    # Create the Request.
    req = Request(
        method=method.upper(),
        url=url,
        headers=headers,
        files=files,
        data=data or {},
        json=json,
        params=params or {},
        auth=auth,
        cookies=cookies,
        hooks=hooks,
    )
    prep = self.prepare_request(req)

    proxies = proxies or {}

    settings = self.merge_environment_settings(
        prep.url, proxies, stream, verify, cert
    )

    # Send the request.
    send_kwargs = {
        'timeout': timeout,
        'allow_redirects': allow_redirects,
    }
    send_kwargs.update(settings)
    resp = self.send(prep, **send_kwargs)

    return resp


Session.request = request


class WeChatMessageTyping(BaseWeChatAPI):
    """客服输入状态"""

    def send_typing(self, user_id):
        """
        客服输入状态

        :param user_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :return: 返回的 JSON 数据包
        """
        data = {"touser": user_id, "command": "Typing"}
        return self._post(
            'message/custom/typing',
            data=data
        )

# class MyWeChatClient(WeChatClient):
#     API_BASE_URL = f'http://{WEIXIN_PROXY_SERVER_ADDR}/cgi-bin/'
#
#     message_typing = WeChatMessageTyping()
#
#     def fetch_access_token(self):
#         """
#         获取 access token
#         详情请参考 http://mp.weixin.qq.com/wiki/index.php?title=通用接口文档
#
#         :return: 返回的 JSON 数据包
#         """
#         access_token = self._fetch_access_token(
#             url=f'{self.API_BASE_URL}token',
#             params={
#                 'grant_type': 'client_credential',
#                 'appid': self.appid,
#                 'secret': self.secret
#             }
#         )
#         print(access_token)
#         return access_token


class OffiAccount:
    """微信公众号操作"""

    def __init__(self, app_id, app_secret):
        # WeChatClient.API_BASE_URL = 'http://47.98.218.74/cgi-bin/'
        self.client = WeChatClient(app_id, app_secret)
        self.access_token = self.client.access_token

    def send_typing(self, user_id):
        """客服输入状态"""
        return self.client.message_typing.send_typing(user_id)

    def send_article(self, user_id, title, description, url, pic_url):
        article = {'title': title,
                   'description': description,
                   'url': url,
                   'picurl': pic_url}
        return self.client.message.send_link(user_id, article)

    def reply_msg(self, user_id, reply_msg, account=None):
        """
        回复消息
        :param user_id: 用户ID
        :param reply_msg: 回复消息
        :param account: 客服账号
        :return:
        """
        return self.client.message.send_text(user_id, reply_msg, account=account)

    def reply_img(self, user_id, media_id, account=None):
        """
        回复消息
        :param user_id: 用户ID
        :param media_id: 上传服务器返回的media_id
        :param account: 客服账号
        :return:
        """
        return self.client.message.send_image(user_id, media_id, account=account)

    def get_kf_accounts(self):
        """
        获取微信客服信息: 采取过期字典方式缓存客服信息, 过期后重新调用接口获取客服信息
        :return: dict
        返回示例:
        {2001: {
            'kf_account': 'kf2001@gh_491de88dfc6e',
            'kf_headimgurl': 'http://mmbiz.qpic.cn/mmbiz_jpg/ZicbGqaKgp7ocianicLE6quicxNW6XuYJRzY8dsMAb7L2t9ickTzsWNEz17Yibs1z1PibFMo70Sd7zib8Gr3tsu3tQGhQw/300?wx_fmt=jpeg/0',
            'kf_nick': '小C',
            'kf_wx': 'c3****946'
            }
        }
        """
        global kf_account_data
        if kf_account_data.keys():
            return kf_account_data
        else:
            account_list = self.client.customservice.get_accounts()
            for account in account_list:
                kf_id = account.pop('kf_id')
                kf_account_data[kf_id] = account
        return kf_account_data

    def create_menu(self, menu_data):
        return self.client.menu.create(menu_data)

    def create_temp_qrcode_img_url(self, action_info, timeout=10, action_name='QR_STR_SCENE'):
        """创建临时二维码
        参考: https://developers.weixin.qq.com/doc/offiaccount/Account_Management/Generating_a_Parametric_QR_Code.html
        :param action_info: 二维码参数
        :param timeout: 过期时间 - 最大2592000（即30天）
        :param action_name: QR_STR_SCENE | QR_SCENE
        :return:
        """
        data = {
            'expire_seconds': timeout,
            'action_name': action_name,
            'action_info': {
                'scene':{}
                    # {'scene_str': action_info},
            }
        }
        if action_name == 'QR_STR_SCENE':

            data['action_info']['scene']['scene_str'] = action_info
        else:
            assert isinstance(action_info, int)
            data['action_info']['scene']['scene_id'] = action_info
        ret_data = self.client.qrcode.create(data)
        print('ret_data', ret_data)
        return self.client.qrcode.get_url(ret_data['ticket'])

        # return self.client.qrcode.get_url('gQEP8DwAAAAAAAAAAS5odHRwOi8vd2VpeGluLnFxLmNvbS9xLzAyOFRFVTlfSmtldEQxNEI5eGhBYzQAAgTpSCFkAwQ8AAAA')

    def get_message(self, start_time, end_time, msgid=1, number=10000):
        return self.client.customservice.get_records(start_time, end_time, msgid=msgid, number=number)

    def get_material_count(self):
        return self.client.material.get_count()

    def add_tmp_img(self, fpath):
        return self.client.media.upload('image', open(fpath, 'rb'))

    def add_tmp_img_remote(self, url):
        f = get_img_to_memory(url)
        return self.client.media.upload('image', f)

    def get_tmp_img_url(self, media_id):
        return self.client.media.get_url(media_id)

    def upload_tmp_img(self, fpath):
        data = oa.add_tmp_img(fpath)
        img_url = oa.get_tmp_img_url(data['media_id'])
        return img_url

    def upload_material(self, fpath, file_type='image'):
        ret_data = self.client.material.add(file_type, open(fpath, 'rb'))
        print(ret_data)
        return ret_data['media_id']

    def send_index_page(self, user_id, img_url=None):
        if not img_url:
            img_url = 'https://dss0.bdstatic.com/5aV1bjqh_Q23odCf/static/superman/img/logo/bd_logo1-66368c33f8.png'
        self.send_article(user_id, '用户首页', '用户首页',
                        'https://chat-live.med-value.com/pages/user/index',
                        img_url
                        )

    def send_eula_page(self, user_id, img_url=None):
        if not img_url:
            img_url = 'https://img1.baidu.com/it/u=2274835460,799751483&fm=253&fmt=auto&app=138&f=JPEG?w=396&h=500'
        self.send_article(user_id, '用户协议', '查看并同意用户协议之后小聊才能为您服务',
                        'https://chat-live.med-value.com/pages/user/eula',
                        img_url
                        )

    def get_jsapi_ticket(self):
        return self.client.jsapi.get_jsapi_ticket()

    def get_jsapi_signature(self, noncestr, timestamp, url):
        ticket = self.get_jsapi_ticket()
        return self.client.jsapi.get_jsapi_signature(noncestr, ticket, timestamp, url)


if __name__ == '__main__':
    # oa = OffiAccount()

    oa = OffiAccount('123', '123')
    print(oa.access_token)
    # test()
    # img_url = oa.upload_tmp_img('/mnt/d/1.png')
    # print(img_url)
    # x =oa.get_tmp_img_url("LPrzV7x6BDKiodZFbvCFNjUYatvI3AO8Ig-7yIht0_5QqTajSZclNarzCIQfq5hy")
    # print(x)

    # oa.upload_material('/mnt/d/1.png')
    # media_id = 'ILWSWmW3bP6zCwjvxO7jEajuRs0LoKPYlPyESuSW9d4TvyBGfwapPlYAeiuFx1JW'  # 永久素材media_id
    # 'ILWSWmW3bP6zCwjvxO7jEVTSr1ezxUQbpcOnMFKCUTi4p1ENB4Tei9r0IgiRY31R'
    # oa.add_tmp_img('/mnt/d/1.png')

    # url = oa.get_tmp_img_url('l_Avysz1YLAa4t5EZjAIYGA0KWaqFkqz8FTCsPoFEB7AN-ohEVslOBxrF7z7dUrI')
    # print(url)
    oa.send_article('orRSd56HefLUut_ia-xwXGlmCH68', '鱼跃(yuwell)血糖仪580 家用医用款 语音免调码低痛采血 糖尿病血糖测试仪（50片血糖试纸+50支采血针）', '查看详情', 'https://chat-live.j1.sale/product?id=8', 'https://file.j1.sale/api/file/2024-09-12/84286a4e-70d9-11ef-9f41-0242ac120002.png')
    # oa.reply_img('orRSd56HefLUut_ia-xwXGlmCH68', 'Ru5HW9LTcmgRCixmZ3_CdenSfac1JtXS1LoxWMVEViYDVx3ScpuHMrV3fGgOGvh9')
    # x = oa.add_tmp_img_remote('https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png')
    # x = oa.get_tmp_img_url('rEAssefTyr8MuDPtyugp5dr7Urew2P7u25pGK9M4Z-2Uo3FfVKkOguogIWHXLci7')
    # print(x)
    # print(x)
    # menu_data = {
    #         "button": [
    #             {
    #                 "name": "申请提现",
    #                 "type": "click",
    #                 "key": "withdraw"
    #             },
    #             {
    #                 "name": "支付",
    #                 "type": "view",
    #                 "url": "https://chat-live.med-value.com/pages/pay/pay/pay"
    #             }
    #         ]
    #     }

    menu_data = {
    "button": [
        {
            "name": "扫码",
            "sub_button": [
                {
                    "type": "scancode_waitmsg",
                    "name": "扫码带提示",
                    "key": "rselfmenu_0_0",
                    "sub_button": [ ]
                },
                {
                    "type": "scancode_push",
                    "name": "扫码推事件",
                    "key": "rselfmenu_0_1",
                    "sub_button": [ ]
                }
            ]
        },
        {
            "name": "发图",
            "sub_button": [
                {
                    "type": "pic_sysphoto",
                    "name": "系统拍照发图",
                    "key": "rselfmenu_1_0",
                   "sub_button": [ ]
                 },
                {
                    "type": "pic_photo_or_album",
                    "name": "拍照或者相册发图",
                    "key": "rselfmenu_1_1",
                    "sub_button": [ ]
                },
                {
                    "type": "pic_weixin",
                    "name": "微信相册发图",
                    "key": "rselfmenu_1_2",
                    "sub_button": [ ]
                }
            ]
        },
        {
            "name": "发送位置",
            "type": "location_select",
            "key": "rselfmenu_2_0"
        },
        {
           "type": "media_id",
           "name": "图片",
           "media_id": "MEDIA_ID1"
        },
        {
           "type": "view_limited",
           "name": "图文消息",
           "media_id": "MEDIA_ID2"
        },
        {
            "type": "article_id",
            "name": "发布后的图文消息",
            "article_id": "ARTICLE_ID1"
        },
        {
            "type": "article_view_limited",
            "name": "发布后的图文消息",
            "article_id": "ARTICLE_ID2"
        }
    ]
}

    # oa.reply_msg('orRSd56HefLUut_ia-xwXGlmCH68', '22222')
    # x = oa.create_menu(menu_data)
    # print(x)
    # while 1:
    #     print(kf_account_data)
    #     d = oa.get_kf_accounts()
    #     print(d)
    #     time.sleep(1)


    # x = oa.get_message(1679980000, 1679989221)
    # print(x)

    # x = oa.create_temp_qrcode_img_url('1|orRSd56HefLUut_ia-xwXGlmCH68')
    # print(x)

    # x = oa.get_qrcode_img('gQFk8DwAAAAAAAAAAS5odHRwOi8vd2VpeGluLnFxLmNvbS9xLzAyeEEyLTlqSmtldEQxN3M0eGhBMTIAAgTUPSFkAwQIBwAA')
    # print(x)

    # x = oa.get_material_count()

    # data = oa.add_tmp_img('/mnt/d/1.jpg')
    # print(data)
    # x = oa.get_tmp_img_url(data['media_id'])



    #
    # with open('/mnt/d/1_1.jpg', 'wb') as f:
    #     f.write(x.content)
    # print(x.content)