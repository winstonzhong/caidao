"""
Created on 2024年7月24日

@author: lenovo
"""

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
    # keyname = '数据'
    
    def __init__(self, model_instance):
        '''
        :param model_instance:
        >>> pd = PropDictOfModel(DummyModel())
        >>> pd._model_instance is not None
        True
        >>> '_model_instance' in pd
        False
        '''
        super(PropDict, self).__setattr__('_model_instance', model_instance)
        self.update(model_instance.数据)

    def __setattr__(self, name, value):
        '''
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
        >>> pd.save()
        >>> dm.数据.get('ddd')
        [1, 2, 3]
        '''
        super().__setattr__(name, value)
        self.save()
    
    def save(self):
        self._model_instance.数据 = self.copy()
        self._model_instance.save()


if __name__ == "__main__":
    import doctest
    class DummyModel(object):
        def __init__(self):
            self.数据 = {'aaa':1, 'bbb':2}
        def save(self):
            pass

    print(doctest.testmod(verbose=False, report=False))
