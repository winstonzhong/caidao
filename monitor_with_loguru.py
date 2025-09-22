import time
from loguru import logger
from pathlib import Path


def monitor_functions(function_list, log_path="monitor.log", step=False):
    """
    无限循环监控函数列表，根据函数返回值决定是否休眠，带loguru日志功能

    参数:
        function_list: 包含多个函数的列表或元组，这些函数执行后返回True或None
        log_path: 日志文件路径，默认为"monitor.log"
    """
    # 验证输入参数
    assert isinstance(
        function_list, (list, tuple)
    ), f"{type(function_list)}不是列表或元组"
    for func in function_list:
        if not callable(func):
            raise TypeError("列表中的元素必须都是可调用的函数")

    # 确保日志目录存在
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 配置日志：循环日志(每天0点轮转，保留30天)
    logger.add(
        log_path,
        rotation="00:00",  # 每天0点创建新日志
        retention="30 days",  # 保留30天日志
        compression="zip",  # 压缩旧日志
        enqueue=True,  # 异步写入
        backtrace=True,  # 显示完整回溯
        diagnose=True,  # 显示变量值
        level="INFO",  # 最低日志级别
    )

    logger.info("监控函数启动")
    logger.info(f"监控的函数列表: {[func.__name__ for func in function_list]}")

    while True:
        has_true = False

        for func in function_list:
            try:
                result = func()
                if result is True:
                    logger.info(f"函数 {func.__name__} 执行结果: {result}")
                    has_true = True
                    break  # 遇到True立即跳出，无需执行后续函数

            except Exception as e:
                # 输出详细异常信息，包括堆栈跟踪
                logger.exception(f"函数 {func.__name__} 执行出错: {e}")

        if step:
            break

        if not has_true:
            time.sleep(1)
