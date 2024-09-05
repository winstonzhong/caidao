'''
Created on 2024年5月29日

@author: lenovo
'''
import pandas

from tool_env import is_string
from tool_numpy import bin2array


def load_test_arr():
    with open('f:/tmp/test.arr', 'rb') as fp:
        return bin2array(fp.read()) 


def merge(df, left_on=1, right_on=0):
    df = pandas.merge(df, 
                       df, 
                       how='inner',
                       left_on=left_on,
                       right_on=right_on,
                       )

    columns =  {f'{i}_x':i for i in range(left_on)}
    columns[f'{left_on}_y'] = left_on+1
    
    return df.rename(columns=columns)[list(range(left_on+2))]

    return df.rename(columns={'0_x':0,
                              '1_x':1,
                              '2_x':2,
                              '3_y':4})[[0,1,2,3,4]]
    

def is_empty(a):
    return 0 in a.shape

def get_connected_simple(a):
    i = 0
    rtn = []
    tmp = a[0].tolist()
    while not is_empty(a):
        i = a[:,0] == tmp[-1]
        s = a[i]
        if is_empty(s):
            if len(tmp) > 2:
                rtn.append(tmp)
            a = a[1:]
            if is_empty(a):
                break
            tmp = a[0].tolist() 
        else:
            assert s.shape[0] == 1, s
            tmp.append(s[0].tolist()[-1])
            a = a[~i]
    
    if len(tmp) > 2 and tmp not in rtn:
        rtn.append(tmp)
    
    return rtn
            

def get_connected_by_pandas(a):
    df = pandas.DataFrame(a)
    
    i = 1
    rtn = []
    
    while 1:
        df = merge(df, i, i-1) 
        if df.empty:
            break
        rtn.append(df)
        i += 1
    return rtn
    

def test_pandas():
    r = load_test_arr()
    df = pandas.DataFrame(r)
    df1 = merge(df, 1, 0)
    return df, df1
    print(df1)
    
    df2 = merge(df1, 2, 1)
    print(df2)
    
    df1[(df1[0] != df2[0]) | (df1[1] != df2[1]) | (df1[2] != df2[2])]
    return df1, df2

    
    print(df2)

    
    df2 = df2.rename(columns={'0_x':0,
                              '1_x':1,
                              '2_y':3})[[0,1,2,3]]
    print(df2)
    df3 = merge(df2, 3, 2)

    print(df3)

    df3 = df3.rename(columns={'0_x':0,
                              '1_x':1,
                              '2_x':2,
                              '3_y':4})[[0,1,2,3,4]]
                              
    print(df3)

op_dict = {
        'gt':'>',
        'gte':'>=',
        'lt':'<',
        'lte':'<=',
        'isnull':'.isnull()==',
    }

def format_query(name, value):
    '''
    >>> format_query('x', 1)
    'df[df["x"]==1]'
    >>> format_query('x__gte', 1)
    'df[df["x"]>=1]'
    >>> format_query('x__isnull', True)
    'df[df["x"].isnull()==True]'
    >>> format_query('x__isnull', False)
    'df[df["x"].isnull()==False]'
    >>> format_query('x', '1')
    'df[df["x"]=="1"]'
    '''
    l = name.split('__')
    assert len(l) <= 2 and len(l) > 0
    op = '==' if len(l) == 1 else op_dict.get(l[1])
    name = l[0]
    if is_string(value):
        value = f'"{value}"'
    
    return f'''df[df["{name}"]{op}{value}]'''
     

def query_df(df, **k):
    '''
    >>> df = pandas.DataFrame([{'x':1, 'y':2, 'type':None},{'x':3, 'y':4, 'type':0}])
    >>> query_df(df, x=1)
       x  y  type
    0  1  2   NaN
    >>> query_df(df, type__isnull=False)
       x  y  type
    1  3  4   0.0
    >>> query_df(df, type__isnull=True)
       x  y  type
    0  1  2   NaN
    '''
    for name, value in k.items():
        exp = format_query(name, value)
        df = eval(exp)
    return df
    
    

if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
