'''
Created on 2024 Oct 27

@author: Winston
'''
import re


ptn_adb_connect_rtn = re.compile('.+\((\d+)\)')


def 得到ADB连接状态(t):
    '''
    >>> 得到ADB连接状态(('connected to 192.168.1.7:7080', ''))
    >>> 得到ADB连接状态(t1)
    10060
    >>> 得到ADB连接状态(t2)
    10061
    '''
    m = ptn_adb_connect_rtn.match(t[0])
    if m is None:
        return None
    return int(m.groups()[0])
    

def ADB连接是否成功(t):
    '''
    >>> ADB连接是否成功(('connected to 192.168.1.7:7080', ''))
    True
    >>> ADB连接是否成功(t1)
    False
    '''
    return 得到ADB连接状态(t) is None



if __name__ == "__main__":
    import doctest
    t1 = ('cannot connect to 192.168.1.17:7080: 由于连接方在一段时间后没有正确答复或连接的主机没有反应，连接尝试失败。 (10060)\n', '')
    t2 = ('cannot connect to 192.168.1.7:7080: 由于目标计算机积极拒绝，无法连接。 (10061)\n', '')
    print(doctest.testmod(verbose=False, report=False))
        