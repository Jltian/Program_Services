# -*- encoding: UTF-8 -*-
import datetime
import os
import platform
import shutil


if platform.system() in ('Darwin', ):
    SYS_MB_BYTES = 1000
    SYS_GB_BYTES = 1000 * 1000
elif platform.system() in ('Windows', ):
    SYS_MB_BYTES = 1024
    SYS_GB_BYTES = 1024 * 1024
else:
    raise RuntimeError(platform.system())


class Path(object):
    def __init__(self, path):
        if isinstance(path, str):
            self.__path__ = path
        elif isinstance(path, Path):
            self.__path__ = path.__path__
        else:
            raise TypeError

    def __repr__(self):
        return self.__path__

    @property
    def str(self):
        return self.__path__

    @property
    def exists(self):
        """return whether what the path represents exists -> bool"""
        return os.path.exists(self.__path__)

    @property
    def is_file(self):
        """return whether the path represents a file -> bool"""
        return os.path.isfile(self.__path__)

    @property
    def is_folder(self):
        """return whether the path represents a folder -> bool"""
        return os.path.isdir(self.__path__)

    @property
    def name(self):
        """return the name of path -> str"""
        return os.path.split(self.__path__)[-1]

    @property
    def postfix(self):
        """return the postfix (file type) of path -> str"""
        if self.is_file:
            if '.' in self.name:
                return self.__path__.split('.')[-1]
            else:
                return ''
        else:
            return ''

    @property
    def ksize(self):
        """size in KB -> float"""
        return os.stat(self.__path__).st_size

    @property
    def msize(self):
        """size in MB -> float"""
        return os.stat(self.str).st_size / SYS_MB_BYTES

    @property
    def gsize(self):
        return os.stat(self.str).st_size / SYS_GB_BYTES

    @property
    def time_last_visited(self):
        return datetime.datetime.fromtimestamp(os.stat(self.__path__).st_atime)

    @property
    def time_last_modified(self):
        return datetime.datetime.fromtimestamp(os.stat(self.__path__).st_mtime)

    @property
    def time_disk_created(self):
        return datetime.datetime.fromtimestamp(os.stat(self.__path__).st_ctime)

    def sub_path(self, name):
        if self.is_file:
            raise RuntimeError('file {} has no sub_path'.format(self))
        return Path(os.path.join(self.__path__, name))

    def move_to(self, folder_path, overwrite: bool = False):
        if isinstance(folder_path, str):
            folder_path = Path(folder_path)
        elif isinstance(folder_path, Path):
            pass
        else:
            raise NotImplementedError(type(folder_path))

        # 检查目标目录
        if not os.path.exists(folder_path.str):
            os.makedirs(folder_path.str)
        if not folder_path.is_folder:
            raise RuntimeError('target path is not folder: {}.'.format(folder_path))

        # 检查最终目标路径
        target_path = folder_path.sub_path(self.name)
        if target_path.exists:
            if self.is_file:
                if overwrite is True:
                    return Path(shutil.move(self.str, folder_path.str))
                else:
                    raise FileExistsError('target file {} already exists.'.format(target_path))
            elif self.is_folder:
                folder_list, file_list = self.list()
                for file in file_list:
                    file.move_to(target_path, overwrite=overwrite)
                for folder in folder_list:
                    folder.move_to(target_path, overwrite=overwrite)
                return target_path
            else:
                raise RuntimeError(self.str)
        else:
            return Path(shutil.move(self.str, folder_path.str))

    def copy_to(self, folder_path, overwrite: bool = False):
        if isinstance(folder_path, str):
            folder_path = Path(folder_path)
        elif isinstance(folder_path, Path):
            pass
        else:
            raise NotImplementedError(type(folder_path))

        # 检查目标目录
        if not os.path.exists(folder_path.str):
            os.makedirs(folder_path.str)
        if not folder_path.is_folder:
            raise RuntimeError('target path is not folder: {}.'.format(folder_path))

        # 检查最终目标路径
        target_path = folder_path.sub_path(self.name)
        if target_path.exists:
            if self.is_file:
                if overwrite is True:
                    return Path(shutil.copy(self.str, folder_path.str))
                else:
                    raise FileExistsError('target file {} already exists.'.format(target_path))
            elif self.is_folder:
                folder_list, file_list = self.list()
                for file in file_list:
                    file.copy_to(target_path, overwrite=overwrite)
                for folder in folder_list:
                    folder.copy_to(target_path, overwrite=overwrite)
                return target_path
            else:
                raise RuntimeError(self.str)
        else:
            return Path(shutil.copy(self.str, folder_path.str))

    def list(self, ignore_prefix=('.', )):
        """list the folder -> folder_list, file_list"""
        if self.is_folder:
            folder_list, file_list = list(), list()
            for name in os.listdir(self.str):
                for prefix in ignore_prefix:
                    if name.startswith(prefix):
                        continue
                sub_path = self.sub_path(name)
                if sub_path.is_file:
                    file_list.append(sub_path)
                elif sub_path.is_folder:
                    folder_list.append(sub_path)
                else:
                    raise RuntimeWarning(sub_path)
            return folder_list, file_list
        else:
            raise RuntimeError('Non folder can not list.'.format(self))

    def list_folder(self, ignore_prefix=('.', )):
        """list folders in folder -> list"""
        folder_list, file_list = self.list(ignore_prefix=ignore_prefix)
        return folder_list

    def list_file(self, ignore_prefix=('.', )):
        """list files in folder -> list"""
        folder_list, file_list = self.list(ignore_prefix=ignore_prefix)
        return file_list

    def delete(self):
        if self.is_folder:
            os.removedirs(self.str)
        elif self.is_file:
            os.remove(self.str)
        else:
            raise RuntimeError(self)


