# -*- coding: UTF-8 -*-
"""
@File        :tool_wechat.py
@Author      : Li Qiang
@Date        : 2023-03-01 15:18
@Description : 微信接口
@lists 内容概览
  - OffiAccount 微信公众号操作

使用说明
pip install wechatpy==2.0.0a26
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
from wechatpy.client.api import WeChatMessage, WeChatMedia
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

def url_to_memory(url, fname='1.png'):
    """获取图片url, 并保存至内存中读取,
    本方法是为了构建和open方法创建的file-object对象, 用于requests函数上传文件使用, 所以需要指定一个name属性, 供requests调用时读取.
    """
    # print('fname', fname)
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


class WeChatMessageTyping(WeChatMessage):
    """客服输入状态"""

    def send_typing(self, open_id):
        """
        客服输入状态

        :param open_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :return: 返回的 JSON 数据包
        """
        data = {"touser": open_id, "command": "Typing"}
        return self._post(
            'message/custom/typing',
            data=data
        )


class MyWeChatMedia(WeChatMedia):
    def upload_voice_for_text(self, voice_id, media_file):
        """
        上传音频转文字
        :param voice_id: 自定义voice_id
        :param media_file:
        :return:
        """
        return self._post(url="media/voice/addvoicetorecofortext",
                          params={"format": "mp3", "voice_id": voice_id},
                          files={"media": media_file})

    def query_voice_result_for_text(self, voice_id):
        """
        获取语音转文字识别结果
        :param voice_id:: 自定义voice_id
        :return:
        """
        return self._post(url="media/voice/queryrecoresultfortext", params={"voice_id": voice_id})


WeChatClient.media = MyWeChatMedia()

WeChatClient.message = WeChatMessageTyping()



class OffiAccount:
    """微信公众号操作"""

    def __init__(self, app_id, app_secret):
        # WeChatClient.API_BASE_URL = 'http://47.98.218.74/cgi-bin/'
        self.app_id = app_id
        self.app_secret = app_secret
        self._client = None
        # self.access_token = self.client.access_token
    
    @property
    def expired(self):
        expires_at = self._client.expires_at
        return expires_at - time.time() <= 200 if expires_at is not None else False
    
    @property
    def client(self):
        if self._client is None or self.expired:
            self._client = WeChatClient(self.app_id, self.app_secret) 
        return self._client
    
    def get_tmp_media_data_by_url(self, url, media_type, fname):
        """根据url获取临时素材的media_id"""
        f = url_to_memory(url, fname=fname)
        return self.client.media.upload(media_type, f)

    def get_tmp_img_media_id_by_url(self, url):
        """获取图片格式临时素材的media_id"""
        return self.get_tmp_media_data_by_url(url, 'image', 'image.jpg')['media_id']

    def get_tmp_voice_media_id_by_url(self, url):
        """获取语音格式临时素材的media_id"""
        return self.get_tmp_media_data_by_url(url, 'voice', 'voice.mp3')['media_id']

    def get_tmp_video_media_id_by_url(self, url):
        """获取视频格式临时素材的media_id"""
        return self.get_tmp_media_data_by_url(url, 'video', 'video.mp4')['media_id']

    def get_tmp_thumb_media_id_by_url(self, url):
        """获取缩略图片格式临时素材的media_id"""
        return self.get_tmp_media_data_by_url(url, 'thumb', 'thumb.jpg')['thumb_media_id']

    def get_media_data_by_url(self, url, media_type, fname=None, title=None, introduction=None):
        """
        根据url获取永久素材的media_id
        :param url: 文件url
        :param media_type: 媒体文件类型，分别有图片（image）、语音（voice）、视频（video）和缩略图（thumb）
        :param fname: 文件名
        :param title: 视频素材标题，仅上传视频素材时需要
        :param introduction: 视频素材简介，仅上传视频素材时需要
        :return: 返回的 JSON 数据包
        """
        if not fname:
            fname = url.rsplit('/')[-1]
        f = url_to_memory(url, fname=fname)
        data = self.client.material.add(media_type, f, title=title, introduction=introduction)
        print(data)
        return data

    def get_img_media_data_by_url(self, url):
        """获取图片格式永久素材的media_id"""
        return self.get_media_data_by_url(url, 'image')

    def get_voice_media_data_by_url(self, url):
        """获取语音格式永久素材的media_id"""
        return self.get_media_data_by_url(url, 'voice')

    def get_video_media_data_by_url(self, url, title=None, introduction=None):
        """获取视频格式永久素材的media_id"""
        return self.get_media_data_by_url(url, 'video', title=title, introduction=introduction)['media_id']

    def get_thumb_media_data_by_url(self, url):
        """获取缩略图片格式永久素材的media_id"""
        return self.get_media_data_by_url(url, 'thumb')

    def get_thumb_media_id_by_url(self, url):
        """获取缩略图片格式永久素材的media_id"""
        return self.get_media_data_by_url(url, 'thumb')['media_id']

    def send_typing(self, open_id):
        """客服输入状态"""
        return self.client.message.send_typing(open_id)

    def reply_img_by_media_id(self, open_id, media_id, account=None):
        """
        基于media_id回复图片
        :param open_id: 用户ID
        :param media_id: 上传服务器返回的media_id
        :param account: 客服账号
        :return:
        """
        return self.client.message.send_image(open_id, media_id, account=account)

    def reply_voice_by_media_id(self, open_id, media_id, account=None):
        """
        基于media_id回复图片
        :param open_id: 用户ID
        :param media_id: 上传服务器返回的media_id
        :param account: 客服账号
        :return:
        """
        return self.client.message.send_voice(open_id, media_id, account=account)

    def reply_video_by_media_id(self, open_id, media_id, title=None, description=None, account=None):
        """
        基于media_id回复图片
        :param open_id: 用户ID
        :param media_id: 发送的视频的媒体ID。 可以通过 :func:`upload_media` 上传。
        :param title: 视频消息的标题
        :param description: 视频消息的描述
        :param account: 可选，客服账号
        :return: 返回的 JSON 数据包
        """
        return self.client.message.send_video(open_id, media_id, title=title, description=description, account=account)



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

    def query_menu(self):
        """查询菜单"""
        return self.client.menu.get_menu_info()

    def create_menu(self, menu_data):
        """创建菜单
            {
                "button": [{
                    "type": "click",
                    "name": "今日资讯",
                    "key": "daily_news"
                }, {
                    "name": "菜单",
                    "sub_button": [{
                        "type": "click",
                        "name": "常见问题",
                        "key": "faq"
                    }, {
                        "type": "view",
                        "name": "我的健康档案",
                        "url": "https://chat-live.j1.sale/h5"
                    }, {
                        "type": "view",
                        "name": "购买建档服务",
                        "url": "https://chat-live.j1.sale/product?id=1"
                    }, {
                        "type": "view",
                        "name": "绑定邮箱",
                        "url": "https://chat-live.j1.sale/accountbind"
                    }
                    ]
                }]
            }

        """
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

    def get_tmp_img_url(self, media_id):
        return self.client.media.get_url(media_id)

    def upload_tmp_img(self, fpath):
        data = oa.add_tmp_img(fpath)
        img_url = oa.get_tmp_img_url(data['media_id'])
        return img_url

    def upload_material(self, fpath, file_type='image'):
        with open(fpath, 'rb') as fp:
            ret_data = self.client.material.add(file_type, fp)
            return ret_data 
            # print(ret_data)
            # return ret_data['media_id']

    def send_index_page(self, open_id, img_url=None):
        if not img_url:
            img_url = 'https://dss0.bdstatic.com/5aV1bjqh_Q23odCf/static/superman/img/logo/bd_logo1-66368c33f8.png'
        self.reply_page_card(open_id, '用户首页', '用户首页',
                        'https://chat-live.med-value.com/pages/user/index',
                        img_url
                        )

    def send_eula_page(self, open_id, img_url=None):
        if not img_url:
            img_url = 'https://img1.baidu.com/it/u=2274835460,799751483&fm=253&fmt=auto&app=138&f=JPEG?w=396&h=500'
        self.reply_page_card(open_id, '用户协议', '查看并同意用户协议之后小聊才能为您服务',
                        'https://chat-live.med-value.com/pages/user/eula',
                        img_url
                        )

    def get_jsapi_ticket(self):
        return self.client.jsapi.get_jsapi_ticket()

    def get_jsapi_signature(self, noncestr, timestamp, url):
        ticket = self.get_jsapi_ticket()
        return self.client.jsapi.get_jsapi_signature(noncestr, ticket, timestamp, url)

    def reply_text(self, open_id, reply_text, account=None):
        """
        回复文本消息
        :param open_id: 用户open_id
        :param reply_text: 回复消息
        :param account: 客服账号
        :return:
        """
        return self.client.message.send_text(open_id, reply_text, account=account)

    def reply_msg_menu(self, open_id, menu_list, head_content='', tail_content='', account=None):
        """
        回复快捷菜单消息
        msg_menu = {
            "head_content": "您对本次服务是否满意呢？",
            "list": [
                {
                    "id": "101",
                    "content": "满意"
                },
                {
                    "id": "102",
                    "content": "不满意"
                },
            ],
            "tail_content": "欢迎再次光临"
        }
        :param open_id: 用户open_id;
        :param menu_list: 菜单项; ['满意', '不满意']
        :param head_content: 开头;
        :param tail_content: 结尾;
        :param account: 客服账号;
        :return:
        """
        msg_menu = {
            "head_content": head_content,
            "list": [],
            "tail_content": tail_content
        }
        for idx, menu in enumerate(menu_list):
            menu_item = {'id': idx, 'content': menu}
            msg_menu['list'].append(menu_item)
        return self.client.message.send_msg_menu(open_id, msg_menu, account=account)

    def reply_img(self, open_id, url, account=None):
        """
        回复图片消息
        :param open_id: open_id
        :param url: 图片url (10M，支持PNG\JPEG\JPG\GIF格式)
        :param account: 客服账号
        :return:
        """
        media_id = self.get_tmp_img_media_id_by_url(url)
        return self.reply_img_by_media_id(open_id, media_id, account=account)

    def reply_voice(self, open_id, url, account=None):
        """
        回复语音消息
        :param open_id: open_id
        :param url: 文件url (2M，播放长度不超过60s，支持AMR\MP3格式)
        :param account: 客服账号
        :return:
        """
        media_id = self.get_tmp_voice_media_id_by_url(url)
        print('media_id', media_id)
        return self.reply_voice_by_media_id(open_id, media_id, account=account)

    def reply_video(self, open_id, url, title=None, description=None, account=None):
        """
        回复视频消息
        :param open_id: open_id
        :param title: 视频消息的标题
        :param url: 文件url (10MB，支持MP4格式)
        :param description: 视频消息的描述
        :param account: 可选，客服账号
        :return:
        """
        media_id = self.get_tmp_video_media_id_by_url(url)
        return self.reply_video_by_media_id(open_id, media_id, title=title, description=description, account=account)

    def reply_page_card(self, open_id, title, description, url, pic_url):
        """发送页面卡片消息"""
        article = {'title': title,
                   'description': description,
                   'url': url,
                   'picurl': pic_url}
        return self.client.message.send_link(open_id, article)

    def add_draft_article(self, thumb_url, article):
        """添加文章到草稿箱
        article = {
            "title":'测试',
            "author":'张三',
            "digest":'这是摘要',
            "content":'这是内容',
            "content_source_url":'https://chat-live.j1.sale/product?id=7',
            "thumb_media_id":'',
            "need_open_comment":1,
            "only_fans_can_comment":1,
        }
        """
        thumb_media_id = self.get_thumb_media_id_by_url(thumb_url)
        article['thumb_media_id'] = thumb_media_id
        return self.client.draft.add([article])

    def del_draft_article(self, media_id):
        """删除草稿箱文章"""
        return self.client.draft.delete(media_id)

    def publish_article(self, media_id):
        """草稿箱文章发布"""
        return self.client.freepublish.submit(media_id)

    def get_article(self, publish_id):
        """
        获取文章信息
        发布状态(publish_status)，0:成功, 1:发布中，2:原创失败, 3: 常规失败, 4:平台审核不通过, 5:成功后用户删除所有文章, 6: 成功后系统封禁所有文章
        """
        return self.client.freepublish.get(publish_id)

    def del_article(self, article_id):
        """发布文章删除, 通过get_article方法获取"""
        return self.client.freepublish.delete(article_id)

    def upload_voice_for_text(self, voice_id, url):
        """上传音频转文字"""
        media_file = url_to_memory(url, fname='1.mp3')
        return self.client.media.upload_voice_for_text(voice_id, media_file)

    def query_voice_result_for_text(self, voice_id):
        """获取语音转文字识别结果"""
        return self.client.media.query_voice_result_for_text(voice_id)
    
    def 同步识别语音MP3(self, url):
        voice_id = f'{time.time()}'
        rtn = self.upload_voice_for_text(voice_id, url)
        assert rtn.get('errcode') == 0, rtn
        while 1:
            rtn = self.query_voice_result_for_text(voice_id)
            assert rtn.get('is_end'), rtn
            return rtn.get('result')

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
    oa.reply_page_card('orRSd56HefLUut_ia-xwXGlmCH68', '鱼跃(yuwell)血糖仪580 家用医用款 语音免调码低痛采血 糖尿病血糖测试仪（50片血糖试纸+50支采血针）', '查看详情', 'https://chat-live.j1.sale/product?id=8', 'https://file.j1.sale/api/file/2024-09-12/84286a4e-70d9-11ef-9f41-0242ac120002.png')
    # oa.reply_img('orRSd56HefLUut_ia-xwXGlmCH68', 'Ru5HW9LTcmgRCixmZ3_CdenSfac1JtXS1LoxWMVEViYDVx3ScpuHMrV3fGgOGvh9')
    # x = oa.get_tmp_img_media_id_by_url('https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png')
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

    # oa.reply_text('orRSd56HefLUut_ia-xwXGlmCH68', '22222')
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