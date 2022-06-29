# -*- encoding: UTF-8 -*-
import re
import xlrd

import numpy as np
from queue import Queue


class DataMapper(object):
    def __init__(self, map_rules: dict, hand_input_dict: dict, exclude_key: set = None):
        from extended.wrapper.Log import get_logger
        self.log = get_logger(self.__class__.__name__)
        self.__map_rules__ = map_rules
        self.__modify_dict__ = hand_input_dict.copy()
        self.result_list = list()

        self.ignore_cell = set()
        self.ignore_line = set()

        # vertical match key sequence
        self.lines_to_be_mapped = Queue()
        self.line_tag_sequence = None               # 需要匹配的列名称信息
        self.unknown_tag_list = list()              # 未知列名信息

        self.__last_line_list__ = None              # 前一行信息缓存
        self.__finished__ = False                   # 标识匹配是否已结束
        self.__right_align__ = False                # 行匹配右对齐
        self.__duplicated_tolerance__ = False       # 是否允许出现两次合法的相应数据列
        self.__map_force_vertical__ = False         # 是否强制按行匹配

        # possible keys
        self.__inner_outer_map__ = map_rules
        self.__outer_key_set__ = set()              # 所有可能的外部列名
        self.__outer_inner_map__ = dict()           # 需要匹配的外部列名
        for k, v in self.__map_rules__.items():
            assert isinstance(k, (str, type(None))), '匹配规则 map_rules 的 key 需要是 str/None'
            assert isinstance(v, (list, tuple, set)), '匹配规则 map_rules 的 value 需要是 list'
            for tag in v:
                self.__outer_key_set__.add(tag)
            if k is None:
                continue
            elif isinstance(k, str):
                if k.lower() == 'none':
                    continue
                else:
                    pass
            else:
                raise RuntimeError('未知 key 类型 {} {}'.format(type(k), k))
            for tag in v:
                self.__outer_inner_map__[tag] = k
        self.__exclude_key_set__ = exclude_key      # 不存在的列名

    def __line_clean__(self, *args, **kwargs):
        raise NotImplementedError

    def __check_key_percent__(self, line_list: list):
        count = 0
        for tag in line_list:
            tag = re.sub(r'\W', '', tag)
            if tag in self.__outer_key_set__:
                count += 1
        return count / len(line_list)

    def __check_exclude_key_percent__(self, line_list: list):
        if self.__exclude_key_set__ is None:
            return 0.0
        else:
            count = 0
            for tag in line_list:
                tag = re.sub(r'\W', '', tag)
                if tag in self.__exclude_key_set__:
                    count += 1
            return count / len(line_list)

    @staticmethod
    def __check_digit_percent__(line_list: list):
        count = 0
        for tag in line_list:
            if isinstance(tag, (float, int, np.float, np.int)):
                count += 1
            elif isinstance(tag, str):
                tag = re.sub(r'[^.,\w]', '', tag)
                try:
                    float(tag)
                    count += 1
                except ValueError:
                    pass
            else:
                try:
                    float(tag)
                    count += 1
                except ValueError:
                    pass
        return count / len(line_list)

    def __is_column_line__(self, line_list: list):
        if len(line_list) == 0:
            return False
        key_percent = self.__check_key_percent__(line_list)
        if key_percent > 0.1:
            if self.__check_exclude_key_percent__(line_list) > key_percent:
                return False
            for tag in line_list:
                if ':' in str(tag) or '：' in str(tag):
                    return False
            return True
        else:
            return False

    def __is_exclude_column_line__(self, line_list: list):
        if line_list.__len__() == 0:
            return False
        key_percent = self.__check_exclude_key_percent__(line_list)
        if key_percent > 0.2:
            if self.__check_key_percent__(line_list) > key_percent:
                return False
            for tag in line_list:
                if ':' in str(tag) or '：' in str(tag):
                    return False
            return True
        else:
            return False

    def __is_column_with_data_line__(self, line_list: list):
        if len(line_list) == 0:
            return False
        if self.__map_force_vertical__ is True:
            return False

        line_str = ''.join([str(var) for var in line_list])
        if line_str.count('：') >= 1:
            return True
        elif 0 < line_str.count(':') <= 2 and self.__check_key_percent__(line_list) > 0.2:
            check_time = re.search(r"\d+:\d+:\d", line_str)
            if check_time:
                return False
            else:
                return True
        else:
            if self.__check_key_percent__(re.sub(r'[^-.,\w]', '|', '|'.join(line_list)).split('|')) > 0:
                for tag in line_list:
                    if ':' in str(tag) or '：' in str(tag):
                        return True
                return False
            else:
                return False

    def __is_data_line__(self, line_list: list):
        if self.__check_digit_percent__(line_list) > 0.05:       # 判断有数据
            if self.__map_force_vertical__ is True:
                return True
            line_str = ''.join([str(var) for var in line_list])
            if '：' in line_str and self.__check_digit_percent__(line_list) < 0.5:
                return False
            elif self.__check_digit_percent__(line_list) > 0.5 and (line_str.count(':') + line_str.count('：')) <= 2:
                return True
            elif (':' in line_str or '：' in line_str) and len(line_list) < 6:
                return False
            else:
                return True
        else:
            return False

    def map_horizontal(self, *args, **kwargs):
        raise NotImplementedError

    def map(self, *args, **kwargs):
        raise NotImplementedError

    def map_line(self, line_list: list):
        raise NotImplementedError

    def form_new(self):
        return self.__modify_dict__.copy()

    def is_finished(self):
        return self.__finished__

    def restart(self):
        self.__finished__ = False
        self.map()
        raise NotImplementedError

    def set_right_align(self, algn: bool = True):
        self.__right_align__ = algn
        return self

    def set_duplicated_tolerance(self, tole: bool = True):
        self.__duplicated_tolerance__ = tole
        return self

    def set_force_vertical(self, force: bool = True):
        self.__map_force_vertical__ = force
        return self

    def add_identified_dict(self, d_dict: dict):
        self.__modify_dict__.update(d_dict)
        return self

    def __blank_obj_dict__(self):
        new_dict = dict()
        for tag in self.__inner_outer_map__:
            new_dict[tag] = None
        for tag in self.__modify_dict__:
            new_dict[tag] = self.__modify_dict__[tag]
        return new_dict

    def append_result(self, obj):
        self.result_list.append(obj)

    def update_identified(self, d_dict: dict):
        self.__modify_dict__.update(d_dict)
        return self


