"""
Created on 2024年7月24日

@author: lenovo
"""

import time

import pandas as pd

import io

import tool_wx_df5



class FixedLengthQueue(list):
    """
    从list继承的定长先入先出（FIFO）队列类。
    当队列达到设定的最大长度时，添加新元素会自动删除最早加入的元素。
    支持从现有list拷贝创建实例，超出长度时自动截断最早的元素。

    示例:
    >>> # 基础功能测试
    >>> q = FixedLengthQueue(max_length=3)
    >>> q.enqueue(1)
    >>> q.enqueue(2)
    >>> q.enqueue(3)
    >>> q  # 队列未满，正常添加所有元素
    [1, 2, 3]
    >>> q.enqueue(4)  # 队列已满，删除最早的1，添加4
    >>> q
    [2, 3, 4]
    >>> # 测试最大长度为1的边界场景
    >>> q2 = FixedLengthQueue(max_length=1)
    >>> q2.enqueue(10)
    >>> q2
    [10]
    >>> q2.enqueue(20)  # 满了之后替换唯一元素
    >>> q2
    [20]
    >>> # 从list拷贝创建实例的测试
    >>> # 场景1：初始list长度小于max_length
    >>> q3 = FixedLengthQueue(max_length=3, initial_data=[10, 20])
    >>> q3  # 完整保留所有元素
    [10, 20]
    >>> # 场景2：初始list长度等于max_length
    >>> q4 = FixedLengthQueue(max_length=3, initial_data=[1, 2, 3])
    >>> q4  # 完整保留
    [1, 2, 3]
    >>> # 场景3：初始list长度大于max_length（核心场景）
    >>> q5 = FixedLengthQueue(max_length=3, initial_data=[1, 2, 3, 4, 5])
    >>> q5  # 只保留最后3个元素（删除最早的1、2）
    [3, 4, 5]
    >>> # 场景4：从空list拷贝
    >>> q6 = FixedLengthQueue(max_length=2, initial_data=[])
    >>> q6.enqueue("a")
    >>> q6
    ['a']
    >>> # 拷贝后继续添加元素，验证逻辑一致性
    >>> q5.enqueue(6)
    >>> q5  # 原[3,4,5]满，删除3，添加6 → [4,5,6]
    [4, 5, 6]
    """

    def __init__(self, max_length, initial_data=None, model_instance=None):
        """
        初始化定长队列，支持从现有list拷贝初始数据

        参数:
            max_length (int): 队列的最大长度，必须为正整数
            initial_data (list, optional): 初始化队列的原始list，默认为空列表
        """
        super().__init__()  # 调用父类list的初始化方法
        # 校验最大长度合法性
        if not isinstance(max_length, int) or max_length <= 0:
            raise ValueError("max_length 必须是正整数")
        self.max_length = max_length  # 存储队列最大长度

        # 处理初始数据（从list拷贝）
        if initial_data is None:
            initial_data = []
        # 校验initial_data是否为list类型
        if not isinstance(initial_data, list):
            raise TypeError("initial_data 必须是list类型")

        # 核心逻辑：只保留initial_data的最后max_length个元素（符合FIFO定长规则）
        # 若initial_data长度≤max_length，直接全部添加；否则只加最后max_length个
        valid_data = initial_data[-self.max_length :] if len(initial_data) > 0 else []
        self.extend(valid_data)
        self._model_instance = model_instance

    def save(self):
        """
        保存数据到数据库
        """
        if self._model_instance:
            self._model_instance.save()

    def enqueue(self, item):
        """
        将元素加入队列（核心方法）
        - 队列未满：直接添加到队尾
        - 队列已满：删除队首（最早）元素，再添加新元素到队尾

        参数:
            item: 要加入队列的任意类型元素
        """
        # 队列已满时，删除最早加入的元素（list的pop(0)删除第一个元素）
        if len(self) >= self.max_length:
            self.pop(0)
        # 将新元素添加到队尾（符合FIFO规则）
        if item not in self:
            self.append(item)


