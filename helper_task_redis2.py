import io
import json
import bz2
import redis
from typing import Any
import time
import sys
# import os
import tool_env

from pathlib import Path


if getattr(sys, 'frozen', False):  # pyinstaller打包后的判断
    BASE_DIR = Path(sys.executable).parent / '_internal'
else:
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

    def 预览队列内容(self, task_key: str, count=10):
        """预览队列内容（不解压取出），返回解码后的数据列表"""
        try:
            items = self._get_conn().lrange(task_key, 0, count - 1)
            result = []
            for item in items:
                try:
                    # 尝试解压缩和解析JSON
                    result.append(json.loads(bz2.decompress(item)))
                except:
                    # 如果不是压缩数据，直接返回原始内容
                    result.append(item.decode() if isinstance(item, bytes) else item)
            return result
        except Exception as e:
            print(f"[Redis] 预览队列内容失败: {e}")
            return []

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

    def 提交字典到队列并阻塞等待结果(
        self,
        task_key: str,
        data_dict: dict,
        key_back: str = None,
        timeout: int = 300,
    ) -> dict:
        """
        通用队列任务提交函数 - 直接传入字典，支持多队列

        Args:
            task_key: 任务队列名称（如 "global_task_queue"）
            data_dict: 要提交的字典数据（直接传入，无需组装）
            key_back: 返回队列名称（可选，为空则自动生成）
            timeout: 拉取结果的超时时间（秒）

        Returns:
            dict: 包含结果的字典，失败返回空字典

        自动生成 key_back 规则:
            - 格式: "{task_key}_return_{timestamp}_{random}"
            - 保证每个队列有自己的回传队列，不会重复
        """
        import random

        # 1. 生成唯一 timestamp
        ts = str(time.time())

        # 2. 如果 key_back 为空，自动生成
        if key_back is None:
            rand_suffix = random.randint(1000, 9999)
            key_back = f"{task_key}_return_{ts}_{rand_suffix}"

        # 3. 将 timestamp 注入 data_dict（用于结果匹配）
        data_dict["timestamp"] = ts
        data_dict["key_back"] = key_back

        # 4. 推入 Redis
        self.推入Redis(task_key, data_dict)

        # 5. 循环拉取结果，比较 timestamp
        result = None
        while 1:
            d = self.拉出Redis(key_back, True, timeout)
            print("-" * 66)
            print("获取结果:")
            print(d)

            if not d:
                result = {}
                break
            if d.get("timestamp") != ts:
                print("丢弃前期废弃结果:", d)
                continue
            result = d
            break

        return result if result else {}

    def 提交数据并阻塞等待结果(
        self,
        key_back,
        sys_prompt=None,
        question=None,
        history=None,
        partial_content=None,
        timeout=300,
        **k,
    ):
        """
        提交数据到 global_task_queue 并阻塞等待结果（兼容旧接口）

        此函数保持向后兼容，内部调用新的通用函数 提交字典到队列并阻塞等待结果
        """
        task_key = "global_task_queue"

        # 组装数据字典
        data_dict = {
            "sys_prompt": sys_prompt,
            "question": question,
            "history": history,
            "partial_content": partial_content,
            **k,
        }

        # 调用新的通用函数
        d = self.提交字典到队列并阻塞等待结果(
            task_key=task_key,
            data_dict=data_dict,
            key_back=key_back,
            timeout=timeout,
        )

        # 处理 partial_content 的特殊逻辑（保持向后兼容）
        if d and d.get("result") and partial_content:
            d["result"] = json.loads(d["result"])

        return d

    def 测试服务可用性(self, timeout=10) -> dict:
        """
        测试"提交数据并阻塞等待结果"调用的服务可用性
        
        测试链路：
        1. Redis连接测试 - 验证连接池和ping
        2. 任务队列测试 - 验证推入/拉出功能
        3. Worker响应测试 - 提交测试任务，验证Worker是否响应
        
        Args:
            timeout: 等待Worker响应的超时时间（秒）
            
        Returns:
            {
                "整体状态": "可用" | "部分可用" | "不可用",
                "Redis连接": {"状态": "正常" | "异常", "详情": "..."},
                "任务队列": {"状态": "正常" | "异常", "详情": "..."},
                "Worker服务": {"状态": "正常" | "异常" | "无响应", "详情": "..."},
                "建议操作": "..."
            }
        """
        结果 = {
            "整体状态": "不可用",
            "Redis连接": {"状态": "待测试", "详情": ""},
            "任务队列": {"状态": "待测试", "详情": ""},
            "Worker服务": {"状态": "待测试", "详情": ""},
            "建议操作": ""
        }
        
        # 步骤1: 测试Redis连接
        try:
            conn = self._get_conn()
            if conn and conn.ping():
                结果["Redis连接"] = {"状态": "正常", "详情": "Redis连接池可用，ping成功"}
            else:
                结果["Redis连接"] = {"状态": "异常", "详情": "Redis ping失败"}
                结果["建议操作"] = "检查Redis服务是否启动: sudo systemctl status redis"
                return 结果
        except Exception as e:
            结果["Redis连接"] = {"状态": "异常", "详情": f"连接异常: {str(e)}"}
            结果["建议操作"] = "检查Redis配置和网络连接"
            return 结果
        
        # 步骤2: 测试任务队列
        try:
            测试键 = f"test_queue_{time.time()}"
            测试数据 = {"test": "data", "timestamp": time.time()}
            
            # 推入
            推入结果 = self.推入Redis(测试键, 测试数据, expire_seconds=60)
            # 拉出
            拉出数据 = self.拉出Redis(测试键, 阻塞=False)
            
            if 推入结果 and 拉出数据 and 拉出数据.get("test") == "data":
                结果["任务队列"] = {"状态": "正常", "详情": "推入/拉出功能正常"}
                # 清理
                self.删除任务队列(测试键)
            else:
                结果["任务队列"] = {"状态": "异常", "详情": "推入或拉出失败"}
                结果["建议操作"] = "检查Redis读写权限"
                return 结果
        except Exception as e:
            结果["任务队列"] = {"状态": "异常", "详情": f"队列操作异常: {str(e)}"}
            return 结果
        
        # 步骤3: 测试Worker响应
        try:
            测试键 = f"test_worker_{int(time.time() * 1000)}"
            
            print(f"\n[服务测试] 提交Worker测试任务，等待响应（超时{timeout}秒）...")
            
            # 提交测试任务（简单的echo任务）
            开始时间 = time.time()
            响应 = self.提交数据并阻塞等待结果(
                key_back=测试键,
                sys_prompt="你是一个简单的测试助手，收到测试请求请回复'pong'。",
                question="ping",
                timeout=timeout
            )
            耗时 = time.time() - 开始时间
            
            if 响应 and 响应.get("result"):
                结果["Worker服务"] = {
                    "状态": "正常", 
                    "详情": f"Worker响应正常，耗时{耗时:.2f}秒"
                }
                结果["整体状态"] = "可用"
            else:
                结果["Worker服务"] = {
                    "状态": "无响应", 
                    "详情": f"在{timeout}秒内未收到Worker响应"
                }
                结果["整体状态"] = "部分可用"
                结果["建议操作"] = "检查LLM Worker是否正常运行，或队列是否积压"
                
        except Exception as e:
            结果["Worker服务"] = {"状态": "异常", "详情": f"Worker测试异常: {str(e)}"}
            结果["整体状态"] = "部分可用"
            结果["建议操作"] = "检查Worker日志和队列状态"
        
        return 结果


GLOBAL_REDIS = RedisTaskHandler(pool=GLOBAL_POOL)