class TextMapper(DataMapper):
    def __init__(self, map_rules: dict, hand_input_dict: dict, exclude_key: set = None):
        super(TextMapper, self).__init__(
            map_rules=map_rules, hand_input_dict=hand_input_dict, exclude_key=exclude_key
        )
        self.__line_sep__ = ' '

    def __line_clean__(self, line_str: str):
        # content = re.sub(r'[^.:：\w]', ' ', line_str.strip())
        if len(re.sub(r'\W', '', line_str)) == 0:
            return list()
        content = line_str.strip()
        content = content.split(self.__line_sep__)
        while '' in content:
            content.remove('')
        new_list = list()
        for item in content:
            cleaned_item = re.sub(r'\W', '', item)
            if cleaned_item in self.ignore_line:
                return list()
            if cleaned_item not in self.ignore_cell:
                new_list.append(item)
        return new_list

    def map(self, text_content: str = None):
        if text_content is not None:
            for line_str in text_content.split('\n'):
                self.lines_to_be_mapped.put(line_str)
        while self.lines_to_be_mapped.empty() is False and self.__finished__ is False:
            self.map_line(self.__line_clean__(self.lines_to_be_mapped.get()))
        self.log.info_if(len(self.unknown_tag_list) > 0, '未知列名：\n{}\n{}'.format(
            self.__inner_outer_map__, self.unknown_tag_list
        ))
        return self.result_list

    def map_horizontal(self, text_content: str = None):
        if text_content is None:
            return

        for line_str in text_content.split('\n'):
            cleaned_line = re.sub(r'\W', '', line_str)
            check = True
            for tag in self.ignore_line:
                if tag in cleaned_line:
                    check = False
                    break
            if check is False:
                continue
            line_list = self.__line_clean__(line_str)
            if self.__is_column_with_data_line__(line_list):
                new_list = re.sub(r'[^-.,\w]', '|', '|'.join(line_list)).split('|')

                # 读取横着排列的数据
                while '' in new_list:
                    new_list.remove('')
                while '.' in new_list:
                    new_list.remove('.')

                key_tag = None
                while len(new_list) > 0:
                    top = new_list.pop(0)
                    # 获取数据标签
                    if key_tag is None:
                        cleand_top = re.sub(r'\W', '', top)
                        if cleand_top in self.__outer_key_set__:
                            key_tag = self.__outer_inner_map__.get(cleand_top, None)
                            continue
                        else:
                            continue
                    if key_tag in self.__modify_dict__:
                        key_tag = None
                        continue
                    cleand_top = re.sub(r'\W', '', top)
                    if len(cleand_top) == 0:
                        continue
                    self.__modify_dict__[key_tag] = top
                    key_tag = None
            else:
                pass

    def map_line(self, line_list: list):
        if len(line_list) == 0 or self.__finished__ is True:
            return

        if self.__is_column_line__(line_list):
            # 初始化列名顺序
            if self.line_tag_sequence is None:
                self.line_tag_sequence = list()
                for tag in line_list:
                    # 排列数据列先后
                    key_tag = re.sub(r'\W', '', tag)
                    self.line_tag_sequence.append(
                        self.__outer_inner_map__.get(key_tag, None))
                    if key_tag not in self.__outer_key_set__ and key_tag != '':
                        self.unknown_tag_list.append(key_tag)
            else:
                if self.__duplicated_tolerance__ is False:
                    info = '重复列信息，Dict: {}，List: {}'.format(self.__modify_dict__, line_list)
                    raise RuntimeWarning(info)
                else:
                    self.line_tag_sequence = None
                    self.map_line(line_list)

        elif self.__is_data_line__(line_list):
            # 匹配数据
            if self.__finished__ is True:
                return
            if self.line_tag_sequence is None:
                return

            if len(line_list) < len(self.line_tag_sequence):
                if self.__right_align__ is True:
                    new_dict = dict()
                    index = len(self.line_tag_sequence) - 1
                    while len(line_list) > 0:
                        column_match = False
                        cell = line_list.pop(-1)
                        assert isinstance(cell, str)
                        # 解决两个数字并在一起的问题 99.998100.004
                        if re.sub(r"[\d]", '', cell).count('.') == 2:
                            cell_list = cell.split('.')
                            line_list.append('.'.join([cell_list[0], cell_list[1][:round(0.5 * len(cell_list[1]))]]))
                            cell = '.'.join([cell_list[1][round(0.5 * len(cell_list[1])):], cell_list[2]])
                        while column_match is False:
                            key_tag = self.line_tag_sequence[index]
                            column_match = True
                            # column_match = self.__column_checker__.get(key_tag, lambda x: True).__call__(cell)
                            if key_tag is not None and column_match is True:
                                new_dict[key_tag] = cell
                            index -= 1
                else:
                    print(self.__modify_dict__)
                    print(self.line_tag_sequence, len(self.line_tag_sequence))
                    print(line_list, len(line_list))
                    raise RuntimeWarning('Not enough data to fill data column. {} {} \n {} {}'.format(
                        self.line_tag_sequence, len(self.line_tag_sequence), line_list, len(line_list)
                    ))
            elif len(line_list) > len(self.line_tag_sequence):
                print(self.__modify_dict__)
                print('\t: columns: ', self.line_tag_sequence, len(self.line_tag_sequence))
                print('\t: data', line_list, len(line_list))
                raise RuntimeWarning('Warning: more data than columns')
            else:
                new_dict = dict()
                for index in range(len(self.line_tag_sequence)):
                    key_tag = self.line_tag_sequence[index]
                    if key_tag is not None:
                        new_dict[key_tag] = line_list[index]
            # 生成对象
            new_dict.update(self.__modify_dict__)
            self.append_result(new_dict)
        else:
            pass

        self.__last_line_list__ = line_list

    def set_line_sep(self, sep: str = ' '):
        self.__line_sep__ = sep
        return self