class PropDict(dict):
    """
    >>> pd = PropDict()
    >>> pd.aaa = 1
    >>> pd.aaa
    1
    >>> pd.get('aaa') == 1
    True
    >>> pd = PropDict({'a':2,'b':4})
    >>> pd.a
    2
    >>> pd.get = 100
    >>> pd.get != 100
    True
    >>> pd['get'] == 100
    True
    >>> pd.bbb
    >>> pd.clear()
    >>> pd.aaa
    """

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        return self.get(name)


class PropDictOfModel(PropDict):
    def __init__(self, model_instance, 定长队列长度=100):
        """
        :param model_instance:
        >>> pd = PropDictOfModel(DummyModel())
        >>> pd._model_instance is not None
        True
        >>> '_model_instance' in pd
        False
        """
        super(PropDict, self).__setattr__("_model_instance", model_instance)
        self.update(model_instance.数据)
        self["定长队列"] = FixedLengthQueue(
            max_length=定长队列长度, initial_data=self.定长队列 or []
        )

    def 清空定长队列(self):
        """
        清空定长队列 的 Docstring

        :param self: 说明
        >>> pd = PropDictOfModel(DummyModel())
        >>> pd.入队(1)
        >>> pd.入队(1)
        >>> pd._model_instance.数据
        {'aaa': 1, 'bbb': 2, '定长队列': [1]}
        >>> pd.清空定长队列()
        >>> pd._model_instance.数据
        {'aaa': 1, 'bbb': 2, '定长队列': []}
        """
        self.定长队列.clear()
        self.save()

    def 入队(self, item):
        self.定长队列.enqueue(item)
        self.save()

    def __setattr__(self, name, value):
        """
        >>> dm = DummyModel()
        >>> dm.数据.get('aaa')
        1
        >>> pd = PropDictOfModel(dm)
        >>> pd.aaa = 2
        >>> pd.get('aaa') == 2
        True
        >>> dm.数据.get('aaa')
        2
        >>> pd.bbb
        2
        >>> pd.ccc
        >>> pd.aaa += 2
        >>> pd.aaa == 4
        True
        >>> _ = pd.setdefault('ddd', [1,2,3])
        >>> pd.ddd
        [1, 2, 3]
        >>> dm.数据.get('ddd')
        [1, 2, 3]
        """
        super().__setattr__(name, value)
        self.save()

    def pop(self, key, default=None):
        rtn = super().pop(key, default)
        self.save()
        return rtn

    def setdefault(self, key, default=None):
        need_save = key not in self
        rtn = super().setdefault(key, default)
        if need_save:
            self.save()
        return rtn

    def save(self):
        self._model_instance.数据 = self.copy()
        self._model_instance.save()


