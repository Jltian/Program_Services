# -*- encoding: UTF-8 -*-
import os

from jetend.structures import DBFwrapper


class CSDCwrapper(object):

    def __init__(self, folder_path: str):
        assert os.path.exists(folder_path), '接口文件夹不存在 {}'.format(folder_path)
        assert os.path.isdir(folder_path), '接口文件夹不是文件夹 {}'.format(folder_path)
        self.__path__ = folder_path

    def check_data_integrity(self):
        """检查数据完整性"""
        pass

        # self.__is_file_exists__('JSMX02')                       # 结算明细第二批次文件
        # self.__is_file_exists__('HK_JSMX')                      # 港股通结算明细
        # self.__is_file_exists__('HK_ZQBD')                      # 港股通证券变动
        # self.__is_file_exists__('HK_ZQYE')                      # 港股通证券余额
        # self.__is_file_exists__('ZQYE')                         # 证券余额
        # self.__is_file_exists__('ZQBD')                         # 证券变动

    def load_all(self):
        for file_name in os.listdir(self.__path__):
            if not file_name.lower().endswith('dbf'):
                continue
            file_name_part = file_name.split('.')
            file_name_part.pop()
            file_name_part = '.'.join(file_name_part)
            print(file_name)
            for record in self.__open_dbf_file__(file_name_part):
                raise NotImplementedError(record)
                # print('\t', record)

    # def __load_position__(self, ):

    def __open_dbf_file__(self, dbf_name: str):
        if dbf_name.lower().endswith('.dbf'):
            return DBFwrapper(os.path.join(self.__path__, dbf_name))
        else:
            for file_name in os.listdir(self.__path__):
                if '{}.dbf'.format(dbf_name.lower()) == file_name.lower():
                    return DBFwrapper(os.path.join(self.__path__, file_name))
            raise FileNotFoundError('DBF数据文件缺失 {} {}'.format(dbf_name, self.__path__))

    def __is_file_exists__(self, dbf_name: str):
        for file_name in os.listdir(self.__path__):
            if '{}.dbf'.format(dbf_name.lower()) == file_name.lower():
                return True
        return False


if __name__ == '__main__':

    table = CSDCwrapper(r'Z:\NutStore\我的坚果云\中登数据接口\久铭1号 中金 7.9')

    table.load_all()