# class FolderPath(object):
#     """文件夹路径对象"""
#     def __init__(self, abs_path: str):
#         if os.path.exists(abs_path):
#             assert os.path.isfile(abs_path) is False, 'abs_path {} is a file instead of a folder'.format(abs_path)
#             self.__path__ = abs_path
#         else:
#             RuntimeError('path {} not exists.'.format(abs_path))
#
#     @property
#     def folder_name(self):
#         path_list = self.__path__.split(os.path.sep)
#         return path_list[-1]
#
#     def folder_path(self, move: int=0):
#         assert move <= 0
#         path_list = self.__path__.split(os.path.sep)
#         folder_level = move
#         try:
#             while folder_level < 0:
#                 path_list.pop()
#                 folder_level += 1
#             return os.path.sep.join(path_list)
#         except IndexError:
#             raise ValueError('No such super folder as level {}'.format(move))
#
#     def move_to(self, folder_path: str):
#         if not os.path.exists(folder_path):
#             os.makedirs(folder_path)
#
#         assert os.path.isfile(folder_path) is False
#         target_path = os.path.join(folder_path, self.folder_name)
#         if os.path.exists(target_path) is True:
#             raise FileExistsError('target path {} already exists.'.format(target_path))
#         else:
#             shutil.move(self.__path__, folder_path)
#             self.__path__ = target_path
#
#     def copy_to(self, folder_path: str):
#         if not os.path.exists(folder_path):
#             os.makedirs(folder_path)
#
#         assert os.path.isfile(folder_path) is False
#         target_path = os.path.join(folder_path, self.folder_name)
#         if os.path.exists(target_path) is True:
#             raise FileExistsError('target path {} already exists.'.format(target_path))
#         else:
#             shutil.copy(self.__path__, folder_path)
#
#     def delete(self):
#         os.removedirs(self.__path__)


# class FilePath(object):
#     """文件路径对象"""
#     def __init__(self, abs_path: str):
#         if os.path.exists(abs_path):
#             assert os.path.isfile(abs_path) is True, 'abs_path {} is a folder instead of a file'.format(abs_path)
#             self.__path__ = abs_path
#         else:
#             RuntimeError('path {} not exists.'.format(abs_path))
#
#     @property
#     def full_name(self):
#         return os.path.split(self.__path__)[-1]
#
#     @property
#     def name(self):
#         file_name = self.full_name
#         assert isinstance(file_name, str)
#         file_name = file_name.split('.')
#         file_name.pop()
#         return '.'.join(file_name)
#
#     @property
#     def type(self):
#         file_name = self.full_name
#         assert isinstance(file_name, str)
#         file_name = file_name.split('.')
#         return file_name[-1]
#
#     @property
#     def folder_name(self):
#         path_list = self.__path__.split(os.path.sep)
#         path_list.pop()
#         return path_list[-1]
#
#     def folder_path(self, move: int=0):
#         assert move <= 0
#         path_list = self.__path__.split(os.path.sep)
#         path_list.pop()
#         folder_level = move
#         try:
#             while folder_level < 0:
#                 path_list.pop()
#                 folder_level += 1
#             return os.path.sep.join(path_list)
#         except IndexError:
#             raise ValueError('No such super folder as level {}'.format(move))
#
#     def move_to(self, folder_path: str):
#         if not os.path.exists(folder_path):
#             os.makedirs(folder_path)
#
#         assert os.path.isfile(folder_path) is False
#         target_path = os.path.join(folder_path, self.full_name)
#         if os.path.exists(target_path) is True:
#             raise FileExistsError('target path {} already exists.'.format(target_path))
#         else:
#             shutil.move(self.__path__, folder_path)
#             self.__path__ = target_path
#
#     def copy_to(self, folder_path: str):
#         if not os.path.exists(folder_path):
#             os.makedirs(folder_path)
#
#         assert os.path.isfile(folder_path) is False
#         target_path = os.path.join(folder_path, self.full_name)
#         if os.path.exists(target_path) is True:
#             raise FileExistsError('target path {} already exists.'.format(target_path))
#         else:
#             shutil.copy(self.__path__, folder_path)
#
#     def delete(self):
#         os.remove(self.__path__)
