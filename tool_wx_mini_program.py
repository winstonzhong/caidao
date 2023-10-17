import datetime
import io
import json

import cv2
import requests


APP_ID = '11'
SECRET = '22'

class MiniProgramBase:
    APP_ID = None
    SECRET = None
    def __init__(self):
        self.app_id = self.APP_ID
        self.secret = self.SECRET
        self.access_token = self.get_access_token()

    def get_access_token(self):
        """
        获取小程序access token
        """
        url = 'https://api.weixin.qq.com/cgi-bin/stable_token'
        data = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.secret
        }
        j = requests.post(url, json=data).json()
        return j['access_token']

    def upload_tmp_img(self, img_path):
        """
        上传图片至临时素材库
        :param img_path: 本地图片路径
        :return: media_id
        """
        url = f'https://api.weixin.qq.com/cgi-bin/media/upload?access_token={self.access_token}&type=image'
        file_name = img_path.replace('\\', '/').split('/')[-1]
        # print('file_name', file_name)
        multipart_form_data = {'media': (file_name, open(img_path, 'rb'))}
        resp_data = requests.post(url, files=multipart_form_data).json()
        # print('resp_data', resp_data)
        return resp_data['media_id']
    
    def upload_tmp_img_cv2(self, img):
        url = f'https://api.weixin.qq.com/cgi-bin/media/upload?access_token={self.access_token}&type=image'
        _, buffer = cv2.imencode(".png", img)
        multipart_form_data = {'media': ('test.png', io.BytesIO(buffer))}
        resp_data = requests.post(url, files=multipart_form_data).json()
        return resp_data['media_id']
        

    def send_msg(self, open_id, content):
        """
        发送文本消息给客户
        :param open_id: 客户open_id
        :param content: 发送的文本消息
        :return:
        """
        data = {
            'touser': open_id,
            'msgtype': 'text',
            'text': {
                'content': content
            }
        }
        # print('data', data)
        url = f'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={self.access_token}'
        resp_data = requests.post(url, data=json.dumps(data, ensure_ascii=False).encode()).json()
        return resp_data['errcode'] == 0, resp_data

    def send_img(self, open_id, img_or_fpath):
        """
        发送图片至用户
        :param open_id:
        :param img_path:
        :return:
        """
        # print(type(img_or_fpath), type(img_or_fpath)==str)
        media_id = self.upload_tmp_img(img_or_fpath) if type(img_or_fpath) == str else self.upload_tmp_img_cv2(img_or_fpath)
        url = f'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={self.access_token}'
        data = {
            'touser': open_id,
            'msgtype': 'image',
            'image': {
                'media_id': media_id
            }
        }
        resp_data = requests.post(url, json=data).json()
        return resp_data['errcode'] == 0, resp_data

    def send_card_msessage(self, open_id, title, page_path, img_path):
        """
        发哦卡片消息
        :param data:
        :return:
        """
        media_id = self.upload_tmp_img(img_path)
        url = f'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={self.access_token}'
        data = {
            'touser': open_id,
            'msgtype': 'miniprogrampage',
            'miniprogrampage': {
                'thumb_media_id': media_id,
                'title': title,
                'pagepath': page_path
            }
        }
        resp_data = requests.post(url, data=json.dumps(data, ensure_ascii=False).encode()).json()
        return resp_data['errcode'] == 0, resp_data

    def send_subscribe_message(self, data):
        """
        发送订阅消息
        :param data:  消息体。字典类型
        :return: is success, response data
        """
        url = f'https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={self.access_token}'
        # r = requests.post(url, json=data)
        resp_data = requests.post(url, data=json.dumps(data, ensure_ascii=False).encode()).json()
        # print(r)
        return resp_data['errcode'] == 0, resp_data


class MiniProgram(MiniProgramBase):
    def send_complete_subscribe_message(self,
                                        open_id,
                                        source_code,
                                        order_id,
                                        miniprogram_state='formal',
                                        page='pages/mp-weixin/user/result',
                                        template_id='SuaB_F3ThFXEXgkVk67wxZxGDqkugTBAVSouM5ud8kQ'
                                        ):
        """
        发送结果订阅消息
        :param open_id: 接收者的open_id
        :param source_code: 溯源码
        :param order_id: 订单号
        :param miniprogram_state: # 跳转小程序类型：developer为开发版；trial为体验版；formal为正式版；默认为正式版
        :param page: 跳转页面
        :param template_id: 模板ID
        :return:
        """
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        data = {
            'touser': open_id,
            'template_id': template_id,
            'page': page,
            'data': {"thing1": {"value": "制作结果"},
                     "character_string2": {"value": source_code},
                     "character_string3": {"value": order_id},
                     "time4": {"value": now.strftime('%Y-%m-%d %H:%M:%S')}},
            'miniprogram_state': miniprogram_state,
        }
        is_success, resp = self.send_subscribe_message(data)
        return is_success


if __name__ == '__main__':
    open_id = 'o-THh5De90Rdk0YNg_FLvg_KR-6U'
    # open_id = 'oXZGN6weh1jntM7JV-7_kpEhBk0Q'
    content = '你好'
    img_path = '/mnt/d/tmp.png'
    mp = MiniProgram()

    # mp.upload_img('/mnt/d/tmp.png')
    # mp.send_img(open_id, img_path)
    # mp.send_msg(open_id, content)
    title = '私人定制套餐'
    page_path = 'pages/mp-weixin/pay'
    mp.send_card_msessage(open_id, title, page_path, img_path)

    # source_code = '123'
    # order_id = '234'
    # miniprogram_state = 'trail'
    # mp.send_complete_subscribe_message(open_id, source_code, order_id, miniprogram_state=miniprogram_state)
