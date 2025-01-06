

class TokenExpire(Exception):
    """token失效"""
    code = 4010
    msg = "登陆信息已失效，请重新登陆"