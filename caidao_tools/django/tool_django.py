'''
Created on 2024年5月21日

@author: lenovo
'''

subs = ('lt',
        'lte',
        'gt',
        'gte',
        'in',
        )

def is_field_filter(l, k):
    '''
    >>> is_field_filter(l_test, 'idd__qea__a')
    False
    >>> is_field_filter(l_test, 'idd')
    False
    >>> is_field_filter(l_test, 'id__gte')
    True
    '''
    r = k.rsplit('__', maxsplit=1)
    if len(r) == 2:
        f, sub = r
    else:
        f = r[0]
        sub = None
        
    if f not in l:
        return False
    
    if sub is not None and sub not in subs:
        return False
    
    return True
    

def get_filters(l, **d):
    '''
    >>> get_filters(l_test, id__lte=1, bins=2, bin=3)
    {'id__lte': 1, 'bin': 3}
    '''
    return {k:v for k,v in d.items() if is_field_filter(l, k)}    


if __name__ == '__main__':
    l_test = ['id',
     'bin',]
    import doctest
    print(doctest.testmod(verbose=False, report=False))

