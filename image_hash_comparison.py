import cv2
import numpy as np


def binary_to_hex(binary_str: str) -> str:
    """
    将由0和1组成的二进制字符串转换为十六进制字符串。

    参数:
        binary_str: 由0和1组成的二进制字符串。

    返回:
        对应的十六进制字符串，字母部分为大写，不带前缀"0x"。

    示例:
    >>> binary_to_hex('0000')
    '0'
    >>> binary_to_hex('1111')
    'F'
    >>> binary_to_hex('10101010')
    'AA'
    >>> binary_to_hex('00001111')
    'F'
    >>> binary_to_hex('11110000')
    'F0'
    >>> binary_to_hex('01010101')
    '55'
    >>> binary_to_hex('10000000')
    '80'
    >>> binary_to_hex('00000001')
    '1'
    >>> binary_to_hex('11111111')
    'FF'
    >>> binary_to_hex('00000000')
    '0'
    """
    # 检查输入是否只包含0和1
    if not all(c in {"0", "1"} for c in binary_str):
        raise ValueError("输入字符串必须只包含0和1")

    # 移除前导零，但至少保留一个字符
    binary_str = binary_str.lstrip("0") or "0"

    # 计算需要补零的位数，使二进制字符串长度是4的倍数
    padding = (4 - len(binary_str) % 4) % 4
    padded_binary = "0" * padding + binary_str

    # 转换为十六进制
    hex_str = hex(int(padded_binary, 2))[2:].upper()

    return hex_str


def compute_noise_robust_hash(img, block_size=8, hash_size=16):
    """
    计算对JPEG噪声鲁棒的图像哈希值
    同一图像的不同JPEG压缩版本将生成完全相同的哈希
    >>> get_hash('1750984821.5956340.8464') == get_hash('1750985101.8147630.9073')
    True
    >>> get_hash('1750984852.1473000.3871') == get_hash('1750985101.8147630.9073')
    False
    >>> get_hash('1750984852.1473000.3871') == get_hash('1750985110.3414990.7427')
    True
    """
    try:
        # 读取图像并进行预处理

        # 转为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 中值滤波去除椒盐噪声
        gray = cv2.medianBlur(gray, 3)

        # 调整亮度和对比度，减少JPEG压缩带来的差异
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

        # 缩放图像到固定大小
        img_size = hash_size * block_size
        resized = cv2.resize(gray, (img_size, img_size), interpolation=cv2.INTER_AREA)

        # 分块计算均值
        blocks = []
        for i in range(hash_size):
            for j in range(hash_size):
                block = resized[
                    i * block_size : (i + 1) * block_size,
                    j * block_size : (j + 1) * block_size,
                ]
                # 使用中位数而非均值，更能抵抗噪声
                median = np.median(block)
                blocks.append(median)

        # 计算全局中位数作为阈值
        global_median = np.median(blocks)

        # 生成二值哈希
        bits = [1 if block > global_median else 0 for block in blocks]

        return binary_to_hex("".join([str(bit) for bit in bits]))

    except Exception as e:
        print(f"计算哈希时出错: {e}")
        return None



if __name__ == "__main__":
    import doctest
    def get_hash(fname):
        return compute_noise_robust_hash(cv2.imread(f'/mnt/56T/file/2025-06-27/{fname}.jpg'))
    print(doctest.testmod(verbose=False, report=False))