class 模型的定长先入先出队列(object):
    """
    从object继承的定长先入先出（FIFO）队列类。
    当队列达到设定的最大长度时，添加新元素会自动删除最早加入的元素。
    支持从现有list拷贝创建实例，超出长度时自动截断最早的元素。

    示例:
    >>> # 基础功能测试
    >>> q = 模型的定长先入先出队列(3, DummyModel(), '定长队列')
    >>> q.enqueue(1)
    >>> q.enqueue(2)
    >>> q.enqueue(3)
    >>> q.list  # 队列未满，正常添加所有元素
    [1, 2, 3]
    >>> q.enqueue(4)  # 队列已满，删除最早的1，添加4
    >>> q.list
    [2, 3, 4]
    >>> # 测试最大长度为1的边界场景
    >>> q2 = 模型的定长先入先出队列(1, DummyModel(), '定长队列')
    >>> q2.enqueue(10)
    >>> q2.list
    [10]
    >>> q2.enqueue(20)  # 满了之后替换唯一元素
    >>> q2.list
    [20]
    >>> # 场景2：初始list长度等于max_length
    >>> q4 = 模型的定长先入先出队列(4, q._model_instance, '定长队列')
    >>> q4.list
    [2, 3, 4]
    >>> q4._model_instance.数据.get('定长队列')
    [2, 3, 4]
    >>> q4.enqueue(5)
    >>> q4._model_instance.数据.get('定长队列')
    [2, 3, 4, 5]
    >>> q5 = 模型的定长先入先出队列(3, DummyModel(), '定长队列')
    >>> q5.enqueue({'aaa': 1})
    >>> q5.list[0].get('时间') > 0
    True
    """

    def __init__(self, max_length, model_instance, keyname):
        super().__init__()  # 调用父类list的初始化方法
        # 校验最大长度合法性
        if not isinstance(max_length, int) or max_length <= 0:
            raise ValueError("max_length 必须是正整数")
        self.max_length = max_length  # 存储队列最大长度
        self.keyname = keyname
        self._model_instance = model_instance

        # 校验initial_data是否为list类型
        if not isinstance(self.list, list):
            raise TypeError("initial_data 必须是list类型")

    @property
    def list(self):
        return self._model_instance.数据.setdefault(self.keyname, [])

    def save(self):
        """
        保存数据到数据库
        """
        if self._model_instance:
            self._model_instance.save()

    def enqueue(self, item):
        """
        将元素加入队列（核心方法）
        - 队列未满：直接添加到队尾
        - 队列已满：删除队首（最早）元素，再添加新元素到队尾

        参数:
            item: 要加入队列的任意类型元素
        """
        if item is None:
            return
        if len(self.list) >= self.max_length:
            self.list.pop(0)
        if item not in self.list:
            if isinstance(item, dict):
                item.update({"时间": int(time.time())})
            self.list.append(item)
        self.save()

    def clear(self):
        self.list.clear()
        self.save()

    def __contains__(self, item):
        """
        __contains__ 的 Docstring

        :param self: 说明
        :param item: 说明
        >>> q = 模型的定长先入先出队列(3, DummyModel(), '定长队列')
        >>> 1 in q
        False
        >>> q.enqueue(1)
        >>> 1 in q
        True
        >>> 2 in q
        False
        >>> len(q)
        1
        """
        return item in self.list

    def __len__(self):
        return len(self.list)

    @property
    def last(self):
        """
        获取队列中的最后一个元素
        """
        data = self.list
        return data[-1] if data else None


class 模型的便捷属性字典(object):
    def __init__(self, model_instance, 定长队列长度=100):
        """
        :param model_instance:
        >>> pd = 模型的便捷属性字典(DummyModel())
        >>> pd._model_instance is not None
        True
        >>> '_model_instance' in pd._model_instance.数据
        False
        """
        super().__setattr__("_model_instance", model_instance)
        定长队列 = 模型的定长先入先出队列(
            定长队列长度, model_instance, keyname="定长队列"
        )
        数据记录 = 模型的定长先入先出队列(5000, model_instance, keyname="数据记录")
        super().__setattr__("定长队列", 定长队列)
        super().__setattr__("数据记录", 数据记录)

    def __getattr__(self, name):
        return self._model_instance.数据.get(name)

    def __setattr__(self, name, value):
        """
        >>> dm = DummyModel()
        >>> dm.数据.get('aaa')
        1
        >>> pd = 模型的便捷属性字典(dm)
        >>> dm.数据
        {'aaa': 1, 'bbb': 2, '定长队列': [], '数据记录': []}
        >>> pd.定长队列.enqueue(1)
        >>> dm.数据
        {'aaa': 1, 'bbb': 2, '定长队列': [1], '数据记录': []}
        >>> pd.aaa = 2
        >>> dm.数据.get('aaa')
        2
        >>> pd.bbb
        2
        >>> pd.ccc
        >>> pd.aaa += 2
        >>> pd.aaa == 4
        True
        >>> _ = pd.setdefault('ddd', [1,2,3])
        >>> pd.ddd
        [1, 2, 3]
        >>> dm.数据.get('ddd')
        [1, 2, 3]
        """
        self._model_instance.数据[name] = value
        self.save()

    def pop(self, key, default=None):
        rtn = self._model_instance.数据.pop(key, default)
        self.save()
        return rtn

    def setdefault(self, key, default=None):
        need_save = key not in self._model_instance.数据
        rtn = self._model_instance.数据.setdefault(key, default)
        if need_save:
            self.save()
        return rtn

    def get(self, key, default=None):
        return self._model_instance.数据.get(key, default)

    def save(self):
        self._model_instance.save()

    def __getitem__(self, key):
        """重载 obj[key] 获取值的逻辑
        >>> dm = DummyModel()
        >>> pd = 模型的便捷属性字典(dm)
        >>> pd.aaa == pd['aaa']
        True
        """
        return self._model_instance.数据.get(key)

    def __setitem__(self, key, value):
        """重载 obj[key] = value 设置值的逻辑
        >>> dm = DummyModel()
        >>> pd = 模型的便捷属性字典(dm)
        >>> pd.aaa
        1
        >>> pd['aaa'] = 2
        >>> pd.aaa
        2
        >>> dm.数据.get('aaa')
        2
        """
        self._model_instance.数据[key] = value

    def get_session_df_manager(self, name):
        return 模型的会话管理器(self, name)


