# -*- coding: utf-8 -*-  
import os
import shutil


def file_name(file_dir):  
  for root, dirs, files in os.walk(file_dir): 
    print(root) #当前目录路径 
    print(dirs) #当前路径下所有子目录 
    print(files) #当前路径下所有非目录子文件
    for file in files:
      print(str(root)+"\\"+str(file))
      print(file)
      shutil.copy(str(root)+"\\"+str(file),r'C:\Users\MYSQL\Documents\Desktop\测试文件夹')

#file_name(r'Z:\估值专用邮箱数据\久铭邮件账户分类缓存\收件日20211018 下午 收盘后\久铭产品交割单20211018\中金普通账户')


