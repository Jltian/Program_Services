# _*_ coding: utf-8 _*_

"""
@Author: Wave Zhou
"""

import shutil, datetime, os, logging

# 同一个subfolder整个文件夹的搬运不会搬第二次


end_date_str = str(datetime.datetime.now().date())
logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                    filename='D:\\FundValuation\\debugOut\\{}-log.txt'.format(end_date_str),
                    filemode='a',  ##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    # a是追加模式，默认如果不写的话，就是追加模式
                    format=
                    '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    # 日志格式
                    )


class Move(object):
    def __init__(self, sourcefile):
        # 如果sourcefile是以目录结尾的
        global des
        path = 'D:\FundValuation\DebugOut'
        between = str(datetime.datetime.now().date()) + '读'
        if not str(sourcefile).split(os.path.sep)[-1].__contains__("."):
            sub_folder = str(sourcefile).split(os.path.sep)[-1]
            des = os.path.join(path, between, sub_folder)
            # if not os.path.exists(os.path.join(des,sub_folder)):
            #     os.makedirs(os.path.join(des,sub_folder))
            # try:
            shutil.move(sourcefile, des)
        # except shutil.Error:
        #     con = '\\'
        #     des_array = des.split('\\')[:-1]
        #     print(con.join(des_array))
        #     shutil.move(sourcefile, os.path.join(con.join(des_array),between))
        else:  # 如果sourcefile是以文件结尾的
            sub_folder = str(sourcefile).split(os.path.sep)[-2]
            des = os.path.join(path, between, sub_folder)
            if not os.path.exists(des):
                 os.makedirs(des)
            if not os.path.exists(os.path.join(des,str(sourcefile).split(os.path.sep)[-1])):
                shutil.move(sourcefile, des)
    def output_log(self,message):
        logging.debug(message)

if __name__ == '__main__':
    m = Move("D:\FundValuation\Test\demo1.txt")
    m.output_log("搬迁啦")
