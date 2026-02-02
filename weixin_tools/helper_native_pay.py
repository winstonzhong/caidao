# wechat_core/utils.py
import time
import random
import hashlib
import jwt
from datetime import datetime, timedelta
import xmltodict
import json

# 1. JWT Token生成与解析
def generate_jwt_token(user_info, jwt_secret_key, jwt_expiration_delta):
    """生成登录JWT Token"""
    payload = {
        "user_id": user_info.get("unionid"),  # 用unionid作为用户唯一标识
        "exp": datetime.utcnow() + timedelta(seconds=jwt_secret_key)
    }
    token = jwt.encode(
        payload,
        jwt_expiration_delta,
        algorithm="HS256"
    )
    return token

def parse_jwt_token(token, jwt_secret_key):
    """解析JWT Token，返回用户信息"""
    try:
        payload = jwt.decode(
            token,
            jwt_secret_key,
            algorithms=["HS256"]
        )
        return {"status": "success", "data": payload}
    except jwt.ExpiredSignatureError:
        return {"status": "fail", "msg": "Token已过期"}
    except Exception as e:
        return {"status": "fail", "msg": f"Token解析失败：{str(e)}"}

# 2. 微信支付签名生成（API v2）
def generate_wechat_pay_sign(params, api_key):
    """生成微信支付签名（按ASCII排序，MD5加密）"""
    # 1. 排序参数
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    # 2. 拼接字符串
    sign_str = ""
    for key, value in sorted_params:
        if value and key != "sign":
            sign_str += f"{key}={value}&"
    # 3. 拼接API_KEY并加密
    sign_str += f"key={api_key}"
    sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()
    return sign

# 3. XML与字典互转（微信支付接口专用）
def dict_to_xml(params):
    """字典转XML"""
    xml_str = "<xml>"
    for key, value in params.items():
        xml_str += f"<{key}><![CDATA[{value}]]></{key}>"
    xml_str += "</xml>"
    return xml_str

def xml_to_dict(xml_data):
    """XML转字典"""
    try:
        dict_data = xmltodict.parse(xml_data)
        return dict_data.get("xml", {})
    except Exception as e:
        return {"status": "fail", "msg": f"XML解析失败：{str(e)}"}

# 4. 生成唯一订单号
def generate_order_no():
    """生成自有系统唯一订单号（格式：时间戳+随机数）"""
    timestamp = str(int(time.time()))
    random_str = str(random.randint(1000, 9999))
    return f"ORDER_{timestamp}_{random_str}"