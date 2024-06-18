'''
Created on 2024年6月18日

@author: lenovo
'''
import pandas
import torch


def get_prob_df(l, inverse_ratio=False):
    df = pandas.DataFrame({'cnt':list(l)})
    df['tmp'] = df.cnt.sum() / df.cnt if inverse_ratio else df.cnt / df.cnt.sum()
    
    df['prob'] = torch.softmax(torch.tensor(df.tmp.to_numpy()), axis=0).numpy()
    
    df['bottom'] = df.prob.cumsum()
    df['top'] = df.bottom.shift(1).fillna(0)
    return df

def choose_by_prob(l, v, inverse_ratio=False):
    '''
    >>> choose_by_prob((2,3,4), 0.5, inverse_ratio=True) == 0
    True
    >>> choose_by_prob((2,3,4), 0, inverse_ratio=True) == 0
    True
    >>> choose_by_prob((2,3,4), 0.75, inverse_ratio=True) == 0
    True
    >>> choose_by_prob((2,3,4), 0.753, inverse_ratio=True) == 1
    True
    >>> choose_by_prob((2,3,4), 0.92, inverse_ratio=True) == 1
    True
    >>> choose_by_prob((2,3,4), 0.921, inverse_ratio=True) == 2
    True
    >>> choose_by_prob((2,3,4), 1, inverse_ratio=True) == 2
    True
    >>> choose_by_prob((4,), 1, inverse_ratio=True)
    0
    >>> choose_by_prob((4,), 0, inverse_ratio=True)
    0
    >>> choose_by_prob((4,), 0.6, inverse_ratio=True)
    0
    '''
    df = get_prob_df(l, inverse_ratio=inverse_ratio)
    return df[(v <= df.bottom) & (v >= df.top)].index[0]

if __name__ == '__main__':
    import doctest
    print(doctest.testmod(verbose=False, report=False))
