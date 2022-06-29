# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
from extended.Interface import AbstractDataStructure
from extended.Decoration import depreciated_method


class ObjectDict(dict, AbstractDataStructure):

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    @classmethod
    def init_from(cls, obj):
        from collections.abc import Mapping
        if isinstance(obj, Mapping):
            new_d = cls()
            for key, value in obj.items():
                new_d[key] = value
            return new_d
        else:
            raise NotImplementedError

    def __repr__(self):
        content = '{\n'
        for key, value in self.items():
            content += '\t{}: {}\n'.format(key, value)
        content += '}'
        return content

    def copy(self):
        new_d = ObjectDict()
        for k, v in self.items():
            new_d.__setitem__(k, v)
        return new_d

    def to_dict(self):
        new_d = dict()
        for k, v in self.items():
            new_d[k] = v
        return new_d

    def find_value(self, **kwargs):
        target_dict = self.find_value_where(**kwargs)
        if len(target_dict) == 1:
            return list(target_dict.values())[0]
        if len(target_dict) == 0:
            raise ValueError('No value satisfy {}'.format(kwargs))
        else:
            raise RuntimeError('Unknown Error {}'.format(str(target_dict)))

    def find_value_where(self, **kwargs):
        """
        find values by constrains -> ObjectDict
        :param kwargs:
        :return: DataList, list of stored value
        """
        target_dict = ObjectDict()
        for key, value in self.items():
            all_check = True
            for c_key, c_value in kwargs.items():
                if getattr(value, c_key) != c_value:
                    all_check = False
                    break
            if all_check is True:
                target_dict[key] = value
        return target_dict

    def trim_include_by_keys(self, keys):
        result = ObjectDict()
        for k, v in self.items():
            if k in keys:
                result[k] = v
        return result

    def trim_include_between_attr_value(
            self, attr_tag: str, range_start, range_end,
            include_start: bool = True, include_end: bool = False, inline: bool = False
    ):
        """
        删选合适的数据进入内存 -> dict
        :param attr_tag:
        :param range_start:
        :param range_end:
        :param include_start:
        :param include_end:
        :param inline: whether modify data in self
        :return: DataDict
        """
        result = ObjectDict()

        if range_start is None:
            for key, value in self.items():
                result[key] = value
        else:
            if include_start is True:
                for key, value in self.items():
                    if range_start <= getattr(value, attr_tag):
                        result[key] = value
            else:
                for key, value in self.items():
                    if range_start < getattr(value, attr_tag):
                        result[key] = value

        if range_end is not None:
            if include_end is True:
                for key in list(result.keys()):
                    value = result[key]
                    if getattr(value, attr_tag) > range_end:
                        result.pop(key)
            else:
                for key in list(result.keys()):
                    value = result[key]
                    if getattr(value, attr_tag) >= range_end:
                        result.pop(key)

        if inline is True:
            self.clear()
            self.update(result)
            return self
        else:
            return result

    def trim_include_by_attr_value(self, attr_tag: str, range_iterable, inline: bool = False):
        """

        :param attr_tag:
        :param range_iterable:
        :param inline:
        :return: DataDict
        """
        if isinstance(range_iterable, (set, frozenset, list, tuple)):
            range_iterable = frozenset(range_iterable)
        elif isinstance(range_iterable, (str, int, float)):
            range_iterable = (range_iterable, )
        else:
            from extended.Exceptions import ParamTypeError
            raise ParamTypeError('range_iterable', (set, frozenset, list, tuple), range_iterable)

        result = ObjectDict()

        for key, value in self.items():
            if getattr(value, attr_tag) in range_iterable:
                result[key] = value

        if inline is True:
            self.clear()
            self.update(result)
            return self
        else:
            return result

    @depreciated_method('trim_include_by_attr_value')
    def trim_by_range(self, *args, **kwargs):
        return self.trim_include_by_attr_value(*args, **kwargs)

    def trim_exclude_by_attr_value(self, attr_tag: str, exclude_iterable, inline: bool = False):
        if isinstance(exclude_iterable, (set, frozenset, list, tuple)):
            exclude_iterable = frozenset(exclude_iterable)
        else:
            from extended.Exceptions import ParamTypeError
            raise ParamTypeError('exclude_iterable', (set, frozenset, list, tuple), exclude_iterable)

        result = ObjectDict()

        for key, value in self.items():
            if getattr(value, attr_tag) not in exclude_iterable:
                result[key] = value

        if inline is True:
            self.clear()
            self.update(result)
            return self
        else:
            return result

    @depreciated_method('trim_exclude_by_attr_value')
    def trim_exclude_range(self, *args, **kwargs):
        return self.trim_exclude_by_attr_value(*args, **kwargs)

    def group_by_attr(self, attr_tag: str):
        """
        把内容对象按照 by_tag 属性分组，得到 { by_tag: {obj1, obj2, }} -> dict
        :param attr_tag: related attribute
        :return: dict( key: set())
        """
        grouped_dict = dict()

        for index, obj in self.items():
            # obj = self.__getitem__(index)
            by_value = getattr(obj, attr_tag)

            if by_value is None:
                continue

            if not isinstance(by_value, str):
                by_value = str(by_value)

            if len(by_value) == 0:  # jump to next iteration if no content
                continue

            if by_value not in grouped_dict:
                grouped_dict[by_value] = ObjectDict()

            grouped_dict[by_value][index] = obj

        return grouped_dict

    def group_attr_set_by(self, group_attr: str, by_attr: str):
        """
        建立属性之间映射的快速索引字典 -> dict( by_attr: set(group_attr, ))
        :param group_attr:
        :param by_attr:
        :return: dict( by_attr: set())
        """
        grouped_dict = dict()

        for obj in self.values():
            key = getattr(obj, by_attr)
            if key not in grouped_dict:
                grouped_dict[key] = set()
            grouped_dict[key].add(getattr(obj, group_attr))

        return grouped_dict

    def neighbor_attr_by(self, neighbor_tag: str, shadow_tag: str):
        """
        根据另一个属性(shadow_tag)建立同一个属性不同数据的联系集 -> dict( neighbor_tag_1: set(neighbor_tag_2, ...))
        :param neighbor_tag:
        :param shadow_tag:
        :return: dict( neighbor_tag_1: set(neighbor_tag_2, ...))
        """
        neighbor_dict = dict()

        first_level_index = self.group_attr_set_by(group_attr=shadow_tag, by_attr=neighbor_tag)
        second_level_index = self.group_attr_set_by(group_attr=neighbor_tag, by_attr=shadow_tag)
        for first_k in first_level_index.keys():
            neighbor_dict[first_k] = set()
            for second_k in first_level_index[first_k]:
                neighbor_dict[first_k].update(second_level_index[second_k])

        return neighbor_dict

    def collect_attr_set(self, attr_tag: str):
        """
        收集出现过的属性内容至一个集合 -> set
        :param attr_tag: str
        :return: set()
        """
        collected_set = set()

        for obj in self.values():
            collected_set.add(getattr(obj, attr_tag))

        return collected_set

    def collect_attr_list(self, attr_tag: str):
        """ 收集出现过的属性内容至一个列表 -> list"""
        collected_list = list()

        for obj in self.values():
            collected_list.append(getattr(obj, attr_tag))

        return collected_list

    def count_attr_obj(self, attr_tag: str):
        """
        对出现过的属性对象计数 -> CountingDict
        :param attr_tag: str
        :return: CountingDict
        """
        from extended.data.CountingDict import CountingDict

        counted_dict = CountingDict()

        for obj in self.values():
            counted_dict.count(getattr(obj, attr_tag))

        return counted_dict

    def count_attr_iterable(self, attr_tag: str):
        """对字典储存对象的属性列表中的对象计数 -> CountingDict"""
        from collections import Iterable
        from extended.data.CountingDict import CountingDict

        counted_dict = CountingDict()

        for obj in self.values():
            attr_iterable = getattr(obj, attr_tag)
            assert isinstance(attr_iterable, Iterable), 'tag {} obj {}'.format(attr_tag, str(obj))
            for item in attr_iterable:
                counted_dict.count(item)

        return counted_dict
