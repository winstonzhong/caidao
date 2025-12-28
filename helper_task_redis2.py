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
    # host="192.168.0.140",
    # port=6379,
    # db=14,
    # password="Bubiebeng_1202",
    decode_responses=False,
    socket_connect_timeout=5,
    socket_timeout=None,
    max_connections=20,
    **config
)


class RedisTaskHandler:
    def __init__(
        self,
        pool,  # 接收外部传入的连接池（推荐）
        # host="192.168.0.140",
        # port=6379,
        # db=None,
        # password="Bubiebeng_1202",
        # decode_responses=False,
        # socket_connect_timeout=5,
        # socket_timeout=None,
        max_retries=3,
    ):
        # 初始化配置
        # self.db = db or int(os.getenv("REDIS_DB_INDEX_NUM", 15 if not tool_env.U4080 else 14))
        # self.db = db or 14
        # self.redis_config = {
        #     "host": host,
        #     "port": port,
        #     "db": self.db,
        #     "password": password,
        #     "decode_responses": decode_responses,
        #     "socket_connect_timeout": socket_connect_timeout,
        #     "socket_timeout": socket_timeout,
        # }
        self.pool = pool
        self.max_retries = max_retries
        # self._conn = None

    # @classmethod
    # def from_inner_json(cls):
    #     """
    #     {"host": "xxx", "port": 6379, "password": "xx", "db": 0}
    #     :return:
    #     """
    #     fpath = BASE_DIR / "queue_redis_json.cfg"
    #     with open(fpath, encoding="utf-8") as f:
    #         config = json.load(f)
    #     return cls(**config)

    # # 内部方法：获取/验证连接
    # def _get_conn(self):
    #     if self._conn is None:
    #         self._conn = redis.Redis(**self.redis_config)

    #     retries = 0
    #     while retries < self.max_retries:
    #         try:
    #             if self._conn.ping():
    #                 return self._conn
    #         except (redis.ConnectionError, redis.TimeoutError):
    #             retries += 1
    #             if retries < self.max_retries:
    #                 time.sleep(1)
    #     raise Exception(f"经过{self.max_retries}次重试后，仍无法与Redis建立有效连接")

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


    # def 推入数据队列(self, 数据: dict):
    #     return self.推入Redis("全局数据处理队列", 数据)

    # def 获取全局数据处理队列数据(self, 阻塞=False, 超时时间=0):
    #     return self.拉出Redis("全局数据处理队列", 阻塞=阻塞, 超时时间=超时时间)

    def 删除任务队列(self, task_key: str) -> int:
        return self._get_conn().delete(task_key)

    def 获取队列中任务个数(self, task_key: str) -> int:
        return self._get_conn().llen(task_key)

    def 队列中是否有任务(self, task_key: str) -> bool:
        return bool(self._get_conn().exists(task_key))

    def 清空当前数据库(self):
        return self._get_conn().flushdb()

    # def has_tasks(self, task_key):
    #     return len(self._get_conn().lrange(task_key, 0, 0)) == 1

    # def get_tasks_count(self, task_key):
    #     return self._get_conn().llen(task_key)  # 优化：用llen替代lrange，性能更好

    # def clear_tasks(self, task_key):
    #     self._get_conn().delete(task_key)

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
            _, task_data = r if r is not None else None, None
        else:
            task_data = self._get_conn().lpop(任务队列名称)
        if task_data is not None:
            return json.loads(bz2.decompress(task_data)) if task_data is not None else None

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
            return json.loads(bz2.decompress(task_data)) if task_data is not None else None

    # # 跨进程锁逻辑
    # def 获取锁(self, lock_key):
    #     while self.has_tasks(lock_key):
    #         continue
    #     self.推入Redis(lock_key, {})

    # def 释放锁(self, lock_key):
    #     self.clear_tasks(lock_key)

    def 获取锁(self, lock_key, expire_seconds=30):
        # 尝试设置锁，nx=True表示仅当key不存在时成功，ex设置过期时间防死锁
        return self._get_conn().set(lock_key, "locked", nx=True, ex=expire_seconds)

    def 释放锁(self, lock_key):
        self._get_conn().delete(lock_key)

GLOBAL_REDIS = RedisTaskHandler(pool=GLOBAL_POOL)

