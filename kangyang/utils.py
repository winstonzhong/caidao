import time

from kangyang.helper_cache import patient_login_cache
from kangyang.make_token import encode_token

PATIENT_MINI_TYPE = 1
PATIENT_APP_TYPE = 2


def get_token(store_data):
    token_info = store_data.get('authorization') or store_data.get('cookie')
    if token_info:
        return token_info[1].split('=')[1]


def get_token_new(store_data):
    token_info = store_data.get('authorization') or store_data.get('cookie')
    if token_info:
        return token_info.split('=')[1]

def get_user_id(user):
    user_id = ''
    if 'doctorID' in user.keys():
        user_id = user['doctorID']
    elif 'uuid' in user.keys():
        user_id = user['uuid']
    return user_id


def patient_login_token(open_id, app_id, uuid, patient_id):
    token = encode_token(open_id=open_id, app_id=app_id, uuid=uuid, patient_id=patient_id, create_time=time.time(),
                         ctype=PATIENT_MINI_TYPE)
    patient_login_cache(open_id, app_id, token)
    return token
