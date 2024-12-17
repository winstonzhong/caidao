'''
Created on 2022年5月8日

@author: winston
'''
from gzip import GzipFile
import io


def write_in_chunks(gzip_file, data, chunk_size=1024*1024):  # 1MB chunk size
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        gzip_file.write(chunk)

def gzip_compress(raw_data):
    if raw_data:
        buf = io.BytesIO()
        with GzipFile(mode='wb', fileobj=buf) as fp:
            write_in_chunks(fp, raw_data)
        return buf.getvalue()


def gzip_decompress(raw_data):
    if raw_data:
        return GzipFile(mode='rb', fileobj=io.BytesIO(raw_data)).read()
