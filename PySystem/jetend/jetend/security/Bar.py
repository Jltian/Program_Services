# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------

from jetend.DataCheck import is_valid_float


class Bar(dict):

    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        from pandas import Series
        for obj in args:
            if isinstance(obj, dict):
                self.update(obj)
            elif isinstance(obj, Series):
                for tag in obj.index:
                    self.__setitem__(tag, obj[tag])
            else:
                raise NotImplementedError('{} {}'.format(type(obj), str(obj)))
        for obj_k, obj_v in kwargs.items():
            self.__setitem__(obj_k, obj_v)

    def __get_float_attr__(self, attr_tag: str):
        try:
            attr_value = self.__getitem__(attr_tag)
            if not is_valid_float(attr_value):
                raise AttributeError('Attribute type error {}\n{}'.format(type(attr_value), self))
        except KeyError:
            raise AttributeError('Attribute miss {}\n{}'.format(attr_tag, self))
        return attr_value

    @property
    def open(self):
        return self.__get_float_attr__('open')

    @property
    def close(self):
        return self.__get_float_attr__('close')

    @property
    def high(self):
        return self.__get_float_attr__('high')

    @property
    def low(self):
        return self.__get_float_attr__('low')

    @property
    def volume(self):
        return self.__get_float_attr__('volume')

    @property
    def amount(self):
        return self.__get_float_attr__('amount')
