'''
Created on 2022年8月9日

@author: lenovo
'''

import time

import random

from cryptography.fernet import Fernet

import base64

import os

from tool_gzip import gzip_compress, gzip_decompress

class StrSecret(object):
    def __init__(self, key):
        '''
        >>> key = Fernet.generate_key()
        >>> e = StrSecret(key).encrypt(b'aaa')
        >>> StrSecret(key).decrypt(e)
        b'aaa'
        >>> eb = StrSecret(key).encrypt_to_base64(b'bbb')
        >>> StrSecret(key).decrypt_from_base64(eb)
        b'bbb'
        '''
        self.fn = Fernet(key)
    
    def encrypt(self, s):
        return self.fn.encrypt(gzip_compress(s))
    
    def encrypt_to_base64(self, s):
        return base64.b64encode(self.encrypt(s)).decode()

    def decrypt(self, s):
        return gzip_decompress(self.fn.decrypt(s))
    
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
