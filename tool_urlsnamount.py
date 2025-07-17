import zlib
import base64


def compress_data(url: str, sn: str, amount: str) -> str:
    """
    将URL、序列号和金额压缩并编码为Base64字符串

    参数:
        url (str): HTTPS回调地址
        sn (str): 序列号
        amount (str): 金额

    返回:
        str: 压缩并编码后的Base64字符串，长度不超过255个字符

    示例:
    >>> compressed = compress_data("https://example.com/callback", "SN12345", "100.00")
    >>> len(compressed) <= 255
    True
    >>> decompress_data(compressed)
    ('https://example.com/callback', 'SN12345', '100.00')
    """
    # 拼接数据并添加分隔符
    data = f"{url}|{sn}|{amount}"
    # 压缩数据
    compressed = zlib.compress(data.encode("utf-8"), level=9)
    # 编码为Base64
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
    return encoded


def decompress_data(base64_line: str) -> tuple[str, str, str]:
    """
    从Base64字符串解压并提取URL、序列号和金额

    参数:
        base64_line (str): 压缩并编码后的Base64字符串

    返回:
        tuple[str, str, str]: 解压后的URL、序列号和金额
    """
    # 解码Base64
    compressed = base64.urlsafe_b64decode(base64_line)
    # 解压数据
    data = zlib.decompress(compressed).decode("utf-8")
    # 分割数据
    url, sn, amount = data.split("|", 2)
    return url, sn, amount


if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))
