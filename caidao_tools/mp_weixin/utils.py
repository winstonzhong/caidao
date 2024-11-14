import requests
import datetime
import json


def get_mp_weixin_access_token(app_id, secret):
    """获取小程序access_token"""
    url = 'https://api.weixin.qq.com/cgi-bin/stable_token'
    data = {
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": secret
    }
    print(requests.post(url, json=data).json())
    return requests.post(url, json=data).json()['access_token']


def send_subscribe_message(access_token, data):
    '''
    发送订阅消息(小程序)
    :param data:  消息体。字典类型
    :param accessToken:  接入token
    :return:
    '''
    url = 'https://api.weixin.qq.com/cgi-bin/message/subscribe/send'
    data = json.dumps(data)
    params = {'access_token': access_token}
    r = requests.post(url, data=data, params=params)
    return r.json()


def push(app_id, secret, open_id):
    """推送订阅消息示例"""
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    now = now.strftime('%Y-%m-%d %H:%M:%S')
    access_token = get_mp_weixin_access_token(app_id, secret)
    data = {
        'touser': open_id,
        'template_id': 'OBb2mcqltiwq1f_LDGTmaN_jpEKozQlbWxx4LOg6OhY',
        'page': '/pages/mp-weixin/user/result',
        'data': {'thing1': {'value': '图片制作完成'}, 'thing3': {'value': '点击查看结果'}, 'time4': {'value': now}},
        'miniprogram_state': "trial"
    }
    send_subscribe_message(access_token, data)


def media_check(access_token, open_id, media_url, media_type, scene, version=2):
    """
    音视频内容安全识别接口
    参考: https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/sec-center/sec-check/mediaCheckAsync.html
    :param access_token: 接口调用凭证，该参数为 URL 参数，非 Body 参数
    :param open_id: 用户的openid（用户需在近两小时访问过小程序）
    :param media_url: 要检测的图片或音频的url，支持图片格式包括jpg, jepg, png, bmp, gif（取首帧），支持的音频格式包括mp3, aac, ac3, wma, flac, vorbis, opus, wav
    :param media_type: 1:音频;2:图片
    :param scene: 场景枚举值（1 资料；2 评论；3 论坛；4 社交日志）
    :param version: 接口版本号，2.0版本为固定值2
    :return:
    """
    url = f'https://api.weixin.qq.com/wxa/media_check_async?access_token={access_token}'
    body = {
        'openid': open_id,
        'media_url': media_url,
        'media_type': media_type,
        'version': version,
        'scene': scene
    }
    resp = requests.post(url, json=body)
    print(resp.json())
    return resp.json()


if __name__ == '__main__':
    access_token = get_mp_weixin_access_token('wx6c94a95d736f1969', '0d97072344c896e7473cc214a207e847')
    # print(access_token)
    # open_id = 'o-THh5De90Rdk0YNg_FLvg_KR-6U'
    # media_url = 'https://api.weixin.qq.com/cgi-bin/media/get?access_token=68_zu3BUC3x4heep3BBIl2Q2cx9QfWme_qi5dphSnAFJUrqsonGHHsC7iuFAmwMncH36sFYhHYr9JNQUQj2T2gc2Ls2f-iMUtsBxkt4HdkmckXfoiVnch4hVsRt0b4BKQhAFAJSY&media_id=56WWsf5nMlh5rrys9Lt_n0V1i0TQ7wwT_xk-1bx2vogSXJNTI6cWeEEZubgK7VDj'
    # media_type = 2
    # scene = 4
    #
    # media_check(access_token, open_id, media_url, media_type, scene)
