'''
Created on 2022年8月9日

@author: lenovo
'''

import time

import random

from cryptography.fernet import Fernet

import base64

import os

class StrSecret(object):
    def __init__(self, key):
        '''
        >>> key = Fernet.generate_key()
        >>> e = StrSecret(key).encrypt('aaa')
        >>> StrSecret(key).decrypt(e)
        'aaa'
        >>> eb = StrSecret(key).encrypt_to_base64('bbb')
        >>> StrSecret(key).decrypt_from_base64(eb)
        'bbb'
        '''
        self.fn = Fernet(key)
    
    def encrypt(self, s):
        return self.fn.encrypt(s.encode())
    
    def encrypt_to_base64(self, s):
        return base64.b64encode(self.encrypt(s)).decode()

    def decrypt(self, s):
        s = self.fn.decrypt(s.encode() if type(s) == str else s)
        return s.decode()
    
    def decrypt_from_base64(self, s):
        return self.decrypt(base64.b64decode(s))


    @classmethod
    def gen_key(cls):
        random_bytes = os.urandom(24)
        base64_encoded = base64.urlsafe_b64encode(random_bytes)
        return base64_encoded

    

if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
