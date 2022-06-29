# -*- encoding: UTF-8 -*-
import pandas as pd

from utils import get_logger
from utils.Constants import *


class DataObject(object):
    inner2outer_map = dict()
    __data__ = None
    __env__ = None

    def __init__(self, *args, **kwargs):
        if self.__data__ is None:
            self.__data__ = dict()

    @property
    def log(self):
        log = self.__data__.get('log', None)
        if log is None:
            log = get_logger(self.__class__.__name__)
            self.log = log
        return log

    @log.setter
    def log(self, value):
        self.__data__.__setitem__('log', value)

    def get_attr(self, attr_tag: str):
        if attr_tag not in self.__data__:
            raise KeyError(attr_tag)
        return self.__data__.get(attr_tag)

    def set_attr(self, attr_tag: str, value):
        self.__data__.__setitem__(attr_tag, value)

    def __repr__(self):
        str_list = list()
        for key in self.inner2outer_map.keys():
            try:
                str_list.append('{}={}'.format(key, getattr(self, key)))
            except RecursionError as recur_error:
                print(type(self), key, '属性不存在')
                print(recur_error)
                raise RuntimeError()
            except NotImplementedError as n_e:
                print(key)
                raise n_e
        return self.__class__.__name__ + ': ' + ', '.join(str_list) + '; '

    @property
    def env(self):
        from core.Environment import Environment
        if DataObject.__env__ is None:
            DataObject.__env__ = Environment.get_instance()
        assert isinstance(DataObject.__env__, Environment)
        return DataObject.__env__

    @classmethod
    def init_from(cls, *args, **kwargs):
        """从其他数据生成该数据对象，默认生成方式来源于字典形式，其中字典的key是inner2outer中的outer key。"""

        if len(args) == 1:  # 输入为单个参数并且为字典类型的情况
            data = args[0]
            if isinstance(data, dict):
                return cls.from_dict(data)
            elif isinstance(data, pd.Series):
                return cls.from_series(data)
            else:
                raise NotImplementedError
        elif len(kwargs) > 0:
            return cls.from_parameters(**kwargs)
        else:
            raise NotImplementedError

    def init_property(self):
        raise NotImplementedError

    @classmethod
    def from_series(cls, pd_data: pd.Series):
        return cls.from_dict(pd_data.to_dict())

    @classmethod
    def from_dict(cls, dict_data):
        from collections import Mapping
        assert isinstance(dict_data, Mapping), 'dict_data should be Mapping object.'
        kw_dict = dict()
        outer2inner_map = cls.outer2inner_map()
        for key, value in dict_data.items():
            if key in outer2inner_map:
                kw_dict[outer2inner_map[key]] = value
            else:
                continue
                # raise KeyError('parameters has invalid key {}'.format(key))
        try:
            return cls(**kw_dict)
        except AttributeError:
            raise AttributeError(str(dict_data))

    @classmethod
    def from_parameters(cls, **kwargs):
        kw_dict = dict()
        outer2inner_map = cls.outer2inner_map()
        for key, value in kwargs.items():
            if key in outer2inner_map:
                kw_dict[outer2inner_map[key]] = value
            else:
                continue
                # raise KeyError('parameters has invalid key {}'.format(key))
        return cls(**kw_dict)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.inner2outer_map:
                raise KeyError('No such key as {}'.format(key))
            else:
                setattr(self, key, value)
        return self

    @classmethod
    def outer2inner_map(cls):
        o2i_dict = dict()
        for key, value in cls.inner2outer_map.items():
            o2i_dict[value] = key
        return o2i_dict

    def to_dict(self):
        o_dict = dict()
        for inner_k, outer_k in self.inner2outer_map.items():
            o_dict[outer_k] = getattr(self, inner_k)
        return o_dict

    def form_insert_sql(self, table_name: str):
        col_list, data_list = list(), list()
        for inner_key, outer_key in self.inner2outer_map.items():
            col_list.append(outer_key)
            cell = getattr(self, inner_key)
            if isinstance(cell, float):
                if not is_valid_float(cell):
                    data_list.append("null")
                else:
                    data_list.append(str(cell))
            elif isinstance(cell, int):
                data_list.append(str(cell))
            # elif isinstance(cell, str):
            #     if not is_valid_str(cell):
            #         data_list.append("null")
            #     else:
            #         data_list.append(cell)
            else:
                data_list.append("'{}'".format(cell))
        return 'INSERT INTO {} ({}) VALUES ({})'.format(table_name, ', '.join(col_list), ', '.join(data_list))

    @classmethod
    def inner_column_list(cls):
        return [var for var in cls.inner2outer_map.keys()]

    @classmethod
    def outer_column_list(cls):
        return [var for var in cls.inner2outer_map.values()]
