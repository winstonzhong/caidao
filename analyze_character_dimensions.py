import pandas as pd
import numpy as np


def analyze_character_dimensions(df):
    # 确保DataFrame包含必要的列
    required_columns = ['动作', 'mixamo关键词', 'shape']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"输入的DataFrame缺少必要的列: {required_columns}")

    df = df.copy()
    
    
    # 计算原始的高宽比
    df['height_to_width'] = df['shape'].apply(lambda x: x[0] / x[1] if x[1] > 0 else np.nan)
    
    # 判断高宽比是否正常
    ratio_normal = df.height_to_width > 1.2
    
    # 定义横向姿势关键词列表（导致shape翻转）
    horizontal_keywords = ['creep', 'crawl', '爬', '匍匐', '爬行']
    
    # 检查"动作"或"mixamo关键词"列中是否包含横向姿势关键词
    has_horizontal_keyword = (
        df['动作'].astype(str).str.contains('|'.join(horizontal_keywords), case=False) | 
        df['mixamo关键词'].astype(str).str.contains('|'.join(horizontal_keywords), case=False)
    )
    
    # 定义crouch和walk同时出现的关键词列表
    crouch_walk_keywords = ['crouch.*walk', 'walk.*crouch', '屈膝.*走', '走.*屈膝']
    
    # 检查"动作"或"mixamo关键词"列中是否包含crouch和walk组合关键词
    has_crouch_walk = (
        df['动作'].astype(str).str.contains('|'.join(crouch_walk_keywords), case=False) | 
        df['mixamo关键词'].astype(str).str.contains('|'.join(crouch_walk_keywords), case=False)
    )
    
    # 初始假设body_height为shape[0]
    df['body_height'] = df['shape'].apply(lambda x: x[0])
    df['body_width'] = df['shape'].apply(lambda x: x[1])
    
    # 标记可疑情况：高宽比异常且没有横向姿势关键词
    df['suspicious'] = ~ratio_normal & ~has_horizontal_keyword
    
    df.body_height = np.where(has_horizontal_keyword, df.body_width, df.body_height).astype(float)

    
    # 对crouch和walk同时出现的行，应用身高补偿（基于示例数据估算补偿比例为1.13）
    compensation_ratio = 1.13
    mask = has_crouch_walk | has_horizontal_keyword
    df.loc[mask, 'body_height'] = df.loc[mask, 'body_height'] * compensation_ratio
    s = df.body_height
    df['standard_height'] = s.loc[s.apply(lambda x:np.abs(s-x).sum().mean()).argmin()]
    
    # 移除临时列
    df = df.drop(columns=['height_to_width'], errors='ignore')
    
    return df

if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))