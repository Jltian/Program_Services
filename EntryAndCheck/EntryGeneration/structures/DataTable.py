# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import json

import pandas as pd

from collections.abc import Iterable, Sized


class DataList(Iterable, Sized):
    def __init__(self, d_type: type):
        super(DataList, self).__init__()
        self.data = list()
        self.__d_type__ = d_type

    def __repr__(self):
        # content = '[\n'
        # for value in self.data:
        #     content += '\t{}\n'.format(str(value))
        # content += '\n]'
        return '[\n{}\n] {}'.format('\n\t'.join([str(var) for var in self.data]), len(self))

    def __len__(self):
        return self.data.__len__()

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __setitem__(self, key, value):
        if isinstance(value, self.data_type):
            self.data[key] = value
        else:
            raise TypeError('value should be in type {}'.format(self.data_type))

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __iter__(self):
        return self.data.__iter__()

    @property
    def data_type(self):
        if self.__d_type__ is None:
            for value in self.data:
                if value is not None:
                    return type(value)
            return type(None)
        else:
            return self.__d_type__

    def append(self, value):
        if isinstance(value, self.data_type):
            self.data.append(value)
        else:
            print(type(value), self.data_type)
            raise TypeError('value should be in type {}'.format(self.data_type))

    def extend(self, v_list):
        for item in v_list:
            self.append(item)

    def to_list(self):
        new_l = list()
        for value in self.data:
            new_l.append(value)
        return new_l

    def to_pd(self):
        outer_column_list = self.data_type.outer_column_list()
        o2i_key_map = self.data_type.outer2inner_map()
        record_dict = dict()
        for outer_key in outer_column_list:
            inner_key = o2i_key_map[outer_key]
            column_list = list()
            for obj in self.data:
                column_list.append(getattr(obj, inner_key))
            record_dict[outer_key] = column_list
        result = pd.DataFrame.from_dict(record_dict)
        return result

    def to_csv(self, file_path: str, encoding='utf-8'):
        outer_column_list = self.data_type.outer_column_list()
        o2i_key_map = self.data_type.outer2inner_map()
        record_dict = dict()
        for outer_key in outer_column_list:
            inner_key = o2i_key_map[outer_key]
            column_list = list()
            for obj in self.data:
                try:
                    column_list.append(getattr(obj, inner_key))
                except RecursionError as e:
                    print(type(obj), inner_key)
                    raise RuntimeError(str(e))
                # try:
                #     column_list.append(getattr(obj, inner_key))
                # except NotImplementedError:
                #     column_list.append('NotImplemented')
            record_dict[outer_key] = column_list
        result = pd.DataFrame.from_dict(record_dict)
        result.to_csv(file_path, index=False, encoding=encoding)

    def to_str(self):
        return json.dumps([getattr(var, 'get_state').__call__() for var in self])

    @classmethod
    def from_str(cls, d_type: type, text: str):
        target_list = cls(d_type)
        text_list = json.loads(text)
        for value in text_list:
            target_list.append(getattr(d_type, 'set_state').__call__(value))
        return target_list

    @classmethod
    def from_pd(cls, d_type: type, dt: pd.DataFrame):
        target_list = cls(d_type)
        for i in dt.index:
            one_series = dt.iloc[i, ]
            assert hasattr(d_type, 'from_series')
            target_list.append(getattr(d_type, 'from_series').__call__(one_series))
        return target_list

    @classmethod
    def read_csv(cls, d_type: type, file_path: str):
        return cls.from_pd(d_type, pd.read_csv(file_path))

    def group_by(self, attr_tag: str):
        target_dict = dict()
        for value in self.data:
            attr_value = getattr(value, attr_tag)
            if attr_value not in target_dict:
                target_dict[attr_value] = DataList(self.data_type)
            target_dict[attr_value].append(value)
        return target_dict

    def trim_by_range(self, attr_tag: str, start_end, include_bound=(True, False)):
        assert isinstance(start_end, (list, tuple))
        assert isinstance(include_bound, (list, tuple)) and len(include_bound) == 2
        assert len(start_end) == 2 and start_end[0] <= start_end[1]
        target_list = DataList(self.data_type)
        for value in self.data:
            # from sheets.entry.Position import EntryPosition
            # if isinstance(value, EntryPosition):
            #     print(value.product, value.date, value.institution)
            if include_bound[0] is True and include_bound[1] is True:
                if start_end[0] <= getattr(value, attr_tag) <= start_end[1]:
                    target_list.append(value)
            elif include_bound[0] is True and include_bound[1] is False:
                if start_end[0] <= getattr(value, attr_tag) < start_end[1]:
                    target_list.append(value)
            elif include_bound[0] is False and include_bound[1] is True:
                if start_end[0] < getattr(value, attr_tag) <= start_end[1]:
                    target_list.append(value)
            elif include_bound[0] is False and include_bound[1] is False:
                if start_end[0] < getattr(value, attr_tag) < start_end[1]:
                    target_list.append(value)
            else:
                raise NotImplementedError
        return target_list

    def find_value_where(self, **kwargs):
        """
        find values by constrains -> DataList
        :param kwargs:
        :return: DataList, list of stored value
        """
        target_list = DataList(self.data_type)
        for value in self.data:
            confirm_list = list()
            for c_key, c_value in kwargs.items():
                confirm_list.append(getattr(value, c_key) == c_value)
            all_check = True
            for check in confirm_list:
                if check is False:
                    all_check = False
            if all_check is True:
                target_list.append(value)
        return target_list

    def find_value(self, **kwargs):
        target_list = DataList(self.data_type)
        for value in self.data:
            confirm_list = list()
            for c_key, c_value in kwargs.items():
                try:
                    confirm_list.append(getattr(value, c_key) == c_value)
                except Exception as some_error:
                    raise some_error
            all_check = True
            for check in confirm_list:
                if check is False:
                    all_check = False
            if all_check is True:
                target_list.append(value)
        if len(target_list) == 1:
            return target_list[0]
        if len(target_list) == 0:
            raise ValueError('No value satisfy {}\n{}'.format(kwargs, self))
        else:
            raise RuntimeError('Unknown Error {}'.format(str(target_list)))

    def collect_distinct_attr(self, attr: str):
        """collect distinct attr values -> set"""
        target_set = set()
        for value in self.data:
            target_set.add(getattr(value, attr))
        return target_set

    def map_attr(self, key_attr: str, value_attr: str):
        target_dict = dict()
        for value in self.data:
            target_dict[getattr(value, key_attr)] = getattr(value, value_attr)
        return target_dict

    def check_duplicated_attr(self, attr: str):
        """check whether no duplicated attr value exists -> bool"""
        target_set = set()
        for value in self.data:
            tag = getattr(value, attr)
            if tag in target_set:
                return False
            else:
                target_set.add(tag)
        return True

    def replace_attr_by(self, attr_key: str, attr_value):
        if isinstance(attr_value, dict):
            for value in self.data:
                tag = getattr(value, attr_key)
                if tag in attr_value:
                    setattr(value, attr_key, attr_value[tag])
                else:
                    pass
        else:
            for value in self.data:
                setattr(value, attr_key, attr_value)
        return self

    def sum_attr(self, attr_key: str):
        added = 0.0
        for value in self.data:
            added += getattr(value, attr_key)
        return added
