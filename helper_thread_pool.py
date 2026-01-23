from concurrent.futures import ThreadPoolExecutor

"""
django中使用:
1. 在apps.py中注册关闭钩子
class YourAppConfig(AppConfig):
    name = 'your_app'

    def ready(self):
        # 注册退出钩子，确保应用关闭时关闭线程池
        atexit.register(shutdown_thread_pool)
        
2. 在使用的文件中引入THREAD_POOL


# 使用线程池提交任务（核心优化）
future = THREAD_POOL.submit(func, func_args)

# 可选：添加异常回调（避免线程池内异常静默）
def task_callback(fut):
    try:
        fut.result()  # 触发异常
    except Exception as e:
        logger.error(f"推送任务执行失败: {e}", exc_info=True)

future.add_done_callback(task_callback)


"""



# 全局线程池实例
THREAD_POOL = ThreadPoolExecutor(
    max_workers=5,
    thread_name_prefix="global_push_task_"
)


# 优雅关闭的辅助函数（在项目关闭时调用）
def shutdown_thread_pool():
    if THREAD_POOL:
        THREAD_POOL.shutdown(wait=True)




