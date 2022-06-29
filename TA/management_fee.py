import numpy as np
import pandas as pd
import datetime
import pymysql
import warnings
from sqlalchemy import create_engine
warnings.filterwarnings("ignore")
# 创建连接
conn = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='jiuming_ta_fee')
engine = create_engine('mysql+pymysql://root:jm3389@192.168.1.31:3306/jiuming_ta_fee?charset=utf8')

managementfee_column = ['日期', '产品名称', '产品净值', '客户名称', '客户证件号', '申购ID', '代销机构', '客户经理', '申赎前份额', '管理费率', '当日管理费', '分摊管理费率', '当日待分摊管理费', '当日分摊管理费', '序号']
managementfee = pd.DataFrame(columns=managementfee_column)
start = '2019-1-1'
end = '2019-12-31'
start = datetime.datetime.strptime(start, "%Y-%m-%d").date()
end = datetime.datetime.strptime(end, "%Y-%m-%d").date()
start_the_day_before = start - datetime.timedelta(days=1)


def dateRange(beginDate, endDate):
    dates = []
    dt = beginDate
    while dt <= endDate:
        dates.append(dt)
        dt = dt + datetime.timedelta(1)
    return dates


create_managementfee_table = 'CREATE TABLE 管理费分摊表test (日期 date,产品名称 varchar(25),产品净值 DECIMAL(12,4),客户名称 varchar(25),客户证件号 varchar(25),' \
      '申购ID varchar(25),代销机构 varchar(25),客户经理 varchar(25),申赎前份额 DECIMAL(22,2),管理费率 DECIMAL(12,8),当日管理费 DECIMAL(22,2),' \
      '分摊管理费率 DECIMAL(12,8),当日待分摊管理费 DECIMAL(22,2),当日分摊管理费 DECIMAL(22,2),序号 INT NOT NULL AUTO_INCREMENT,PRIMARY KEY (序号),INDEX(申购ID)) ENGINE=InnoDB default charset=utf8;'

cur = conn.cursor()
cur.execute(create_managementfee_table)
dates = dateRange(start_the_day_before, end)
products = 'SELECT a.`产品简称`,a.`产品全称` FROM jiuming_ta_new.`产品要素表` a '
products = pd.read_sql(products, conn)
products_short = products['产品简称'].values.tolist()
products_long = products['产品全称'].values.tolist()
for p in range(len(products_short)):
      netvalues = 'SELECT jiuming_ta_new.`净值表`.`日期`, jiuming_ta_new.`净值表`.{} FROM jiuming_ta_new.`净值表` WHERE jiuming_ta_new.`净值表`.`日期` BETWEEN \'{}\' AND \'{}\';'.format(products_short[p], start_the_day_before, end)
      netvalues = pd.read_sql(netvalues, conn)
      purchase_ids = 'SELECT a.`name`,a.idnumber,a.`purchase_id` FROM jiuming_ta_new.`申赎流水表` a WHERE a.`product_name`=\'{}\' GROUP BY a.`purchase_id`;'.format(products_long[p])
      purchase_ids = pd.read_sql(purchase_ids, conn)
      customers = purchase_ids['name'].values.tolist()
      customer_ids = purchase_ids['idnumber'].values.tolist()
      purchase_ids = purchase_ids['purchase_id'].values.tolist()
      mm = pd.DataFrame(columns=managementfee_column)
      for p_id in range(len(purchase_ids)):
            m = pd.DataFrame(columns=managementfee_column)
            m['日期'] = dates
            m['产品名称'] = products_short[p]
            m = pd.merge(m, netvalues, how='left', on='日期')
            m['产品净值'] = m[products_short[p]]
            del m[products_short[p]]
            m['客户名称'] = customers[p_id]
            m['客户证件号'] = customer_ids[p_id]
            m['申购ID'] = purchase_ids[p_id]
            m['产品净值'] = m['产品净值'].fillna(0)
            null_ids = m[m['产品净值'] == 0].index.tolist()
            if null_ids:
                  for null_id in null_ids:
                        if null_id != 0:
                              m.loc[null_id,'产品净值']=m.loc[null_id-1,'产品净值']
            m['申赎前份额'] = m['申赎前份额'].fillna(0)
            mm = mm.append(m)
            #managementfee = managementfee.append(m)
      mm.to_sql(name='管理费分摊表test', con=engine, schema='jiuming_ta_fee', if_exists='append', index=False)

