'''
Created on 2022年8月9日

@author: lenovo
'''

import base64
import json

from cryptography.fernet import Fernet, InvalidToken


F = Fernet(b'x5ThDXyOi5twIV_4dmXz-efWK-sXzrc3QQeU3nsTRB0=')


def encrypt(b):
    return F.encrypt(b)

def decrypt(token):
    return F.decrypt(token)                            

def to_token(*a):
    return encrypt('\n'.join(a).encode('utf8'))

def from_token(token):
    try:
        return decrypt(token).decode('utf8').splitlines()
    except InvalidToken:
        pass

def to_name_passwd(token):
    p = from_token(token)
    if p is None or len(p) != 2:
        return None, None
    return p


def save_key(fpath_key, username, groupname):
    with open(fpath_key, 'wb') as fp:
        fp.write(to_token(username, groupname))


def load_key(fpath_key):
    username = groupname = None
    try:
        with open(fpath_key, 'rb') as fp:
            username, groupname = from_token(fp.read())
    except:
        pass
    return username, groupname

class JsonSecret(object):
    def __init__(self, key):
        self.fn = Fernet(key)
    
    def encrypt(self, d):
        s = json.dumps(d)
        return self.fn.encrypt(s.encode())
    
    def decrypt(self, s):
        s = self.fn.decrypt(s.encode() if type(s) == str else s)
        return json.loads(s.decode())    
    

if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
