# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------


class DictObject(dict):

    def __repr__(self):
        str_list = list()
        for key, value in self.items():
            str_list.append('{}={}'.format(key, value))
        return self.__class__.__name__ + ': ' + ', '.join(str_list) + '; '

    @classmethod
    def from_series(cls, pd_data):
        from pandas import Series
        if isinstance(pd_data, Series):
            return cls.from_dict(pd_data.to_dict())
        else:
            from extended.Exceptions import ParamTypeError
            raise ParamTypeError('pd_data', 'pandas.Series', pd_data)

    @classmethod
    def from_dict(cls, dict_data):
        return cls(**dict_data)


class AbstractDataObject:
    inner2outer_map = None

    @classmethod
    def outer2inner_map(cls):
        assert isinstance(cls.inner2outer_map, dict), '{}.inner2outer_map not defined properly.'.format(cls.__name__)
        o2i_dict = dict()
        for key, value in cls.inner2outer_map.items():
            o2i_dict[value] = key
        return o2i_dict

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
    def from_series(cls, pd_data):
        from pandas import Series
        if isinstance(pd_data, Series):
            return cls.from_outer_dict(pd_data.to_dict())
        else:
            from extended.Exceptions import ParamTypeError
            raise ParamTypeError('pd_data', 'pandas.Series', pd_data)

    @classmethod
    def from_outer_dict(cls, dict_data):
        kw_dict = dict()
        outer2inner_map = cls.outer2inner_map()
        for key, value in dict_data.items():
            if key in outer2inner_map:
                kw_dict[outer2inner_map[key]] = value
            else:
                continue
        return cls(**kw_dict)

    @classmethod
    def from_dict(cls, dict_data: dict):
        return cls(**dict_data)

    def to_dict(self):
        o_dict = dict()
        for inner_k in self.inner2outer_map.keys():
            o_dict[inner_k] = getattr(self, inner_k)
        return o_dict

    def to_outer_dict(self):
        o_dict = dict()
        for inner_k, outer_k in self.inner2outer_map.items():
            o_dict[outer_k] = getattr(self, inner_k)
        return o_dict


class AttributeObject(AbstractDataObject):

    def __init__(self, **kwargs):
        AbstractDataObject.__init__(self)
        self.__dict__.update(kwargs)

    def __repr__(self):
        str_list = list()
        for key in self.inner2outer_map.keys():
            try:
                str_list.append('{}={}'.format(key, getattr(self, key)))
            except RecursionError as recur_error:
                print(type(self), key, '属性不存在')
                print(recur_error)
                raise RuntimeError(self.__dict__)
            except NotImplementedError as n_e:
                print(key, type(self))
                raise n_e
            except AttributeError as a_e:
                print(self.__dict__)
                raise a_e
        return self.__class__.__name__ + ': ' + ', '.join(str_list) + '; '

    def __getattr__(self, key: str):
        try:
            return self.__dict__.__getitem__(key)
        except KeyError:
            raise AttributeError('No such attribute as {}'.format(key))

    @classmethod
    def from_dict(cls, dict_data: dict):
        obj = cls()
        obj.__dict__.update(dict_data)
        return obj

    # def __setattr__(self, key: str, value):
    #     if key == '__dict_data__':
    #         self.__dict__.__setitem__(key, value)
    #     elif key in self.__dir__():
    #         property(self, )
    #         object.__setattr__(self, key, value)
    #     # elif key in self.inner2outer_map:
    #     else:
    #         # self.__dict_data__[key] = value
    #         self.__dict_data__.__setitem__(key, value)

    def get_attr(self, key, default=None):
        try:
            return self.__dict__.__getitem__(key)
        except KeyError:
            if key in self.inner2outer_map:
                return default
            else:
                raise AttributeError('No such attribute as {}\n{}'.format(key, self.__dict_data__))

    def set_attr(self, key, value):
        self.__dict__.__setitem__(key, value)
        # self.__setattr__(key, value)

    def pop_attr(self, key):
        try:
            return self.__dict__.pop(key)
        except KeyError:
            return None

    def update(self, obj):
        if isinstance(obj, AttributeObject):
            # for key in self.inner2outer_map:
            #     self.set_attr(key, obj.get_attr(key))
            self.__dict__.update(obj.__dict_data__.copy())
        elif isinstance(obj, dict):
            self.__dict__.update(obj.copy())
        else:
            raise TypeError(type(obj))
        return self

    @property
    def __dict_data__(self):
        return self.__dict__

    # def form_insert_sql(self, table_name: str):
    #     from jetend.DataCheck import is_valid_float
    #     col_list, data_list = list(), list()
    #     for inner_key, outer_key in self.inner2outer_map.items():
    #         col_list.append(outer_key)
    #         # cell = self.get_attr(inner_key)
    #         cell = getattr(self, inner_key)
    #         if cell is None:
    #             data_list.append("''")
    #         elif isinstance(cell, float):
    #             if not is_valid_float(cell):
    #                 data_list.append("null")
    #             else:
    #                 data_list.append(str(cell))
    #         elif isinstance(cell, int):
    #             data_list.append(str(cell))
    #         else:
    #             data_list.append("'{}'".format(cell))
    #     return 'INSERT INTO {} ({}) VALUES ({})'.format(table_name, ', '.join(col_list), ', '.join(data_list))
