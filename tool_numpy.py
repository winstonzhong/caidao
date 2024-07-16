'''
Created on 2024年5月19日

@author: lenovo
'''

import io

import numpy as np
import pandas as pd


def bin2array(b):
    return np.load(io.BytesIO(b))['arr_0']
                
def array2bin(a):
    buffer = io.BytesIO()
    np.savez_compressed(buffer,a)
    return buffer.getvalue()

def array2file(a, fpath):
    with open(fpath, 'wb') as fp:
        fp.write(array2bin(a))
        
def file2array(fpath):
    with open(fpath, 'rb') as fp:
        return bin2array(fp.read())

def random_array():
    choices = [1, 2, 3, 4, 5, 6, 7, 8, 9, np.nan, np.nan, np.nan, np.nan, np.nan]
    out = np.random.choice(choices, size=(100, 100))
    return out

def loops_fill(arr):
    out = arr.copy()
    for row_idx in range(out.shape[0]):
        for col_idx in range(1, out.shape[1]):
            if np.isnan(out[row_idx, col_idx]):
                out[row_idx, col_idx] = out[row_idx, col_idx - 1]
    return out

def pandas_fill(arr):
    df = pd.DataFrame(arr)
    df.fillna(method='ffill', axis=1, inplace=True)
    out = df.to_numpy()
    return out

def numpy_fill(arr):
    mask = np.isnan(arr)
    idx = np.where(~mask,np.arange(mask.shape[1]),0)
    np.maximum.accumulate(idx,axis=1, out=idx)
    out = arr[np.arange(idx.shape[0])[:,None], idx]
    return out


def ffill(arr):
    mask = np.isnan(arr)
    idx = np.where(~mask, np.arange(mask.shape[1]), 0)
    np.maximum.accumulate(idx, axis=1, out=idx)
    out = arr[np.arange(idx.shape[0])[:,None], idx]
    return out

def bfill(arr):
    mask = np.isnan(arr)
    idx = np.where(~mask, np.arange(mask.shape[1]), mask.shape[1] - 1)
    idx = np.minimum.accumulate(idx[:, ::-1], axis=1)[:, ::-1]
    out = arr[np.arange(idx.shape[0])[:,None], idx]
    return out


def test_correct():
    a = random_array()
    print(a)
    print(loops_fill(a))
    print(pandas_fill(a))
    print(numpy_fill(a))
    print(ffill(a))

def test_speed():
    import timeit
    setup = '''from __main__ import loops_fill
from __main__ import random_array
from __main__ import pandas_fill
from __main__ import numpy_fill
from __main__ import ffill
'''
    
    print('loops_fill',timeit.timeit('loops_fill(random_array())', 
                        number=1000,
                        setup=setup,
                        ))
    
    print('pandas_fill',timeit.timeit('pandas_fill(random_array())', 
                        number=1000,
                        setup=setup,
                        ))
    
    print('numpy_fill',timeit.timeit('numpy_fill(random_array())', 
                        number=1000,
                        setup=setup,
                        ))

    print('ffill',timeit.timeit('ffill(random_array())', 
                        number=1000,
                        setup=setup,
                        ))

def test_split():
    # 固定窗口的切分
    arr = np.array(np.arange(100)).reshape(5,-1)
    window_size = 3
    indices = np.arange(arr.shape[0] - window_size + 1)  # 切分位置
    sub_arrays = np.array_split(arr, indices, axis=0)
    
    # 移动窗口的切分
    arr = np.array(np.arange(100)).reshape(5,-1)
    window_shape = (2, 2)  # 窗口大小
    window_view = np.lib.stride_tricks.as_strided(
        arr, 
        shape=(arr.shape[0] - window_shape[0] + 1, arr.shape[1] - window_shape[1] + 1) + window_shape, 
        strides=arr.strides + arr.strides)
    
    # print("固定窗口切分后的子数组：")
    # print(sub_arrays)
    # print("移动窗口切分后的视图：")
    # print(window_view)
    return arr, window_view

def test_split2(image):

    # image = np.random.rand(100, 350)
    
    window_height = 5
    window_width = 350
    stride_y = 1
    
    # 获取原始数组的 strides
    strides = image.strides
    
    # 计算新的 strides
    # new_strides = (strides[0], strides[1], strides[0], strides[1])
    
    new_strides = (strides[0], strides[0], strides[1])
    
    # shape=(100 - window_height + 1, window_width, window_height, window_width)
    
    shape=(100 - window_height + 1, window_height, window_width)
    # 使用 as_stride 函数进行移动窗口切片
    windows = np.lib.stride_tricks.as_strided(image, 
                                             shape=shape, 
                                             strides=new_strides)
    
    # print(windows.shape)
    return windows
    

if __name__ == "__main__":
    test_speed()
    # test_correct()

    