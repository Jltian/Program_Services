# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
from extended.Interface import AbstractDataStructure


class List(list, AbstractDataStructure):
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)

    def __repr__(self):
        content, iter_count = 'List starts [\n', 0
        for value in self.__iter__():
            content += 'index {}: {},\n'.format(iter_count, value)
            iter_count += 1
        content += '] List ends'
        return content

    @classmethod
    def from_pd(cls, d_type: type, dt):
        from pandas import DataFrame
        assert isinstance(dt, DataFrame)
        target_list = cls()
        for i in dt.index:
            one_series = dt.iloc[i, ]
            assert hasattr(d_type, 'from_series')
            target_list.append(getattr(d_type, 'from_series').__call__(one_series))
        return target_list

    @classmethod
    def from_dict_list(cls, d_type: type, d_list):
        target_list = cls()
        for d_obj in d_list:
            assert isinstance(d_obj, dict)
            if hasattr(d_type, 'from_dict'):
                target_list.append(getattr(d_type, 'from_dict').__call__(d_obj))
            else:
                target_list.append(d_type(**d_obj))
        return target_list

    @classmethod
    def init_from(cls, obj):
        new_obj = cls()
        if isinstance(obj, (list, tuple)):
            new_obj.extend(obj)
        else:
            raise NotImplementedError(type(obj))
        return new_obj

    def copy(self):
        new_l = List()
        new_l.extend(self)
        return new_l

    def to_list(self):
        new_l = list()
        new_l.extend(self)
        return new_l

    def change_attr(self, **kwargs):
        """批量修改列表内对象属性"""
        focus_overwrite = kwargs.get('focus_overwrite', False)
        for obj in self.__iter__():
            for attr_tag, from_to in kwargs.items():
                if attr_tag in('focus_overwrite', ):
                    continue
                if isinstance(from_to, dict) and focus_overwrite is False:
                    if getattr(obj, attr_tag) in from_to:
                        setattr(obj, attr_tag, from_to[getattr(obj, attr_tag)])
                else:
                    setattr(obj, attr_tag, from_to)
        return self

    def find_value_where(self, **kwargs):
        """
        find values by constrains -> ObjectDict
        :param kwargs:
        :return: DataList, list of stored value
        """
        target_list = List()
        for value in self.__iter__():
            all_check = True
            for c_key, c_value in kwargs.items():
                if isinstance(c_value, (list, tuple)):
                    try:
                        if getattr(value, c_key) not in c_value:
                            all_check = False
                            break
                    except AttributeError:
                        if value[c_key] not in c_value:
                            all_check = False
                            break
                else:
                    try:
                        if getattr(value, c_key) != c_value:
                            all_check = False
                            break
                    except AttributeError:
                        if value[c_key] != c_value:
                            all_check = False
                            break
            if all_check is True:
                target_list.append(value)
        return target_list

    def find_value(self, **kwargs):
        target_list = self.find_value_where(**kwargs)
        if len(target_list) == 1:
            return target_list[0]
        if len(target_list) == 0:
            raise ValueError('No value satisfy {}\n{}'.format(kwargs, str(self)))
        else:
            raise RuntimeError('Unknown Error {}\n{}'.format(str(kwargs), str(target_list)))

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
        if range_start is None or range_end is None:
            pass
        else:
            assert range_start <= range_end, '削减范围的开始必须在结束前面 {} {}'.format(range_start, range_end)

        result = List()

        for value in self.__iter__():
            if range_start is None:
                pass
            else:
                if include_start is True:
                    if getattr(value, attr_tag) < range_start:
                        continue
                else:
                    if getattr(value, attr_tag) <= range_start:
                        continue
            if range_end is None:
                pass
            else:
                if include_end is True:
                    if getattr(value, attr_tag) > range_end:
                        continue
                else:
                    if getattr(value, attr_tag) >= range_end:
                        continue

            result.append(value)

        if inline is True:
            raise RuntimeError('不允许直接删除列表内容。')
        else:
            return result

    def group_by_attr(self, attr_tag: str):
        """
        把内容对象按照 by_tag 属性分组，得到 { by_tag: {obj1, obj2, }} -> dict
        :param attr_tag: related attribute
        :return: dict( key: set())
        """
        grouped_dict = dict()

        for obj in self.__iter__():
            # obj = self.__getitem__(index)
            by_value = getattr(obj, attr_tag)

            if by_value is None:
                continue

            if not isinstance(by_value, str):
                by_value = str(by_value)

            if len(by_value) == 0:  # jump to next iteration if no content
                continue

            if by_value not in grouped_dict:
                grouped_dict[by_value] = List()

            grouped_dict[by_value].append(obj)

        return grouped_dict

    def group_attr_set_by(self, group_attr: str, by_attr: str):
        """
        建立属性之间映射的快速索引字典 -> dict( by_attr: set(group_attr, ))
        :param group_attr:
        :param by_attr:
        :return: dict( by_attr: set())
        """
        grouped_dict = dict()

        for obj in self.__iter__():
            key = getattr(obj, by_attr)
            if key not in grouped_dict:
                grouped_dict[key] = set()
            grouped_dict[key].add(getattr(obj, group_attr))

        return grouped_dict

    def collect_attr_set(self, attr_tag: str):
        """
        收集出现过的属性内容至一个集合 -> set
        :param attr_tag: str
        :return: set()
        """
        collected_set = set()

        for obj in self.__iter__():
            try:
                collected_set.add(getattr(obj, attr_tag))
            except AttributeError:
                collected_set.add(obj[attr_tag])

        return collected_set

    def collect_key_value_set(self, key_tag: str):
        collected_set = set()

        for obj in self.__iter__():
            collected_set.add(obj[key_tag])

        return collected_set

    def collect_attr_list(self, attr_tag: str):
        """ 收集出现过的属性内容至一个列表 -> list"""
        collected_list = list()

        for obj in self.__iter__():
            collected_list.append(getattr(obj, attr_tag))

        return collected_list

    def collect_attr_combine_list(self, attr_list: list):
        collected_list = list()

        for obj in self.__iter__():
            collected_list.append([getattr(obj, var) for var in attr_list])

        return collected_list

    def collect_key_value_list(self, key_tag: str):
        collected_list = list()

        for obj in self.__iter__():
            collected_list.append(obj[key_tag])

        return collected_list

    def collect_attr_map(self, ket_attr: str, value_attr: str):
        collected_dict = dict()

        for obj in self.__iter__():
            collected_dict[getattr(obj, ket_attr)] = getattr(obj, value_attr)

        return collected_dict

    def collect_attr_series(self, index_attr: str, data_attr: str):
        from pandas import Series
        return Series(data=self.collect_attr_list(data_attr), index=self.collect_attr_list(index_attr))

    def collect_key_value_series(self, index_key: str, data_key: str):
        from pandas import Series
        return Series(data=self.collect_key_value_list(data_key), index=self.collect_key_value_list(index_key))

    def batch_set_key_value(self, key: str, value):
        for obj in self.__iter__():
            obj[key] = value

    def sum_attr(self, attr_tag: str):
        result = 0.0

        for obj in self.__iter__():
            result += getattr(obj, attr_tag)

        return result

    def sort_by_key(self, key_tag: str, reverse: bool = False):
        return sorted(self, key=lambda s: s[key_tag], reverse=reverse)

    def to_pd(self):
        from pandas import DataFrame
        type_set = set()
        for obj in self.__iter__():
            type_set.add(type(obj))
        if len(type_set) == 1:
            obj_type = list(type_set)[0]
        elif len(type_set) == 0:
            if self.__len__() == 0:
                return DataFrame()
            else:
                raise RuntimeError('列表中没有数据对象，无法生成 {}'.format(DataFrame.__name__))
        else:
            raise RuntimeError('列表中存在多个类型数据对象 {}，无法生成 {}'.format(type_set, DataFrame.__name__))
        # assert issubclass(obj_type, AbstractDataObject), '{}'.format(obj_type)
        o2i_key_map = obj_type.outer2inner_map()
        outer_column_list = list(o2i_key_map.keys())
        record_dict = dict()
        for outer_key in outer_column_list:
            inner_key = o2i_key_map[outer_key]
            column_list = list()
            for obj in self.__iter__():
                column_list.append(getattr(obj, inner_key))
            record_dict[outer_key] = column_list
        result = DataFrame.from_dict(record_dict)
        return result

    # def write_to_xls(self, sheet):
    #     from jetend.structures import MassObject
    #     from xlwt.Worksheet import Worksheet
    #     assert isinstance(sheet, Worksheet), '{}'.format(type(sheet))
    #     for i in range(len(self)):
    #         obj = self.__getitem__(i)
    #         assert isinstance(obj, MassObject), str(type(obj))
    #         if i == 0:
    #             obj.write_columns_to_xls(sheet, 0)
    #         obj.write_content_to_xls(sheet, i + 1)


if __name__ == '__main__':
    print(issubclass(List, list))
