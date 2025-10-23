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

if __name__ == "__main__":
    import doctest

    print(doctest.testmod(verbose=False, report=False))
