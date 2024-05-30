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
    return pandas.merge(df, 
                       df, 
                       how='inner',
                       left_on=left_on,
                       right_on=right_on,
                       )
    

def test_pandas():
    r = load_test_arr()
    df = pandas.DataFrame(r)
    # df['i'] = df.index
    
    print(df[df[0].isin((32,36,37,39))])
    # return df
    
    df1 = pandas.merge(df, 
                       df, 
                       how='inner',
                       left_on=1,
                       right_on=0,
                       )
    
    df1 = df1.rename(columns={'0_x':0,'1_y':3})[[0,1,3]]

    print(df1)
    
    df2 = merge(df1, 3, 1)

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


    #        3   0_x   1_x   3_x   0_y   1_y   3_y
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
    
    df1 = df1.rename(columns={'0_x':0,
                              '1_x':1,
                              '3_y':2})[[0,1,3]]
    print(df2)
    return
    
    # print(df1)
    
    # return df, df1
    # left = df[(~df.i.isin(df1.i_x))&(~df.i.isin(df1.i_y))]
    # print(df)
    
    # return df, df1
    
    df1 = df1.rename(columns={'1_y':3, 1:2})
    
    return df1
    
    df2 = pandas.merge(df, 
                       df1, 
                       how='inner',
                       left_on=0,
                       right_on='key',
                       )
    
    # print(df1)
    return df2
    

if __name__ == "__main__":
    print(test_pandas())
