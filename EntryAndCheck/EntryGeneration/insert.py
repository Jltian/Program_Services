import pymysql
from WindPy import *

w.start();
a = w.tdays("2021-01-01","2023-01-01").Times;
b = 0


#打开数据库连接
db = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='test', charset='utf8')
cursor = db.cursor()  # 使用cursor()方法获取操作游标



for i in a:
    b = b + 1;
    sql = "INSERT INTO `trade_date` (`id`, `date`) VALUES ('%d', '%s');"%(b,i)
    cursor.execute(sql)
#info = cursor.fetchall()
    db.commit()
cursor.close()  # 关闭游标
db.close()  # 关闭数据库连接