# class 模型的定长数据帧(pd.DataFrame):
#     # 定义元数据列表，保存自定义属性名，确保pandas操作后属性不丢失
#     _metadata = ["_mdict", "_key_name"]

#     def __init__(self, mdict, name):
#         self._name = name
#         try:
#             json_str = mdict.get(self._key_name)
#             df_data = (
#                 pd.read_json(io.StringIO(json_str)) if json_str else pd.DataFrame()
#             )
#         except KeyError as e:
#             raise KeyError(f"mdict中未找到key: {self._key_name}") from e
#         except Exception as e:
#             raise ValueError(f"JSON数据解析失败: {e}") from e
#         super().__init__(data=df_data)
#         self._mdict = mdict

#     @property
#     def _key_name(self):
#         return f"df__{self._name}"

#     # 可选：重写__finalize__方法，确保属性继承（pandas子类化规范）
#     def __finalize__(self, other, method=None, **kwargs):
#         """确保自定义属性在pandas操作（如切片）后传递给新对象"""
#         for name in self._metadata:
#             setattr(self, name, getattr(other, name, None))
#         return super().__finalize__(other, method=method, **kwargs)

#     def save(self):
#         self._mdict[self._key_name] = self.to_json()
#         self._mdict.save()

#     def 追加(self, df):
#         tool_wx_df5.合并上下两个df(self, df)


class 模型的会话管理器(object):
    def __init__(self, mdict, name):
        self.name = name
        try:
            json_str = mdict.get(self.key_name)
            self.df = (
                pd.read_json(io.StringIO(json_str)) if json_str else pd.DataFrame()
            )
        except KeyError as e:
            raise KeyError(f"mdict中未找到key: {self.key_name}") from e
        except Exception as e:
            raise ValueError(f"JSON数据解析失败: {e}") from e
        self.mdict = mdict

    @property
    def key_name(self):
        return f"df__{self.name}"

    def save(self):
        self.mdict[self.key_name] = self.df.to_json()
        self.mdict.save()

    def append(self, df):
        # print('----'* 5)
        容器key = df.容器key.iloc[0] if df.empty else None
        df, changed = tool_wx_df5.合并上下两个df(self.df, df)
        if changed:
            self.df = df

        # print(changed, 容器key)

        if 容器key is not None:
            tmp = df[((df.容器key != 容器key) | (~pd.isna(df.链接))) & (~df.已处理)]
            if not tmp.empty:
                df.loc[tmp.index, "已处理"] = True
                self.df = df
                changed = True

        if changed:
            # print('changed!!!!!!!!!!!!!!!')
            self.save()


if __name__ == "__main__":
    import doctest

    class DummyModel(object):
        def __init__(self):
            self.数据 = {"aaa": 1, "bbb": 2}

        def save(self):
            pass

    print(doctest.testmod(verbose=False, report=False))
