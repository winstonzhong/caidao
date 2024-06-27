'''
Created on 2023年12月13日

@author: lenovo
'''
import re


ptn_pair = re.compile('[^:]+:[^:^\s]+')
ptn_device_info = re.compile('^([^\s]+)\s+[^\n]+device:([^\s]+)', re.M)



def parse_line_to_dict(line):
    '''
    >>> d = parse_line_to_dict('192.168.0.115:7002     device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:3')
    >>> d.get('id')
    '192.168.0.115:7002'
    >>> d.get('name')
    'HWALP'
    >>> d.get('offline')
    >>> parse_line_to_dict('192.168.0.190:7080     offline product:OCE-AN10 model:OCE_AN10 device:HWOCE-L transport_id:33').get('offline')
    True
    '''
    l = re.split('\s+', line)
    d = {'id':l[0]
        }
    for x in l[1:]:
        tmp = re.split(':', x,maxsplit=1)
        if len(tmp) == 2:
            d[tmp[0]] = tmp[1]
        elif tmp[0].strip() == 'offline':
            d['offline'] = True
    
    d['name'] = d.get('device')
    d['transport_id'] = int(d.get('transport_id'))
    
    return d
    
    
    
def parse_devices(txt):
    '''
    >>> list(parse_devices(txt0))
    []
    >>> l = list(parse_devices(txt1))
    >>> len(l) == 1
    True
    >>> l[0].get('id') 
    '192.168.0.115:7002'
    >>> l = list(parse_devices(txt2))
    >>> len(l) == 2
    True
    >>> l[0].get('id')
    'D3H7N18126007114'
    >>> l[1].get('id')
    '192.168.0.115:7002'
    >>> l[1].get('name')
    'HWALP'
    >>> l[1].get('transport_id')
    3
    >>> l[0].get('transport_id')
    5
    '''
    
    l = [x.strip() for x in txt.splitlines() if x.strip()]
    
    for line in l[1:]:
        yield parse_line_to_dict(line)
    
    # l = l[1:]
    # print(l)
    #
    # l = [re.split('\s+', x) for x in l]
    #
    # print(l)

if __name__ == '__main__':
    import doctest
    txt0 = 'List of devices attached\n'
    txt1 = 'List of devices attached\n192.168.0.115:7002     device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:3\n\n'
    txt2 = 'List of devices attached\nD3H7N18126007114       device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:5\n192.168.0.115:7002     device product:ALP-AL00 model:ALP_AL00 device:HWALP transport_id:3\n\n'
    print(doctest.testmod(verbose=False, report=False))
    # print(ptn_device_info.findall(txt1))
    # print(re.split('\s+', txt1))
    # parse_devices_new(txt1)
    
    
