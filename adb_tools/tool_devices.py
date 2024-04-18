'''
Created on 2023年12月13日

@author: lenovo
'''
import re


ptn_pair = re.compile('[^:]+:[^:^\s]+')
ptn_device_info = re.compile('^([^\s]+)\s+[^\n]+device:([^\s]+)', re.M)

def parse_devices(txt):
    '''
    >>> list(parse_devices(txt0))
    []
    >>> list(parse_devices(txt1))
    [{'id': '192.168.0.115:7002', 'name': 'HWALP'}]
    >>> list(parse_devices(txt2))
    [{'id': 'D3H7N18126007114', 'name': 'HWALP'}, {'id': '192.168.0.115:7002', 'name': 'HWALP'}]
    '''
    for x in ptn_device_info.findall(txt):
        yield dict(zip(('id', 'name'), x))
    


if __name__ == '__main__':
    import doctest
    txt0 = 'List of devices attached\n'
    txt1 = 'List of devices attached\n192.168.0.115:7002     device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:3\n\n'
    txt2 = 'List of devices attached\nD3H7N18126007114       device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:5\n192.168.0.115:7002     device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:3\n\n'
    print(doctest.testmod(verbose=False, report=False))