share = 'UPDATE `管理费分摊表test` SET `申赎前份额`= (SELECT sum(share) FROM jiuming_ta_new.`申赎流水表` a WHERE `管理费分摊表test`.日期 >= a.`confirmation_date` and a.`purchase_id`=管理费分摊表test.`申购ID`)'
seller = 'UPDATE `管理费分摊表test` a, jiuming_ta_new.`最新客户信息表` b SET a.`客户经理`= b.`客户经理`,a.`代销机构`= b.`代销机构` WHERE b.证件号 = a.`客户证件号`'
managementfee_rate = 'UPDATE `管理费分摊表test` SET `管理费率`= jiuming_ta_new.`最新管理费率`(`日期`,`产品名称`)'
managementfee_today = 'UPDATE `管理费分摊表test` SET `当日管理费`= `产品净值`*`申赎前份额`*`管理费率`/365'
managementfee_share_rate = 'UPDATE `管理费分摊表test` SET `分摊管理费率`= `管理费率`-`管理费返还率`(`日期`,`客户名称`,`产品名称`)'
managementfee_share_today = 'UPDATE `管理费分摊表test` SET `当日待分摊管理费`= `产品净值`*`申赎前份额`*`分摊管理费率`/365,`当日分摊管理费`= 0'
delete_lastday = 'DELETE FROM `管理费分摊表test` WHERE 日期 = \'{}\''.format(end)
adjust_date = 'UPDATE `管理费分摊表test` SET `日期` = DATE_ADD(日期,INTERVAL 1 DAY)'

try:
      cur.execute(share)
      print("份额填充完成")
      cur.execute(seller)
      print("渠道及客户经理填充完成")
      cur.execute(managementfee_rate)
      print("管理费率填充完成")
      cur.execute(managementfee_today)
      print("单日管理费计算完成")
      cur.execute(managementfee_share_rate)
      print("管理费返还率填充完成")
      cur.execute(managementfee_share_today)
      print("单日管理费返还计算完成")
      cur.execute(delete_lastday)
      cur.execute(adjust_date)
except Exception as e:
      conn.rollback()
      print('啊噢，全完了', e)
else:
      conn.commit()
      print('当日待分摊管理费处理成功')
managementfee_share_product = 'SELECT b.日期,a.`产品简称`,b.`当日待分摊管理费` FROM jiuming_ta_new.`产品要素表` a,`管理费分摊表test` b WHERE a.`产品全称` = b.`客户名称` AND b.`当日待分摊管理费`>0'
managementfee_share_product = pd.read_sql(managementfee_share_product, conn)

try:
    managementfee_sharefee_id = []
    for index, row in managementfee_share_product.iterrows():
        #print(row['日期'], row['产品简称'], row['当日待分摊管理费'])
        managementfee_share_data = 'SELECT a.`日期`,a.`产品名称`,a.`客户名称`,a.`申赎前份额`,a.`当日分摊管理费`,a.`序号` FROM 管理费分摊表test a WHERE a.`日期`=\'{}\' AND a.`产品名称`=\'{}\''.format(row['日期'], row['产品简称'])
        managementfee_share_date = pd.read_sql(managementfee_share_data, conn)
        managementfee_share_date = managementfee_share_date.fillna(0)
        managementfee_share_date['当日分摊管理费'] = managementfee_share_date['申赎前份额'] * row['当日待分摊管理费'] / managementfee_share_date['申赎前份额'].sum()
        mf_id = managementfee_share_date[['当日分摊管理费', '序号']][managementfee_share_date['当日分摊管理费'] != 0].values.tolist()
        managementfee_sharefee_id.extend(list(map(tuple, mf_id)))
        print(index / len(managementfee_share_product.index))
    managementfee_share_update = 'UPDATE 管理费分摊表test SET `当日分摊管理费` = `当日分摊管理费` + %s WHERE `序号` = %s'
    cur.executemany(managementfee_share_update, managementfee_sharefee_id)
except Exception as e:
      conn.rollback()
      print('当日分摊管理费处理失败', e)
else:
      conn.commit()
      print('当日分摊管理费处理成功')

