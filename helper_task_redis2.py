import io
import json
import bz2
import redis
from typing import Any
import time
import os
import tool_env


class RedisTaskHandler:
    def __init__(
            self,
            host="192.168.0.140",
            port=6379,
            db=None,
            password="Bubiebeng_1202",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=None,
            max_retries=3
    ):
        # 初始化配置
        # self.db = db or int(os.getenv("REDIS_DB_INDEX_NUM", 15 if not tool_env.U4080 else 14))
        self.db = db or 14
        self.redis_config = {
            "host": host,
            "port": port,
            "db": self.db,
            "password": password,
            "decode_responses": decode_responses,
            "socket_connect_timeout": socket_connect_timeout,
            "socket_timeout": socket_timeout
        }
        self.max_retries = max_retries
        self._conn = None

    # 内部方法：获取/验证连接
    def _get_conn(self):
        if self._conn is None:
            self._conn = redis.Redis(**self.redis_config)

        retries = 0
        while retries < self.max_retries:
            try:
                if self._conn.ping():
                    return self._conn
            except (redis.ConnectionError, redis.TimeoutError):
                retries += 1
                if retries < self.max_retries:
                    time.sleep(1)
        raise Exception(f"经过{self.max_retries}次重试后，仍无法与Redis建立有效连接")

    # ========== 原有函数改造为类方法 ==========
    def 获取缓存任务(self, 任务队列名称, 阻塞=False):
        if 阻塞:
            _, task_data = self._get_conn().blpop(任务队列名称)
        else:
            task_data = self._get_conn().lpop(任务队列名称)
        return json.loads(task_data) if task_data else {}

    def 写任务到缓存(self, task_key: str, task_data: Any, expire_seconds: int = 1800) -> Any:
        result = self._get_conn().rpush(task_key, json.dumps(task_data))
        if expire_seconds and result:
            self._get_conn().expire(task_key, expire_seconds)
        return result

    def 删除任务队列(self, task_key: str) -> int:
        return self._get_conn().delete(task_key)

    def 获取队列中任务个数(self, task_key: str) -> int:
        return self._get_conn().llen(task_key)

    def 队列中是否有任务(self, task_key: str) -> bool:
        return bool(self._get_conn().exists(task_key))

    def 清空当前数据库(self):
        return self._get_conn().flushdb()

    # ========== 原有Redis任务管理器/锁逻辑整合 ==========
    def 推入Redis(self, task_key, d):
        buf = io.StringIO()
        json.dump(d, buf)
        data = buf.getvalue()
        data = bz2.compress(data.encode())
        self._get_conn().lpush(task_key, data)

    def has_tasks(self, task_key):
        return len(self._get_conn().lrange(task_key, 0, 0)) == 1

    def get_tasks_count(self, task_key):
        return self._get_conn().llen(task_key)  # 优化：用llen替代lrange，性能更好

    def clear_tasks(self, task_key):
        self._get_conn().delete(task_key)

    def 拉出Redis(self, task_key):
        a = self._get_conn().rpop(task_key)
        return json.loads(bz2.decompress(a)) if a is not None else None

    # 跨进程锁逻辑
    def 获取锁(self, lock_key):
        while self.has_tasks(lock_key):
            continue
        self.推入Redis(lock_key, {})

    def 释放锁(self, lock_key):
        self.clear_tasks(lock_key)


# ========== 使用示例 ==========
if __name__ == "__main__":
    # 第一步：初始化一次连接参数
    redis_handler = RedisTaskHandler(
        host="192.168.0.100",
        port=6379,
        db=10,
        password="new_password"
    )
    # 后续调用所有方法无需传连接参数
    redis_handler.写任务到缓存("test_key", {"data": "test"})
    print(redis_handler.获取队列中任务个数("test_key"))
    redis_handler.获取锁("lock_key")
    redis_handler.释放锁("lock_key")