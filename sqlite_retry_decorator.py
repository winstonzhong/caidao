import time
import logging
import asyncio
from functools import wraps
from django.db import OperationalError

logger = logging.getLogger(__name__)

def sqlite_retry(max_retries=3, base_delay=0.1, backoff_factor=2):
    """
    自动重试因SQLite数据库锁定导致的操作失败的装饰器
    
    参数:
        max_retries: 最大重试次数
        base_delay: 初始延迟时间(秒)
        backoff_factor: 延迟倍增因子
    """
    def decorator(view_func):
        # 同步视图处理
        if not asyncio.iscoroutinefunction(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                retries = 0
                while True:
                    try:
                        return view_func(request, *args, **kwargs)
                    except OperationalError as e:
                        if 'database is locked' not in str(e) or retries >= max_retries:
                            logger.error(f"数据库错误(非锁定或超出重试次数): {str(e)}")
                            raise
                        
                        logger.warning(f"捕获到数据库锁定异常: {str(e)}")
                        delay = base_delay * (backoff_factor ** retries)
                        logger.warning(
                            f"SQLite数据库锁定，将在{delay:.2f}秒后重试 (尝试 {retries + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        retries += 1
            return wrapper
        
        # 异步视图处理
        else:
            @wraps(view_func)
            async def async_wrapper(request, *args, **kwargs):
                retries = 0
                while True:
                    try:
                        return await view_func(request, *args, **kwargs)
                    except OperationalError as e:
                        if 'database is locked' not in str(e) or retries >= max_retries:
                            logger.error(f"数据库错误(非锁定或超出重试次数): {str(e)}")
                            raise
                        
                        logger.warning(f"捕获到数据库锁定异常: {str(e)}")
                        delay = base_delay * (backoff_factor ** retries)
                        logger.warning(
                            f"SQLite数据库锁定，将在{delay:.2f}秒后重试 (尝试 {retries + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        retries += 1
            return async_wrapper
    
    return decorator    