"""
Redis 队列工具函数

提供 key_back 共享/独立判定及唯一化转换。
"""

import random
import time


def is_shared_key_back(key_back: str) -> bool:
    """
    判断 key_back 是否为共享返回队列。

    当前规则：外部显式传入的 key_back（非 None）视为共享队列（legacy 兼容模式）。
    函数内部自动生成的 key_back（None 时会重新生成）是唯一的，不共享。

    >>> is_shared_key_back("global_return_queue")
    True
    >>> is_shared_key_back(None)
    False
    """
    return key_back is not None


def ensure_unique_key_back(task_key: str, key_back: str = None) -> str:
    """
    确保返回的 key_back 是一个独立的回传队列名称。

    - 如果 key_back 为 None：按原有规则生成全新唯一队列。
    - 如果 key_back 是共享队列：在原 key 后追加时间戳和随机后缀，使其独立化。

    >>> result_none = ensure_unique_key_back("factor_generation", None)
    >>> result_none.startswith("factor_generation_return_")
    True
    >>> result_shared = ensure_unique_key_back("factor_generation", "global_queue")
    >>> result_shared.startswith("global_queue_")
    True
    >>> result_shared != "global_queue"
    True
    """
    ts = str(time.time())
    rand_suffix = random.randint(1000, 9999)

    if key_back is None:
        return f"{task_key}_return_{ts}_{rand_suffix}"

    if is_shared_key_back(key_back):
        return f"{key_back}_{ts}_{rand_suffix}"

    return key_back
