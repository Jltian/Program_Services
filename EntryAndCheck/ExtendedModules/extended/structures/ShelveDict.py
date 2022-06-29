# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import os
import logging
import shelve

from collections.abc import Mapping, Sized


class ShelveDict(Mapping, Sized):

    def __init__(self, db_path: str, writeback: bool=False, new: bool=False):
        self.__logger__ = logging.getLogger(self.__class__.__name__)
        self.__closed_tag__ = False   # tag whether db is closed

        if '.' in db_path:
            if db_path.split('.')[-1] == 'db':
                self.__path__ = db_path
            else:
                self.__path__ = '.'.join([db_path, 'db'])
        else:
            self.__path__ = '.'.join([db_path, 'db'])

        if os.path.exists(self.__path__):
            if new is True:
                os.remove(self.__path__)
            self.__db__ = shelve.open(self.__path__, writeback=writeback, protocol=None)
        else:
            if new is False:
                raise FileNotFoundError(self.__path__)
            self.__db__ = shelve.open(self.__path__, writeback=writeback, protocol=None)

        self.__logger__.info('Connected to shelve database {}'.format(self.__path__))

    @classmethod
    def init_from(cls, data, db_path: str, writeback=False):
        if data is None:
            new_db = cls(db_path=db_path, writeback=writeback, new=True)
        elif isinstance(data, Mapping):
            new_db = cls(db_path=db_path, writeback=writeback, new=True)
            for k, v in data.items():
                new_db[k] = v
        else:
            raise NotImplementedError
        return new_db

    @classmethod
    def connect(cls, db_path: str, writeback=False):
        return cls(db_path=db_path, writeback=writeback)

    def __iter__(self):
        for key in self.keys():
            yield key

    def __getitem__(self, key: str):
        return self.__db__[key]

    def __setitem__(self, key: str, data):
        self.__db__[key] = data
        self.__closed_tag__ = False

    def __contains__(self, key: str):
        return self.__db__.__contains__(key)

    def __delitem__(self, key):
        del self.__db__[key]
        self.__closed_tag__ = False

    def __len__(self):
        return self.__db__.__len__()

    def keys(self):
        return self.__db__.keys()

    def values(self):
        return self.__db__.values()

    def items(self):
        return self.__db__.items()

    def set(self, key: str, data):
        self.__setitem__(key, data)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def flush(self):
        self.__db__.sync()
        self.__closed_tag__ = False

    def clear(self):
        self.__db__.clear()
        self.__closed_tag__ = False
        self.__logger__.info('shelve database {} cleared.'.format(self.__path__))

    def close(self):
        self.__db__.close()
        self.__closed_tag__ = True
        self.__logger__.info('shelve database {} closed.'.format(self.__path__))

    def delete(self):
        from os import remove
        self.__db__.clear()
        self.__db__.close()
        self.__closed_tag__ = True
        remove(self.__path__)

    @property
    def is_active(self):
        return not self.__closed_tag__

    def to_list(self):
        return [var for var in self.values()]

    def to_dict(self, key_range=None):
        new_d = dict()
        if key_range is None:
            for key, value in self.items():
                new_d[key] = value
        else:
            for key, value in self.items():
                if key in key_range:
                    new_d[key] = value
        return new_d

    def update(self, data):
        from collections import Mapping
        if isinstance(data, Mapping):
            for key, value in data.items():
                self.__setitem__(key, value)
        else:
            raise NotImplementedError


if __name__ == '__main__':
    pass
