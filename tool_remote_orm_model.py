import requests


class RemoteModel:
    """
    >>> import requests
    >>> from unittest.mock import patch, MagicMock
    >>> mock_response = MagicMock()
    >>> mock_response.json.return_value = {'id': 1, 'name': 'Alice'}  # 无 'url' 键

    >>> # 测试初始化时设置常规属性（url/pk_name）不会触发递归
    >>> with patch('requests.get', return_value=mock_response):
    ...     obj = RemoteModel('https://api.example.com', pk_name='uid')
    ...     print(obj.url)          # 常规属性，直接访问
    ...     print(obj.pk_name)      # 常规属性，直接访问
    https://api.example.com
    uid

    >>> # 测试初始数据属性通过 __getattr__ 访问
    >>> with patch('requests.get', return_value=mock_response):
    ...     obj = RemoteModel('https://api.example.com')
    ...     print(obj.id)          # 初始数据属性，通过 __getattr__
    ...     print(obj.name)
    1
    Alice

    >>> # 测试设置常规属性不会污染 _initial_data
    >>> with patch('requests.get', return_value=mock_response):
    ...     obj = RemoteModel('https://api.example.com')
    ...     obj.url = 'new-url'    # 修改常规属性
    ...     print(obj.url)
    ...     print('url' in obj._initial_data)  # 初始数据中无 'url'
    new-url
    False
    >>> with patch('requests.get', return_value=mock_response):
    ...     obj = RemoteModel('https://api.example.com')
    >>> not obj.changed_data
    True
    >>> obj.is_empty()
    False
    >>> obj.due_time = 60
    >>> obj.changed_data == {'due_time': 60}
    True
    """

    def __init__(self, url, pk_name="id", **kwargs):
        # 先设置常规属性，此时 _initial_data 尚未创建
        super().__setattr__("url", url)
        super().__setattr__("pk_name", pk_name)
        super().__setattr__("changed_attr_names", set())

        # 最后设置 _initial_data
        response = requests.get(url, params=kwargs)
        response.raise_for_status()
        data = response.json()
        super().__setattr__("_initial_data", data)

    def __getattr__(self, name):
        if "_initial_data" in self.__dict__ and name in self._initial_data:
            return self._initial_data[name]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name, value):
        self.changed_attr_names.add(name)
        if "_initial_data" in self.__dict__ and name in self._initial_data:
            self._initial_data[name] = value
        else:
            super().__setattr__(name, value)

    @property
    def data(self):
        return self._initial_data

    def is_empty(self):
        return not bool(len(self._initial_data))

    @property
    def changed_data(self):
        # return {key: self._initial_data[key] for key in self.changed_attr_names}
        return {key: getattr(self, key) for key in self.changed_attr_names}

    def save(self):
        if not self.changed_data:
            print("no data changed")
            return

        pk_value = getattr(self, self.pk_name, None)
        if pk_value is None:
            raise ValueError(f"Primary key value for '{self.pk_name}' is not set.")

        payload = {"pk_name": self.pk_name, "pk_value": pk_value, **self.changed_data}
        response = requests.post(self.url, data=payload)
        response.raise_for_status()
        self.changed_data.clear()


if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
