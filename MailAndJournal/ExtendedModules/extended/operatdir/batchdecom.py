#coding=utf-8
import rarfile,os,re,shutil
from os import listdir
class BatchDecompression(object):
    def __int__(self):
       super(BatchDecompression, self)
    def __init__(self,sourcedir,targetdir,sample):
        self.source = sourcedir
        self.target = targetdir
        self.sample = sample
    def batchExt(self):
        filenames = listdir(self.source)
        for file in filenames:
            path1 = os.path.join(self.source,file)
            rf = rarfile.RarFile(path1)  # 待解压文件
            rf.extractall(self.target)#解压指定文件路径
        folders = listdir(self.target)
        pattern = r"" + self.sample#指定匹配模板
        self.recursion_search(folders,pattern)
    def recursion_search(self,folders,pattern):
        for fd in folders:
            if fd.endswith("rar" or "zip"):
                os.remove(os.path.join(self.target, fd))
                continue
            path2 = os.path.join(self.target, fd)
            self.rec_find(path2,pattern)
            shutil.rmtree(os.path.join(self.target, fd))
    def rec_find(self,path2,pattern):
        file_names = os.listdir(path2)
        for fs in file_names:
            if os.path.isdir(os.path.join(path2, fs)):
                self.rec_find(os.path.join(path2,fs),pattern)
            elif re.search(pattern, fs) and re.search(pattern, fs).group(0) == self.sample:
                shutil.move(os.path.join(path2,fs), os.path.join(self.target,fs))

