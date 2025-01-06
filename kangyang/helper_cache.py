from django.core.cache import cache

from kangyang.exceptions import TokenExpire

TOKEN_CACHE_TIMEOUT = 3600 * 24 * 30


def patient_login_cache(openid, app_id, token):
    key = "patient:mini:{0}:LoginCache:{1}".format(app_id, openid)
    cache.set(key, token, TOKEN_CACHE_TIMEOUT)


def get_patient_login_cache(openid, app_id):
    key = "patient:mini:{0}:LoginCache:{1}".format(app_id, openid)
    token = cache.get(key)
    if not token:
        raise TokenExpire
    return token


def delete_patient_login_cache(openid, app_id):
    key = "patient:mini:{0}:LoginCache:{1}".format(app_id, openid)
    cache.delete(key)
