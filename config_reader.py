def read_config_from_string(config_str):
    """
    解析配置字符串，提取配置项、值和相关注释

    参数:
        config_str (str): 包含配置内容的多行字符串

    返回:
        dict: 包含配置信息的字典，结构为:
             {
                 'configs': {配置项: 值},
                 'comments': {配置项: 注释}
             }

    示例:
    >>> config_str = '''
    ... #adb 链接的手机的ip和端口号
    ... ip_port=192.168.0.190:7070
    ... #微信账号名称
    ... wx_name=我是小李医生
    ... '''.strip()
    >>> result = read_config_from_string(config_str)
    >>> result['configs']['ip_port']
    '192.168.0.190:7070'
    >>> result['configs']['wx_name']
    '我是小李医生'
    >>> result['comments']['ip_port']
    'adb 链接的手机的ip和端口号'

    >>> config_str = '''
    ... # 数据库配置
    ...
    ... db_host=localhost
    ...
    ... db_port=3306
    ... '''.strip()
    >>> result = read_config_from_string(config_str)
    >>> result['configs']['db_host']
    'localhost'
    >>> 'db_port' in result['comments']
    False

    >>> config_str = '''
    ... ip=127.0.0.1
    ... port=8080
    ... '''.strip()
    >>> result = read_config_from_string(config_str)
    >>> len(result['comments'])
    0

    >>> config_str = '''
    ... connection_string=server=localhost;db=test;pass=123=456
    ... '''.strip()
    >>> result = read_config_from_string(config_str)
    >>> result['configs']['connection_string']
    'server=localhost;db=test;pass=123=456'
    """
    config_data = {"configs": {}, "comments": {}}
    last_comment = None

    # 按行处理配置字符串
    for line in config_str.split("\n"):
        line = line.strip()

        if not line:  # 空行
            last_comment = None
            continue

        if line.startswith("#"):  # 注释行
            comment = line[1:].strip()
            if comment:  # 忽略空注释
                last_comment = comment
            continue

        if "=" in line:  # 配置项行
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            config_data["configs"][key] = value

            if last_comment is not None:
                config_data["comments"][key] = last_comment
                last_comment = None

    return config_data


def read_config_from_file(file_path):
    """
    从文件读取配置内容，调用read_config_from_string解析

    参数:
        file_path (str): 配置文件路径

    返回:
        dict: 同read_config_from_string的返回格式
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            config_str = file.read()
        return read_config_from_string(config_str)
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件不存在: {file_path}")
    except Exception as e:
        raise Exception(f"读取配置文件时出错: {str(e)}")


if __name__ == "__main__":
    # 运行所有doctest测试用例
    import doctest

    print(doctest.testmod(verbose=False, report=False))
