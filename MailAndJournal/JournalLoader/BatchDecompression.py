# coding=utf-8
import rarfile, os, re, shutil, zipfile
from os import listdir

# _*_ coding: utf-8 _*_

"""
@Author: Wave Zhou
"""


# param(压缩包所在文件夹的源位置，指定压缩包解压后存放文件的目标位置，要从压缩包中匹配出的文件名构成的数组)
# @author周浪
class BatchDecompression(object):
    def __int__(self):
        super(BatchDecompression, self)

    def __init__(self, sourcedir, targetdir, sample):
        self.source = sourcedir
        self.target = targetdir
        self.sample = sample
        self.flag = None
        self.valid_file_list = list()

    def batchExt(self):
        if len(self.sample) < 1:
            raise Exception('第三个参数数组不能为空')
        filenames = listdir(self.source)
        for file in filenames:
            if '行情' in file:
                continue
            path1 = os.path.join(self.source, file)
            if file.endswith('rar'):
                rf = rarfile.RarFile(path1)  # 待解压文件
                rf.extractall(self.target)  # 解压指定文件路径
            elif file.endswith('zip'):
                zf = zipfile.ZipFile(path1)
                zf.extractall(self.target)
                zf.close()
        folders = listdir(self.target)
        if len(self.sample) == 1:
            pattern = r"" + self.sample[0]  # 指定匹配模板
            self.flag = True
            self.recursion_search(folders, pattern)

        else:
            for i in range(len(self.sample)):
                if i == len(self.sample) - 1:
                    self.flag = True  # 最后一次遍历清楚压缩包
                pattern = r"" + self.sample[i]
                self.recursion_search(folders, pattern)

        for fd in folders:  # 最后清楚多余文件夹和文件
            if os.path.isdir(os.path.join(self.target, fd)):
                shutil.rmtree(os.path.join(self.target, fd))
            elif fd not in self.valid_file_list:
                os.remove(os.path.join(self.target, fd))

    def recursion_search(self, folders, pattern):
        foders_tmp = folders[:]  # 为了避免数组中元素删除造成的指针跳位
        for fd in foders_tmp:
            if fd.endswith('rar') or fd.endswith('zip'):
                if self.flag:
                    os.remove(os.path.join(self.target, fd))
                    folders.remove(fd)
                continue
            elif os.path.isfile(os.path.join(self.target, fd)):
                if re.search(pattern, fd) and re.search(pattern, fd).group(0) == pattern:
                    self.valid_file_list.append(fd)
                continue
            path2 = os.path.join(self.target, fd)
            self.rec_find(path2, pattern)

    def rec_find(self, path2, pattern):  # 开始递归查找想保留的文件内容
        file_names = os.listdir(path2)
        for fs in file_names:
            if os.path.isdir(os.path.join(path2, fs)):
                self.rec_find(os.path.join(path2, fs), pattern)
            elif re.search(pattern, fs) and re.search(pattern, fs).group(0) == pattern:
                self.valid_file_list.append(fs)
                shutil.move(os.path.join(path2, fs), os.path.join(self.target, fs))

    # def judge_includedir(self,f):
    #     temp = False
    #     if os.path.isdir(os.path.join(self.target,f)):
    #         temp = True
    #     return temp
    # def judge_includedir(self,folders):
    #     temp = False
    #     for f in folders:
    #         if os.path.isdir(os.path.join(self.target,f)):
    #             temp = True
    #     return temp
    # def deal_no_dir(self,files,pattern):
    #     for f in files:
    #         if  not (re.search(pattern, f) and re.search(pattern, f).group(0) == pattern):
    #             os.remove(os.path.join(self.target,f))
