import pandas as pd
from sqlalchemy import create_engine
import pymysql
from WindPy import *
import time
import datetime
import warnings
import math

# 业绩报酬预提 专享10 王顺兴（这个产品只有这一个客户，是专户，只收取管理费），久铭9 李孟英 （同样是只有一个客户，专户，只收取管理费）
warnings.filterwarnings('ignore')
end_date = datetime.date(2022, 6, 29)
t = str(end_date)

conn1 = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='jiuming_ta_new', charset='utf8')
conn2 = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='jingjiu_ta', charset='utf8')
conn3 = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='jiuming_ta_fee', charset='utf8')
engine1 = create_engine('mysql+pymysql://root:jm3389@192.168.1.31/jiuming_ta_new')
engine2 = create_engine('mysql+pymysql://root:jm3389@192.168.1.31/jingjiu_ta')
engine3 = create_engine('mysql+pymysql://root:jm3389@192.168.1.31/jiuming_ta_fee')


def update_info(conn, engine,t):
    # sql_product_info_org = 'select * from 产品要素表'
    # product_info_org = pd.read_sql(sql=sql_product_info_org, con=conn)
    # sql_product_info_upd = 'select * from 产品要素修改表 where 日期 <= \'{}\''.format(t)
    # product_info_upd = pd.read_sql(sql=sql_product_info_upd, con=conn)
    # product_info_upd = product_info_upd.sort_values(by='序号', ascending=False)
    # product_info_upd = product_info_upd.drop_duplicates(subset=['产品简称','产品代码','修改类型'])
    # for index,row in product_info_upd.iterrows():
    #     product_name, product_code, update_type, update_info = row['产品简称'], row['产品代码'], row['修改类型'], row['修改信息']
    #     product_info_org[update_type][(product_info_org['产品简称'] == product_name) & (product_info_org['产品代码'] == product_code)] = update_info
    # cursor = conn.cursor()
    # sql = 'DELETE FROM `最新产品要素表`;'
    # cursor.execute(sql)
    # conn.commit()
    # cursor.close()
    # # product_info_org.to_sql(name='最新产品要素表', con=engine, if_exists='replace', index=False)
    # product_info_org.to_sql(name='最新产品要素表', con=engine, if_exists='append', index=False)

    sql_customer_info_org = 'select * from 客户信息表'
    customer_info_org = pd.read_sql(sql=sql_customer_info_org, con=conn)
    sql_customer_info_upd = 'select * from 客户信息修改表 where 日期 <= \'{}\''.format(t)
    customer_info_upd = pd.read_sql(sql=sql_customer_info_upd, con=conn)
    customer_info_upd = customer_info_upd.sort_values(by='日期', ascending=False)
    customer_info_upd = customer_info_upd.drop_duplicates(subset=['姓名','证件号','修改类型'])
    for index, row in customer_info_upd.iterrows():
        customer_name, customer_code, update_type, update_info = row['姓名'], row['证件号'], row['修改类型'], row['修改信息']
        customer_info_org[update_type][(customer_info_org['姓名'] == customer_name) & (customer_info_org['证件号'] == customer_code)] = update_info
    cursor = conn.cursor()
    sql = 'DELETE FROM `最新客户信息表`;'
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    # customer_info_org.to_sql(name='最新客户信息表', con=engine, if_exists='replace', index=False)
    customer_info_org.to_sql(name='最新客户信息表', con=engine, if_exists='append', index=False)


def save_to_mysqls(journals,conn):
    cursor = conn.cursor()
    sql='insert into `业绩基准表` (日期,`000300.SH`,`SPX.GI`,`HSI.HI`,`一年期定期存款利率`) values(%s,%s,%s,%s,%s)'
    cursor.executemany(sql, journals)
    conn.commit()
    cursor.close()


def update_performance(conn, last_date: datetime.date):
    code=["000300.SH","SPX.GI","HSI.HI"]
    journal=[]
    cursor = conn.cursor()
    cursor.execute('select max(日期) from 业绩基准表')
    d=cursor.fetchall()                                             #### 接收全部的返回结果行
    d=d[0][0]+datetime.timedelta(days=1)
    dd=(last_date - d).days

    for ddd in range(dd):
        journal1=[]
        dddd = d + datetime.timedelta(days=ddd)
        journal1.append(dddd)
        for i in code:
            data1=w.wsd(i, "close", dddd, dddd, "Days=Alldays")
            data11=data1.Data[0][0]
            journal1.append(data11)
        journal1.extend([0.0, ])
        if type(journal1[1]) is not str:
            journal.append(journal1)
    print(journal)
    return (journal)

w.start()
update_info(conn1, engine1, t)
update_info(conn2, engine2, t)
save_to_mysqls(update_performance(conn1, last_date=end_date + datetime.timedelta(days=1)),conn1)
cursor = conn1.cursor()
cursor.execute('call `更新星期五表`(%s)',(t))
conn1.commit()
cursor.close()
cursor = conn3.cursor()
cursor.execute('call `weekly_performence_fee`(%s)',(t))

conn3.commit()
cursor.close()
w.stop()
