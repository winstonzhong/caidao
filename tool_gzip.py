'''
Created on 2022年5月8日

@author: winston
'''
from gzip import GzipFile
import io


def gzip_compress(raw_data):
    if raw_data:
        buf = io.BytesIO()
        with GzipFile(mode='wb', fileobj=buf) as fp:
            fp.write(raw_data)
        return buf.getvalue()


def gzip_decompress(raw_data):
    if raw_data:
        return GzipFile(mode='rb', fileobj=io.BytesIO(raw_data)).read()
