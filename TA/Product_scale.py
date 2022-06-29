import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
import datetime
import pymysql
import warnings
from sqlalchemy import create_engine
warnings.filterwarnings("ignore")
# 创建连接
conn = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='jiuming_ta_fee')
engine = create_engine('mysql+pymysql://root:jm3389@192.168.1.31:3306/jiuming_ta_fee?charset=utf8')
productscale_column = ['日期', '产品名称', '产品净值', '总份额', '产品总资产']
productscale = pd.DataFrame(columns=productscale_column)
products = ['久铭6号']
dates = ['2019-12-27']

cur = conn.cursor()
products_all = 'SELECT a.`产品简称`,a.`产品全称` FROM jiuming_ta_new.`产品要素表` a '
products_all = pd.read_sql(products_all, conn)
# products_short = products['产品简称'].values.tolist()
# products_long = products['产品全称'].values.tolist()
dict_products = products_all.set_index('产品简称').T.to_dict('records')[0]
if products == []:
    products = list(dict_products)
    print(products)
data = []

for d in dates:
    for p in products:
        netvalues = 'SELECT jiuming_ta_new.`净值表`.{} FROM jiuming_ta_new.`净值表` WHERE jiuming_ta_new.`净值表`.`日期` = \'{}\' ;'.format(p, d)
        netvalues = pd.read_sql(netvalues, conn).values.tolist()[0][0]
        share = 'SELECT sum(share) FROM jiuming_ta_new.`申赎流水表` a WHERE a.`product_name`=\'{}\' and a.`confirmation_date` <= \'{}\';'.format(dict_products[p],d)
        share = pd.read_sql(share, conn).values.tolist()[0][0]
        assets = round(netvalues*share,2)
        data.append([d, p, netvalues, share, assets])


data=DataFrame(data)
data.columns = productscale_column

writer = pd.ExcelWriter('产品规模.xlsx')
data.to_excel(writer, sheet_name='产品规模')
writer.save()