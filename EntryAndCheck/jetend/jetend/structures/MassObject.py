# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------


class MassObject:
    inner2outer_map = None

    def __init__(self, **kwargs):
        pass

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

    @classmethod
    def write_columns_to_xls(cls, sheet, line: int):
        from xlwt.Worksheet import Worksheet
        assert isinstance(sheet, Worksheet), '{}'.format(type(sheet))
        col = 0
        for tag in cls.inner2outer_map:
            sheet.write(line, col, cls.inner2outer_map[tag])
            col += 1

    def write_content_to_xls(self, sheet, line: int):
        from datetime import date
        from xlwt.Worksheet import Worksheet
        assert isinstance(sheet, Worksheet), '{}'.format(type(sheet))
        col = 0
        for tag in self.inner2outer_map:
            value = getattr(self, tag)
            if isinstance(value, date):
                sheet.write(line, col, value.strftime('%Y%m%d'))
            elif isinstance(value, (float, int)):
                sheet.write(line, col, value)
            elif isinstance(value, str):
                sheet.write(line, col, value)
            elif value is None:
                sheet.write(line, col, '')
            else:
                raise TypeError('{} {}'.format(type(value), self))
            col += 1

    @classmethod
    def from_series(cls, pd_data):
        from pandas import Series
        assert isinstance(pd_data, Series), str(type(pd_data))
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
        return cls(**kw_dict)

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

    @classmethod
    def define_table(cls, meta):
        """define mapping table for sqlalchemy -> sqlalchemy.orm.Table"""
        raise NotImplementedError