class ExcelMapper(DataMapper):
    def __init__(self, map_rules: dict, hand_input_dict: dict, exclude_key: set = None):
        super(ExcelMapper, self).__init__(
            map_rules=map_rules, hand_input_dict=hand_input_dict, exclude_key=exclude_key
        )
        self.ignore_above_line = set()
        self.__data_line_ignore_tag__ = False
        self.__start_line__ = None
        self.__end_line__ = None
        self.__started__ = True

    def __line_clean__(self, line_list: list):
        content = list()
        for item in line_list:
            content.append(str(item).strip().upper())
        new_list = list()
        for item in content:
            cleaned_item = re.sub(r'[^/\w]', '', item)
            if cleaned_item in self.ignore_line:
                return list()
            if cleaned_item not in self.ignore_cell:
                new_list.append(item)
        return new_list

    def map(self, xls_content: xlrd.sheet.Sheet = None):
        self.__finished__ = False
        if xls_content is not None:
            for index in range(xls_content.nrows):
                self.lines_to_be_mapped.put(xls_content.row_values(index))
        while self.lines_to_be_mapped.empty() is False:
            line = self.__line_clean__(self.lines_to_be_mapped.get())
            # print(line)
            if len(line) == 0:
                continue
            for item in line:
                cleaned_item = re.sub(r'\W', '', item)
                if self.__start_line__ is not None:
                    if self.__start_line__ in cleaned_item:
                        self.__started__ = True
                if cleaned_item in self.ignore_above_line:
                    if self.lines_to_be_mapped.empty() is False:
                        self.lines_to_be_mapped.get()
                        self.__data_line_ignore_tag__ = True
                    break
                if self.__end_line__ is not None:
                    if cleaned_item == self.__end_line__:
                        self.__finished__ = True
                    if len(self.__end_line__) >= 4 and self.__end_line__ in cleaned_item:
                        self.__finished__ = True
            self.map_line(line)
        if self.__started__ is False:
            raise RuntimeError('Warning: mapping never starts.')
        if len(self.unknown_tag_list) > 0:
            raise RuntimeWarning('未知列名：\n{}\n{}'.format(self.unknown_tag_list, self.__inner_outer_map__, ))
        return self.result_list

    def map_horizontal(self, xls_content: xlrd.sheet.Sheet = None, force_map: bool = False):
        if xls_content is None:
            return
        for index in range(xls_content.nrows):
            line_list = self.__line_clean__(xls_content.row_values(index))
            cleaned_line = re.sub(r'\W', '', ''.join(line_list))
            check = True
            for tag in self.ignore_line:
                if tag in cleaned_line:
                    check = False
                    break
            if not check:
                continue

            if self.__is_column_with_data_line__(line_list) or force_map is True:
                new_list = re.sub(r'[^-.,\w]', '|', '|'.join(line_list)).split('|')

                # 读取横着排列的数据
                while '' in new_list:
                    new_list.remove('')

                key_tag = None
                while len(new_list) > 0:
                    top = new_list.pop(0)
                    if key_tag is None:
                        cleand_top = re.sub(r'\W', '', top)
                        if self.__check_key_percent__([cleand_top, ]) > 0:
                            key_tag = self.__outer_inner_map__.get(cleand_top, None)
                            continue
                        else:
                            continue
                    if key_tag not in self.__modify_dict__:
                        self.__modify_dict__[key_tag] = top
                    key_tag = None
            else:
                pass

    def map_line(self, line_list: list):
        if len(line_list) == 0 or self.__started__ is False or self.__finished__ is True:
            return

        if self.__is_column_line__(line_list):
            self.__data_line_ignore_tag__ = False
            # 初始化列名顺序
            if self.line_tag_sequence is None:
                self.line_tag_sequence = list()
                for tag in line_list:
                    # 排列数据列先后
                    key_tag = re.sub(r'\W', '', tag)
                    self.line_tag_sequence.append(
                        self.__outer_inner_map__.get(key_tag, None))
                    if key_tag not in self.__outer_key_set__ and key_tag != '':
                        self.unknown_tag_list.append(key_tag)
            else:
                self.__finished__ = True
                info = '重复列信息，Dict: {}，\n List: {}, \nCol: {}'.format(
                    self.__modify_dict__, line_list, self.line_tag_sequence)
                if self.__duplicated_tolerance__ is True:
                    self.log.debug('出现新的符合匹配的列名行, 已强制跳过')
                    self.__finished__ = False
                    # self.log.debug(info)
                else:
                    # self.log.warning(info)
                    raise RuntimeWarning('出现新的符合匹配的列名行, 匹配两遍的问题 {}'.format(info))

        elif self.__is_exclude_column_line__(line_list):
            if self.line_tag_sequence is None:
                pass
            else:
                self.__finished__ = True

        elif self.__is_data_line__(line_list):
            # 匹配数据
            if self.__finished__ is True:
                return

            if self.line_tag_sequence is None:
                info = '数据行出现在列名行之前 Dict: {}, line: {}'.format(self.__modify_dict__, line_list)
                self.log.warning_if(self.__exclude_key_set__ is None, info)
                self.log.debug_if(not self.__data_line_ignore_tag__ and self.__exclude_key_set__ is not None, info)
                return

            if len(line_list) < len(self.line_tag_sequence):
                print('\t', self.line_tag_sequence, len(self.line_tag_sequence))
                print('\t', line_list, len(line_list))
                raise RuntimeWarning('Not enough data to fill data column.')

            if len(line_list) > len(self.line_tag_sequence):
                print('\t', self.line_tag_sequence, len(self.line_tag_sequence))
                print('\t', line_list, len(line_list))
                raise RuntimeWarning('Warning: more data than columns')

            new_dict = dict()
            for index in range(len(self.line_tag_sequence)):
                key_tag = self.line_tag_sequence[index]
                if key_tag is not None:
                    new_dict[key_tag] = line_list[index]
            # 生成对象
            new_dict.update(self.__modify_dict__)
            self.append_result(new_dict)

        else:
            pass

        self.__last_line_list__ = line_list

    def set_start_line(self, tag: str):
        self.__start_line__ = tag
        self.__started__ = False
        return self

    def set_end_line(self, tag: str):
        self.__end_line__ = tag
        return self


