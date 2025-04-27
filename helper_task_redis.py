import io
import json
import bz2
import redis


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
