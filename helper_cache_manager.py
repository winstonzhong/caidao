import pandas as pd

from typing import Callable, Dict


class DataFrameCacheManager:
    def __init__(
        self, df_factory: Callable[[str], pd.DataFrame], max_memory_mb: int = 500
    ):
        """
        初始化缓存管理器

        参数:
            df_factory: 创建DataFrame的工厂函数，接收id参数，返回DataFrame
            max_memory_mb: 允许的最大内存使用量（MB），默认500MB
        """
        self.df_factory = df_factory
        self.max_memory_bytes = max_memory_mb * 1024 * 1024  # 转换为字节
        self.current_memory_bytes = 0

        # 缓存结构: {id: (DataFrame, 引用计数, 内存大小)}
        self.cache: Dict[str, tuple[pd.DataFrame, int, int]] = {}

    def get(self, df_id: str) -> pd.DataFrame:
        """
        通过ID获取DataFrame

        参数:
            df_id: DataFrame的唯一标识

        返回:
            pd.DataFrame: 对应的DataFrame
        """
        # 检查缓存中是否存在
        if df_id in self.cache:
            df, count, size = self.cache[df_id]
            # 更新引用计数
            self.cache[df_id] = (df, count + 1, size)
            return df

        # 不存在则创建
        df = self.df_factory(df_id)
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
                df_id: {
                    "reference_count": count,
                    "memory_mb": round(size / (1024 * 1024), 2),
                }
                for df_id, (_, count, size) in self.cache.items()
            },
        }
