# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import json
import os


FILE_ENCODING = 'UTF-8'


class FileDataBase(object):
    """文档型简易json数据库"""

    def __init__(self, db_path: str):
        self.__path__ = db_path

    def show_data_bases(self):
        """搜索文档目录，返回寻找到的数据集合"""
        # 搜寻文档目录
        db_list = list()
        for item_name in os.listdir(self.__path__):
            # 判断是否是Sector并返回Sector
            if os.path.isdir(os.path.join(self.__path__, item_name)) and os.path.exists(
                os.path.join(self.__path__, item_name, BaseSector.__index_file_name__)
            ):
                db_list.append(os.path.join(self.__path__, item_name))
            else:
                pass
        return db_list


class BaseSector(object):
    """数据集合，内含若干表格"""
    __index_file_name__ = '__sector_index__.json'

    def __init__(self, sector_path: str):
        self.__path__ = sector_path
        self.structure = json.load(open(os.path.join(self.__path__, )))

    def __repr__(self):
        return 'FileBaseSector {}, Located {}'.format(self.name, self.__path__)

    @property
    def name(self):
        return self.__path__.split(os.path.sep)[-1]
