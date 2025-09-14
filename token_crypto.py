import os
import time
from cryptography.fernet import Fernet, InvalidToken

# 获取全局token，测试时可替换为临时token
TOKEN = os.getenv("REDIS_TASKS_TOKEN")

# 初始化加密器
try:
    if not TOKEN:
        # 测试环境下生成临时token
        TOKEN = Fernet.generate_key().decode()
        print("使用临时测试token")
    cipher_suite = Fernet(TOKEN)
except Exception as e:
    raise RuntimeError(f"加密器初始化失败: {str(e)}")

def encrypt(s=None):
    """
    加密函数，使用全局token进行对称加密
    
    参数:
        s: 要加密的数据，默认为None时使用当前时间戳
    返回:
        加密后的字符串
    
    >>> # 测试加密时间戳
    >>> token = encrypt()
    >>> isinstance(token, str)
    True
    >>> len(token) > 0
    True
    
    >>> # 测试加密自定义字符串
    >>> secret = "test_string"
    >>> encrypted = encrypt(secret)
    >>> decrypted = cipher_suite.decrypt(encrypted.encode()).decode()
    >>> decrypted == secret
    True
    """
    # 如果s为None，则使用当前时间戳
    if s is None:
        s = time.time()
    
    # 将数据转换为字节串并加密
    data_bytes = str(s).encode('utf-8')
    encrypted_data = cipher_suite.encrypt(data_bytes)
    
    # 返回字符串形式的加密结果
    return encrypted_data.decode('utf-8')

def decrypt(s, base_time=None):
    """
    解密函数，使用全局token进行解密并验证时间
    
    参数:
        s: 要解密的字符串
        base_time: 基准时间，默认为None时使用当前时间
    返回:
        解密成功且时间差在60秒内返回True，否则返回False
    
    >>> # 测试正常解密（时间在60秒内）
    >>> current_time = time.time()
    >>> token = encrypt(current_time)
    >>> decrypt(token, current_time)
    True
    
    >>> # 测试时间差刚好60秒
    >>> token = encrypt(time.time() - 59)
    >>> decrypt(token)
    True
    
    >>> # 测试时间差超过60秒
    >>> token = encrypt(time.time() - 61)
    >>> decrypt(token)
    False
    
    >>> # 测试使用自定义基准时间
    >>> base = time.time()
    >>> token = encrypt(base - 30)
    >>> decrypt(token, base)
    True
    
    >>> # 测试无效token
    >>> decrypt("invalid_token")
    False
    
    >>> # 测试错误类型的输入
    >>> decrypt(12345)
    False
    """
    try:
        # 将字符串转换为字节串并解密
        encrypted_bytes = str(s).encode('utf-8')  # 确保输入被转换为字符串
        decrypted_bytes = cipher_suite.decrypt(encrypted_bytes)
        
        # 将解密结果转换为时间戳
        decrypted_time = float(decrypted_bytes.decode('utf-8'))
        
        # 确定基准时间
        current_time = base_time if base_time is not None else time.time()
        
        # 计算与基准时间的差值
        time_difference = abs(current_time - decrypted_time)
        
        # 检查时间差是否在60秒以内
        return time_difference <= 60
    
    except (InvalidToken, ValueError, TypeError, Exception):
        # 任何异常都返回False
        return False

if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))

