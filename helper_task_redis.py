import io
import json
import bz2
import redis
from typing import Any
import time
import os
import tool_env


# 全局Redis连接变量，初始化为None
REDIS_CONN = None

# print('=======================', os.getenv("REDIS_DB_INDEX_NUM"))

REDIS_DB_INDEX = int(os.getenv("REDIS_DB_INDEX_NUM", 15 if not tool_env.U4080 else 14))

print('=' *80)
print(f'using REDIS_DB_INDEX:{REDIS_DB_INDEX}, tool_env.U4080: {tool_env.U4080}')
print('=' *80)

def get_REDIS_CONN(max_retries=3):
    """
    获取Redis连接，如果连接不存在则创建，如果存在则检查有效性

    参数:
        max_retries: 连接检查的最大重试次数

    返回:
        有效的Redis连接对象

    异常:
        如果最终无法建立或验证连接，抛出异常
    """
    global REDIS_CONN

    # 如果连接不存在，则创建新连接
    if REDIS_CONN is None:
        REDIS_CONN = redis.Redis(
            host="192.168.0.140",  # Redis服务器地址
            port=6379,  # Redis端口
            db=REDIS_DB_INDEX,  # 使用的数据库编号
            password="Bubiebeng_1202",  # Redis密码
            decode_responses=True,  # 自动将字节转换为字符串
            socket_connect_timeout=5,  # 连接超时时间(秒)
            socket_timeout=None,  # 读写超时时间(秒)
        )

    # 检查连接是否有效
    retries = 0
    while retries < max_retries:
        try:
            if REDIS_CONN.ping():
                return REDIS_CONN
        except (redis.ConnectionError, redis.TimeoutError):
            retries += 1
            if retries < max_retries:
                time.sleep(1)  # 等待1秒后重试

    # 如果所有重试都失败，抛出异常
    raise Exception(f"经过{max_retries}次重试后，仍无法与Redis建立有效连接")


def 获取缓存任务(任务队列名称, 阻塞=False):
    if 阻塞:
        _, task_data = get_REDIS_CONN().blpop(任务队列名称)
    else:
        task_data = get_REDIS_CONN().lpop(任务队列名称)
    return json.loads(task_data) if task_data else {}


def 写任务到缓存(task_key: str, task_data: Any, expire_seconds: int = 1800) -> Any:
    """
    向Redis写入任务数据

    参数:
        task_key: 任务唯一标识键
        task_data: 任务数据（将被序列化为JSON）
        expire_seconds: 可选，任务过期时间（秒）

    返回:
        写入Redis的结果

    异常:
        当Redis连接失败或操作出错时抛出异常
    """

    result = get_REDIS_CONN().rpush(task_key, json.dumps(task_data))

    if expire_seconds and result:
        get_REDIS_CONN().expire(task_key, expire_seconds)
    return result


def 删除任务队列(task_key: str) -> int:
    """
    删除Redis中指定的key

    参数:
        task_key: 要删除的key名称

    返回:
        被删除的key的数量（1表示删除成功，0表示key不存在）
    """
    deleted_count = get_REDIS_CONN().delete(task_key)
    return deleted_count


def 获取队列中任务个数(task_key: str) -> int:
    """
    获取Redis中指定任务队列中的任务数量

    参数:
        task_key: 任务队列的键名

    返回:
        任务队列中的任务数量
    """
    return get_REDIS_CONN().llen(task_key)


def 队列中是否有任务(task_key: str) -> bool:
    return bool(get_REDIS_CONN().exists(task_key))

def 清空当前数据库():
    return REDIS_CONN.flushdb()


class Redis任务管理器(object):
    def __init__(self, host, port, db, password, task_key):
        self.con = redis.Redis(host=host, port=port, db=db, password=password)
        self.task_key = task_key

    def 推入Redis(self, d):
        buf = io.StringIO()
        json.dump(d, buf)
        data = buf.getvalue()
        data = bz2.compress(data.encode())
        self.con.lpush(self.task_key, data)

    def has_tasks(self):
        return len(self.con.lrange(self.task_key, 0, 0)) == 1

    def get_tasks_count(self):
        return len(self.con.lrange(self.task_key, 0, 1000))

    def clear_tasks(self):
        self.con.delete(self.task_key)

    def 拉出Redis(self):
        a = self.con.rpop(self.task_key)
        return json.loads(bz2.decompress(a)) if a is not None else None


class 跨进程共享变量控制锁(Redis任务管理器):
    def 获取锁(self):
        while True:
            if self.has_tasks():
                continue
            break
        self.推入Redis({})

    def 释放锁(self):
        self.clear_tasks()
