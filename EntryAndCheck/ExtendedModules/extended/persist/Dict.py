# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import os

from collections import Mapping, Sized

from extended.Interface import AbstractPersistObject
from extended.Interface import AbstractPersistStructure


class BasePersistDict(Mapping, Sized, AbstractPersistStructure):
    __postfix__ = None

    def __init__(self, path: str):
        Mapping.__init__(self)
        Sized.__init__(self)

        os.makedirs(path, exist_ok=True)
        self.__path__ = path

    def __iter__(self):
        return self.keys()

    def __getitem__(self, key: str):
        raise NotImplementedError

    def __setitem__(self, key: str, value):
        raise NotImplementedError

    def get(self, k: str, default=None):
        try:
            return self.__getitem__(k)
        except KeyError or FileNotFoundError:
            if default is None:
                raise KeyError
            else:
                return default

    def __keys__(self):
        return self.__list_path__()

    def __len__(self):
        return len(list(self.__keys__()))

    def to_dict(self):
        new_d = dict()
        for k, v in self.items():
            new_d[k] = v
        return new_d

    def keys(self):
        for key in self.__keys__():
            yield key

    def values(self):
        for key in self.__keys__():
            yield self.__getitem__(key)

    def items(self):
        for key in self.__keys__():
            yield key, self.__getitem__(key)

    def update(self, mapping):
        assert hasattr(mapping, 'items')
        for k, v in mapping.items():
            self.__setitem__(k, v)

    def to_object_dict(self):
        from extended.data.ObjectDict import ObjectDict
        new_d = ObjectDict()
        for k, v in self.items():
            new_d[k] = v
        return new_d


class TextDict(BasePersistDict):
    __postfix__ = 'txt'

    def __init__(self, path: str, encoding: str = 'utf-8'):
        BasePersistDict.__init__(self, path)

        self.__encoding__ = encoding

    def __setitem__(self, key: str, value):
        assert isinstance(value, str), 'TextDict value should be in type `str`.'
        full_key = self.__check_postfix__(key)
        with open(self.__sub_path__(full_key), mode='w', encoding=self.__encoding__) as f:
            f.write(value)

    def __getitem__(self, key: str):
        full_key = self.__check_postfix__(key)
        try:
            with open(self.__sub_path__(full_key), mode='r', encoding=self.__encoding__) as f:
                return f.read()
        except FileNotFoundError:
            raise KeyError('no such key as {}'.format(key))


class TextObjDict(TextDict):
    __postfix__ = None

    def __init__(self, path: str, obj_type: type, encoding: str = 'utf-8'):
        BasePersistDict.__init__(self, path)
        assert hasattr(obj_type, AbstractPersistObject.__get_state_attribute__)
        assert hasattr(obj_type, AbstractPersistObject.__set_state_attribute__)
        self.__obj_type__ = obj_type
        self.__encoding__ = encoding

    def __setitem__(self, key: str, value):
        assert isinstance(value, AbstractPersistObject)
        full_key = self.__check_postfix__(key)
        with open(self.__sub_path__(full_key), mode='w', encoding=self.__encoding__) as f:
            f.write(getattr(value, AbstractPersistObject.__get_state_attribute__).__call__())

    def __getitem__(self, key: str):
        full_key = self.__check_postfix__(key)
        try:
            with open(self.__sub_path__(full_key), mode='r', encoding=self.__encoding__) as f:
                return getattr(self.__obj_type__, AbstractPersistObject.__set_state_attribute__).__call__(f.read())
        except FileNotFoundError:
            raise KeyError('no such key as {}'.format(key))
