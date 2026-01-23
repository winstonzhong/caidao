import io
import json
import bz2
import redis
from typing import Any
import time

# import os
# import tool_env

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


with open(BASE_DIR / "queue_redis_json.cfg", encoding="utf-8") as f:
    config = json.load(f)


GLOBAL_POOL = redis.ConnectionPool(
    decode_responses=False,
    socket_connect_timeout=5,
    socket_timeout=None,
    max_connections=20,
    **config,
)


class RedisTaskHandler:
    def __init__(
        self,
        pool,  # 接收外部传入的连接池（推荐）
        max_retries=3,
    ):
        self.pool = pool
        self.max_retries = max_retries

    def _get_conn(self):
        """从连接池获取连接，每次调用都返回一个新的 Redis 实例（轻量操作）"""
        retries = 0
        while retries < self.max_retries:
            try:
                # 从连接池获取连接（Redis 实例会自动管理连接生命周期）
                conn = redis.Redis(connection_pool=self.pool)
                if conn.ping():  # 验证连接有效性
                    return conn
            except (redis.ConnectionError, redis.TimeoutError):
                retries += 1
                if retries < self.max_retries:
                    time.sleep(1)
        raise Exception(f"经过{self.max_retries}次重试后，仍无法与Redis建立有效连接")

    def 删除任务队列(self, task_key: str) -> int:
        return self._get_conn().delete(task_key)

    def 获取队列中任务个数(self, task_key: str) -> int:
        return self._get_conn().llen(task_key)

    def 队列中是否有任务(self, task_key: str) -> bool:
        return bool(self._get_conn().exists(task_key))

    def 清空当前数据库(self):
        return self._get_conn().flushdb()

    def 推入Redis(self, task_key: str, d: dict, expire_seconds=1800):
        data = json.dumps(d)
        data = bz2.compress(data.encode())
        result = self._get_conn().lpush(task_key, data)
        if expire_seconds and result:
            self._get_conn().expire(task_key, expire_seconds)
        return result

    def 拉出Redis(self, 任务队列名称, 阻塞=False, 超时时间=0):
        if 阻塞:
            r = self._get_conn().blpop(任务队列名称, timeout=超时时间)
            task_data = r[1] if r is not None else None
        else:
            task_data = self._get_conn().lpop(任务队列名称)
        if task_data is not None:
            return (
                json.loads(bz2.decompress(task_data)) if task_data is not None else None
            )

    def 设置Redis(self, task_key: str, d: dict, expire_seconds=1800):
        data = json.dumps(d)
        data = bz2.compress(data.encode())
        result = self._get_conn().set(task_key, data)
        if expire_seconds and result:
            self._get_conn().expire(task_key, expire_seconds)
        return result

    def 获取Redis(self, 任务队列名称):
        task_data = self._get_conn().get(任务队列名称)
        if task_data is not None:
            return (
                json.loads(bz2.decompress(task_data)) if task_data is not None else None
            )

    def 获取锁(self, lock_key, expire_seconds=30):
        # 尝试设置锁，nx=True表示仅当key不存在时成功，ex设置过期时间防死锁
        return self._get_conn().set(lock_key, "locked", nx=True, ex=expire_seconds)

    def 释放锁(self, lock_key):
        self._get_conn().delete(lock_key)

    # question=None,
    # sys_prompt=SYS_COMMON,
    # partial_content=None,
    # history=None,

    def 提交数据并阻塞等待结果(
        self,
        key_back,
        sys_prompt=None,
        question=None,
        history=None,
        partial_content=None,
        timeout=300,
    ):
        task_key = "global_task_queue"

        ts = str(time.time())
        d = {
            "sys_prompt": sys_prompt,
            "question": question,
            "history": history,
            "partial_content": partial_content,
            "key_back": key_back,
            "timestamp": ts,
        }
        self.推入Redis(task_key, d)

        # return self.拉出Redis(key_back, True, timeout)
        while 1:
            d = self.拉出Redis(key_back, True, timeout)
            print("-" * 66)
            print("获取结果:")
            print(d)

            if not d:
                break
            if d.get("timestamp") != ts:
                print("丢弃前期废弃结果:", d)
                continue
            break

        if d and d.get("result") and partial_content:
            d["result"] = json.loads(d["result"])

        return d


GLOBAL_REDIS = RedisTaskHandler(pool=GLOBAL_POOL)
