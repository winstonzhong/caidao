import itsdangerous


class TokenError(Exception):
    """token失效"""
    code = 4001
    msg = "" "登陆信息已失效"


salt = '!QAZ@WSX#EDC'  # 加盐
TOKEN = itsdangerous.JSONWebSignatureSerializer(salt)  # 不过期token，简化前端操作


def encode_token(**kwargs):
    res = TOKEN.dumps(kwargs)
    token = res.decode()  # 指定编码格式
    return token


def decode_token(token):
    try:
        res = TOKEN.loads(token)
        return res
    except:
        raise TokenError('token解析失败')
