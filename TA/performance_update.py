import pymysql
from WindPy import *
import time
import datetime
import warnings

warnings.filterwarnings('ignore')
conn = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='jiuming_ta_new', charset='utf8')

w.start()
t='2020-2-12'

def save_to_mysqls(journals):
    cursor = conn.cursor()
    sql='insert into `业绩基准表` (日期,`000300.SH`,`SPX.GI`,`HSI.HI`,`一年期定期存款利率`) values(%s,%s,%s,%s,%s)'
    cursor.executemany(sql, journals)
    conn.commit()
    cursor.close()

code=["000300.SH","SPX.GI","HSI.HI"]
journal=[]
cursor = conn.cursor()
cursor.execute('select max(日期) from 业绩基准表')
d=cursor.fetchall()                                             ####接收全部的返回结果行
d=d[0][0]+datetime.timedelta(days=1)
dd=(datetime.date.today()-d).days

for ddd in range(dd):
    journal1=[]
    dddd = d + datetime.timedelta(days=ddd)
    journal1.append(dddd)
    for i in code:
        data1=w.wsd(i,"close", dddd,dddd,"Days=Alldays")
        data11=data1.Data[0][0]
        journal1.append(data11)
    journal1.extend([''])
    if type(journal1[1]) is not str:
        journal.append(journal1)
print(journal)
w.stop()


save_to_mysqls(journal)

cursor = conn.cursor()
cursor.execute('call `更新星期五表`(%s)',(t))
conn.commit()
cursor.close()
