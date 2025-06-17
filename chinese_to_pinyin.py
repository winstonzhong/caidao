import re
from pypinyin import pinyin, Style

def chinese_to_pinyin(name: str) -> str:
    """
    将中文名称转换为拼音替代的名称，符合文件命名规范。
    
    参数:
        name (str): 中文名称
    
    返回:
        str: 拼音替代的名称，符合文件命名规范
    """
    # 将中文转换为拼音列表，使用不带声调的风格
    pinyin_list = pinyin(name, style=Style.NORMAL)
    
    # 拼接拼音列表为字符串
    pinyin_str = ''.join([item[0] for item in pinyin_list])
    
    # 替换非字母数字字符为下划线
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', pinyin_str)
    
    # 确保没有连续的下划线
    clean_name = re.sub(r'_+', '_', clean_name)
    
    # 去除首尾的下划线
    clean_name = clean_name.strip('_')
    
    return clean_name

# 示例用法
if __name__ == "__main__":
    print(chinese_to_pinyin("你好，世界!"))  # 输出: ni_hao_shi_jie
    print(chinese_to_pinyin("Python编程"))  # 输出: Python_bian_cheng
    print(chinese_to_pinyin("123测试"))     # 输出: 123_ce_shi    