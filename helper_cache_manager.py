import pandas as pd

from typing import Dict, Protocol, TypeVar

T = TypeVar("T", bound="DataFrameProvider")


# 定义接口协议
class DataFrameProvider(Protocol):
    @property
    def id(self) -> int:  # 修改为int类型
        ...

    def get(self, key: int) -> pd.DataFrame:  # 修改为int类型
        ...


class DataFrameCacheManager:
    def __init__(self, max_memory_mb: int = 500):
        """
        初始化缓存管理器

        参数:
            max_memory_mb: 允许的最大内存使用量（MB），默认500MB
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024  # 转换为字节
        self.current_memory_bytes = 0

        # 缓存结构: {id: (DataFrame, 引用计数, 内存大小)}
        self.cache: Dict[int, tuple[pd.DataFrame, int, int]] = {}  # key类型改为int

    def get(self, obj: T) -> pd.DataFrame:
        """
        通过对象获取DataFrame

        参数:
            obj: 实现了id属性和get方法的对象

        返回:
            pd.DataFrame: 对应的DataFrame
        """
        df_id = obj.id

        # 检查缓存中是否存在
        if df_id in self.cache:
            df, count, size = self.cache[df_id]
            # 更新引用计数
            self.cache[df_id] = (df, count + 1, size)
            return df

        # 不存在则通过对象方法获取
        df = obj.get(df_id)
        # 计算内存使用
        df_size = self._get_df_memory_usage(df)

        # 检查是否需要清理缓存
        self._ensure_memory_limit(df_size)

        # 添加到缓存
        self.cache[df_id] = (df, 1, df_size)
        self.current_memory_bytes += df_size

        return df

    def _get_df_memory_usage(self, df: pd.DataFrame) -> int:
        """计算DataFrame的内存使用量（字节）"""
        return df.memory_usage(deep=True).sum()

    def _ensure_memory_limit(self, incoming_size: int) -> None:
        """
        确保添加新DataFrame后总内存不超过限制

        参数:
            incoming_size: 即将添加的DataFrame大小（字节）
        """
        # 如果添加后会超过限制，则需要清理
        while (
            self.current_memory_bytes + incoming_size > self.max_memory_bytes
            and self.cache
        ):
            # 找到引用计数最低的项
            min_count_id = min(self.cache, key=lambda k: self.cache[k][1])
            # 移除该项并释放内存
            _, _, size = self.cache.pop(min_count_id)
            self.current_memory_bytes -= size

    def get_stats(self) -> dict:
        """获取缓存状态统计信息"""
        return {
            "total_items": len(self.cache),
            "total_memory_mb": round(self.current_memory_bytes / (1024 * 1024), 2),
            "max_memory_mb": round(self.max_memory_bytes / (1024 * 1024), 2),
            "items": {
                str(df_id): {  # 将key转为字符串以便JSON序列化
                    "reference_count": count,
                    "memory_mb": round(size / (1024 * 1024), 2),
                }
                for df_id, (_, count, size) in self.cache.items()
            },
        }
