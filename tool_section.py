'''
Created on 2023年4月24日

@author: lenovo
'''
def is_useless(sid1, direction1, point1, sid2, direction2, point2):
    '''
    >>> is_useless(0,1,2,1,1,1)
    False
    >>> is_useless(906,0,12,906,0,4.9)
    True
    >>> is_useless(906,0,4.9,906,0,12)
    False
    >>> is_useless(714,1,-5,714,1,-7)
    False
    >>> is_useless(714,1,-7,714,1,-5)
    True
    >>> is_useless(714,1,7,714,0,5)
    True
    >>> is_useless(714,0,7,714,1,5)
    False
    >>> is_useless(714,0,5,714,1,5)
    True
    >>> is_useless(714,1,5,714,0,7)
    False
    '''
    if sid1 != sid2:
        return False
    
    if direction1 == 0 and direction2 == 0 and point1 < point2:
        return False

    if direction1 == 1 and direction2 == 1 and point1 > point2:
        return False
            
    if direction1 > direction2 and point1 <  point2:
        return False

    if direction1 < direction2 and point1 >  point2:
        return False
            
    return True

    

if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))
    