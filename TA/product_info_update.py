import pymysql
import datetime
import warnings
import pandas as pd
from sqlalchemy import create_engine

warnings.filterwarnings('ignore')
conn1 = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='jiuming_ta_new', charset='utf8')
conn2 = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='jingjiu_ta', charset='utf8')
engine1 = create_engine('mysql+pymysql://root:jm3389@192.168.1.31/jiuming_ta_new')
engine2 = create_engine('mysql+pymysql://root:jm3389@192.168.1.31/jingjiu_ta')
t='2021-8-10'

def update_info(conn, engine):
    # sql_product_info_org = 'select * from 产品要素表'
    # product_info_org = pd.read_sql(sql=sql_product_info_org, con=conn)
    # sql_product_info_upd = 'select * from 产品要素修改表 where 日期 <= \'{}\''.format(t)
    # product_info_upd = pd.read_sql(sql=sql_product_info_upd, con=conn)
    # product_info_upd = product_info_upd.sort_values(by='序号', ascending=False)
    # product_info_upd = product_info_upd.drop_duplicates(subset=['产品简称','产品代码','修改类型'])
    # for index,row in product_info_upd.iterrows():
    #     product_name, product_code, update_type, update_info = row['产品简称'], row['产品代码'], row['修改类型'], row['修改信息']
    #     product_info_org[update_type][(product_info_org['产品简称'] == product_name) & (product_info_org['产品代码'] == product_code)] = update_info
    # product_info_org.to_sql(name='最新产品要素表', con=engine, if_exists='replace', index=False)

    sql_customer_info_org = 'select * from 客户信息表'
    customer_info_org = pd.read_sql(sql=sql_customer_info_org, con=conn)
    sql_customer_info_upd = 'select * from 客户信息修改表 where 日期 <= \'{}\''.format(t)
    customer_info_upd = pd.read_sql(sql=sql_customer_info_upd, con=conn)
    customer_info_upd = customer_info_upd.sort_values(by='日期', ascending=False)
    customer_info_upd = customer_info_upd.drop_duplicates(subset=['姓名','证件号','修改类型'])
    for index,row in customer_info_upd.iterrows():
        customer_name, customer_code, update_type, update_info = row['姓名'], row['证件号'], row['修改类型'], row['修改信息']
        customer_info_org[update_type][(customer_info_org['姓名'] == customer_name) & (customer_info_org['证件号'] == customer_code)] = update_info
    customer_info_org.to_sql(name='最新客户信息表', con=engine, if_exists='replace', index=False)

update_info(conn1, engine1)
update_info(conn2, engine2)