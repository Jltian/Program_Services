# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
from extended.Decoration import depreciated_method


class AbstractDataStructure:

    @classmethod
    def init_from(cls, obj):
        raise NotImplementedError

    def find_value(self, **kwargs):
        raise NotImplementedError

    def find_value_where(self, **kwargs):
        raise NotImplementedError

    def trim_include_between_attr_value(
            self, attr_tag: str, range_start, range_end,
            include_start: bool = True, include_end: bool = False, inline: bool = False
    ):
        raise NotImplementedError

    def group_by_attr(self, attr_tag: str):
        raise NotImplementedError

    def collect_attr_set(self, attr_tag: str):
        raise NotImplementedError

    def collect_key_value_set(self, key_tag: str):
        raise NotImplementedError

    def collect_attr_list(self, attr_tag: str):
        raise NotImplementedError

    def collect_key_value_list(self, key_tag: str):
        raise NotImplementedError

    # ----------------- [depreciated] -----------------
    @depreciated_method('trim_include_between_attr_value')
    def trim_between_range(self, *args, **kwargs):
        return self.trim_include_between_attr_value(*args, **kwargs)

    @depreciated_method('group_by_attr')
    def group_by(self, *args, **kwargs):
        return self.group_by_attr(*args, **kwargs)


class AbstractPersistObject:
    __get_state_attribute__ = 'get_state'
    __set_state_attribute__ = 'set_state'

    def get_state(self):
        """return the content of the object -> str"""
        raise NotImplementedError

    @classmethod
    def set_state(cls, state: str):
        """return the new object -> obj"""
        raise NotImplementedError


class AbstractPersistStructure:
    __path__ = None
    __postfix__ = None

    def __list_path__(self):
        from os import listdir
        assert isinstance(self.__path__, str), '__path__ should be set in function __init__'
        assert isinstance(self.__postfix__, str), '__postfix__ should be set in class definition'
        for tag in listdir(self.__path__):
            if tag.startswith('.'):
                continue
            if not tag.endswith(self.__postfix__):
                continue
            yield '.'.join(tag.split('.')[:-1])

    def __check_postfix__(self, key: str):
        if '.' in key:
            if key.split('.')[-1] == self.__postfix__:
                return key
            else:
                return '{}.{}'.format(key, self.__postfix__)
        else:
            return '{}.{}'.format(key, self.__postfix__)

    def __sub_path__(self, sub_name: str):
        from os import path
        assert isinstance(self.__path__, str), '__path__ should be set in function __init__'
        return path.join(self.__path__, sub_name)
