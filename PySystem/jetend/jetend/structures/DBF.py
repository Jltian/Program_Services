# -*- encoding: UTF-8 -*-
import os

from collections import Iterable, OrderedDict

from dbfread import DBF


class DBFwrapper(Iterable):

    def __init__(self, file_path: str):
        assert file_path.split('.')[-1].upper() == 'DBF', '输入文件并非DBF文件 {}'.format(file_path)
        assert os.path.exists(file_path), '输入文件不存在 {}'.format(file_path)
        self.__path__ = file_path

        self.table = DBF(self.__path__, encoding='gb18030')

    def __iter__(self):
        for record in self.table:
            assert isinstance(record, OrderedDict), '{}'.format(type(record))
            yield record

    def deleted(self):
        for record in self.table.deleted:
            assert isinstance(record, OrderedDict), '{}'.format(type(record))
            yield record
