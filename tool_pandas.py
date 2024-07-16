'''
Created on 2024年5月29日

@author: lenovo
'''
import pandas

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
    # df['i'] = df.index
    
    # print(df[df[0].isin((32,36,37,39))])
    # return df
    
    # df1 = pandas.merge(df, 
    #                    df, 
    #                    how='inner',
    #                    left_on=1,
    #                    right_on=0,
    #                    )
    #
    # df1 = df1.rename(columns={'0_x':0,'1_y':2})[[0,1,2]]
    #
    # print(df1)
    df1 = merge(df, 1, 0)
    return df, df1
    print(df1)
    
    df2 = merge(df1, 2, 1)
    print(df2)
    
    df1[(df1[0] != df2[0]) | (df1[1] != df2[1]) | (df1[2] != df2[2])]
    return df1, df2

    #     0   1
    # 3  32  36
    # 4  36  37
    # 5  37  39
    #         0     1     2
    # 0      32    36    37
    # 1      36    37    39
    # 2      67    68    71
    # 3      87    88    89
    # 4     113   114   115
    # ..    ...   ...   ...
    # 157  1162  1164  1165
    # 158  1164  1165  1166
    # 159  1174  1175  1179
    # 160  1175  1179  1183
    # 161  1203  1206  1207
    
    #        2   0_x   1_x   2_x   0_y   1_y   2_y
    # 0     37    32    36    37    36    37    39
    # 1    202   194   198   202   198   202   206
    # 2    255   247   248   255   248   255   256
    # 3    260   258   259   260   259   260   261
    # 4    338   335   337   338   337   338   339
    # ..   ...   ...   ...   ...   ...   ...   ...
    # 76  1063  1056  1057  1063  1057  1063  1064
    # 77  1093  1091  1092  1093  1092  1093  1094
    # 78  1154  1148  1150  1154  1150  1154  1158
    # 79  1165  1162  1164  1165  1164  1165  1166
    # 80  1179  1174  1175  1179  1175  1179  1183
    
    #        0     1     2     3
    # 0     32    36    37    39
    # 1    194   198   202   206
    # 2    247   248   255   256
    # 3    258   259   260   261
    # 4    335   337   338   339
    # ..   ...   ...   ...   ...
    # 76  1056  1057  1063  1064
    # 77  1091  1092  1093  1094
    # 78  1148  1150  1154  1158
    # 79  1162  1164  1165  1166
    # 80  1174  1175  1179  1183    
    
    print(df2)
    # return

    
    df2 = df2.rename(columns={'0_x':0,
                              '1_x':1,
                              '2_y':3})[[0,1,2,3]]
    print(df2)
    # return
    
    df3 = merge(df2, 3, 2)

    print(df3)

    df3 = df3.rename(columns={'0_x':0,
                              '1_x':1,
                              '2_x':2,
                              '3_y':4})[[0,1,2,3,4]]
                              
    print(df3)
    

if __name__ == "__main__":
    print(test_pandas())