# class PDFMapper(DataMapper):
#
#     def __init__(self, target: type, col_name: dict, hand_input_dict: dict):
#         super(PDFMapper, self).__init__(target=target, col_name=col_name, hand_input_dict=hand_input_dict)
#         self.__start_pattern__ = None
#         self.__finish_pattern__ = None
#         self.__started__ = True
#         self.__tag_to_be_filled__ = list()
#         self.__data_to_be_filled__ = list()
#         self.__new_obj_dict__ = self.__blank_obj_dict__()
#
#     def set_start_pattern(self, s_p: str):
#         self.__start_pattern__ = s_p
#
#     def set_end_pattern(self, e_p: str):
#         self.__finish_pattern__ = e_p
#
#     def __line_clean__(self, line_str: str):
#         # content = re.sub(r'[^.:：\w]', ' ', line_str.strip())
#         content = line_str.strip()
#         for tag in self.ignore_line:
#             if tag in content:
#                 return str()
#         if len(content) > 0 and content in self.ignore_cell:
#             return str()
#         return content
#
#     @staticmethod
#     def convert_pdf_2_text(path: str):
#         from io import StringIO
#         from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
#         from pdfminer.converter import TextConverter
#         from pdfminer.layout import LAParams
#         from pdfminer.pdfpage import PDFPage
#         retstr = StringIO()
#         rsrcmgr = PDFResourceManager()
#         device = TextConverter(rsrcmgr, retstr, codec='utf-8', laparams=LAParams())
#         interpreter = PDFPageInterpreter(rsrcmgr, device)
#         with open(path, 'rb') as fp:
#             for page in PDFPage.get_pages(fp, set()):
#                 interpreter.process_page(page)
#             text = retstr.getvalue()
#         device.close()
#         retstr.close()
#         text_line = text.split('\n')
#         for line_no, line in enumerate(text_line):
#             print(line_no, line)
#         return text
#
#     def map(self, text_content: str=None, start_pattern: str=None):
#         if start_pattern is None:
#             self.__start_mapping__ = True
#         if text_content is not None:
#             for line_str in text_content.split('\n'):
#                 self.lines_to_be_mapped.put(line_str)
#         while self.lines_to_be_mapped.empty() is False:
#             self.map_line(self.__line_clean__(self.lines_to_be_mapped.get()))
#         self.append_result(self.__target__(**self.__new_obj_dict__))
#
#         for line in pdf_content_list:
#             if len(line.replace(' ', '')) == 0:
#                 continue
#             else:
#                 self.lines_to_be_mapped.put(line)
#
#         if self.__start_pattern__ is not None:
#             self.__started__ = False
#
#         while self.lines_to_be_mapped.empty() is False:
#             line = self.__line_clean__(self.lines_to_be_mapped.get())
#             if len(line) == 0:
#                 continue
#
#             if self.__started__ is False and self.__finished__ is False:
#                 if self.__start_pattern__ in line:
#                     self.__started__ = True
#                 continue
#             elif self.__started__ is True and self.__finished__ is False:
#                 if self.__finish_pattern__ is not None:
#                     if self.__finish_pattern__ in line:
#                         self.__finished__ = True
#                 if self.__finished__ is True:
#                     continue
#                 self.map_line(line)
#             else:
#                 continue
#         if self.__started__ is False:
#             raise RuntimeWarning('Warning: mapping never starts.')
#         return self.result_list
#
#     def map_line(self, line_str: str):
#
#         if len(line_str) == 0:
#             return
#
#         if self.__is_column_line__([line_str, ]):
#             self.__tag_to_be_filled__.append(line_str)
#         else:
#             self.__data_to_be_filled__.append(line_str)
#             if len(self.__tag_to_be_filled__) > 0:
#                 for i in range(len(line_str)):
#                     tag = self.__tag_to_be_filled__.pop(0)
#                     if self.__new_obj_dict__[tag] is not None:
#                         self.append_result(self.__target__(**self.__new_obj_dict__))
#                         self.__new_obj_dict__ = self.__blank_obj_dict__()
#                     self.__new_obj_dict__[tag] = line_str[i]
#             else:
#                 pass
#
#     def map_horizontal(self, pdf_path: str):
#         text_content = self.convert_pdf_2_text(pdf_path)
#
#         for line_str in text_content.split('\n'):
#             cleaned_line = re.sub(r'\W', '', line_str)
#             check = True
#             for tag in self.ignore_line:
#                 if tag in cleaned_line:
#                     check = False
#                     break
#             if not check:
#                 continue
#             new_list = re.sub(r'[^-.,\w]', '|', line_str).split('|')
#             if self.__is_column_with_data_line__(new_list):
#
#                 # 读取横着排列的数据
#                 while '' in new_list:
#                     new_list.remove('')
#                 while '.' in new_list:
#                     new_list.remove('.')
#
#                 key_tag = None
#                 while len(new_list) > 0:
#                     top = new_list.pop(0)
#                     if key_tag is None:
#                         cleand_top = re.sub(r'\W', '', top)
#                         if cleand_top in self.__outer_key_set__:
#                             key_tag = self.__outer_inner_map__.get(cleand_top, None)
#                             continue
#                         else:
#                             continue
#                     if key_tag in self.__modify_dict__:
#                         key_tag = None
#                         continue
#                     self.__modify_dict__[key_tag] = top
#                     key_tag = None
#             else:
#                 pass


if __name__ == '__main__':
    pass
    # PDFMapper.convert_pdf_2_text(r'D:\久铭产品交割单\2018年4月\久铭产品交割单20180411\中信美股\SACTC1050US20170324组合调整报告2018-04-11.pdf')
