import pandas as pd
import pymysql
import numpy as np
import save_to_excel
import re


conn = pymysql.connect(host='192.168.1.31',database='jiuming_ta_new', user='root', password='jm3389', charset='utf8', port=3306)
sql = 'SELECT * FROM `申赎流水表` WHERE name LIKE \'静康%\''

shenshu_flow = pd.read_sql(sql,conn)
shenshu_flow['institution'] = '静康'
shenshu_flow.rename(columns={'name':'产品','date':'日期','idnumber':'证券代码','product_name':'证券名称','type':'交易类别',
                             'amount':'发生金额','netvalue':'净值','share':'份额','institution':'机构'}, inplace=True)
shenshu_flow = shenshu_flow[['产品','机构','日期','证券代码','证券名称','交易类别','发生金额','净值','份额']]
print(shenshu_flow)

for ind in range(len(shenshu_flow)):
    shenshu_flow['产品'][ind] = re.search(r"(.*)私募证券投资基金",shenshu_flow['产品'][ind]).group(1)
    if len(shenshu_flow['产品'][ind])>5:
        shenshu_flow['产品'][ind] = shenshu_flow['产品'][ind][:6]
    else:
        shenshu_flow['产品'][ind] = shenshu_flow['产品'][ind][:4]
    try:
        shenshu_flow['证券名称'][ind] = re.search(r"(.*)私募证券投资基金",shenshu_flow['证券名称'][ind]).group(1)
        if len(shenshu_flow['证券名称'][ind])>5:
            shenshu_flow['证券名称'][ind] = shenshu_flow['证券名称'][ind][2:]
    except AttributeError:
        try:
            shenshu_flow['证券名称'][ind] = re.search(r"(.*)证券投资基金",shenshu_flow['证券名称'][ind]).group(1)
            if len(shenshu_flow['证券名称'][ind])>5:
                shenshu_flow['证券名称'][ind] = shenshu_flow['证券名称'][ind][2:]
        except AttributeError:
            shenshu_flow['证券名称'][ind] = re.search(r"(.*)私募基金",shenshu_flow['证券名称'][ind]).group(1)
            shenshu_flow['证券名称'][ind] = shenshu_flow['证券名称'][ind][2:]



shenshu_flow.loc[shenshu_flow['交易类别']=='申购','净值']=np.nan
shenshu_flow.loc[shenshu_flow['交易类别']=='申购','份额']=np.nan
shenshu_flow.loc[shenshu_flow['交易类别']=='赎回','净值']=np.nan
shenshu_flow.loc[shenshu_flow['交易类别']=='赎回','发生金额']=np.nan
shenshu_flow = shenshu_flow[shenshu_flow['交易类别']!='份额转入']
shenshu_flow = shenshu_flow[shenshu_flow['交易类别']!='份额转出']
shenshu_flow = shenshu_flow.sort_values(by='日期',ascending=True)
shenshu_flow = shenshu_flow.reset_index(drop=True)
print(shenshu_flow)


path_xlsx = r'D:\test\yimi\基金交易流水\静康申赎流水计划.xlsx'
save_to_excel.tosheet(path_xlsx,shenshu_flow)


