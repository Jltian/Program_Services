# -*- encoding: UTF-8 -*-
import datetime

import pandas as pd

from core.Environment import Environment
from sheets.raws.RawNormal import RawNormalFlow
from utils.Constants import *


PATH = r'C:\Download\test.xlsx'

env = Environment()
pd_data = pd.read_excel(PATH, sheet_name='test')
for i in pd_data.index:
    date_str = str(pd_data.loc[i, '清算周期'])
    obj = RawNormalFlow(
        product='稳健22号', institution='中泰',
        date=datetime.datetime.strptime(date_str, '%Y%m%d').date(),
        security_code=pd_data.loc[i, '证券代码'], security_name=pd_data.loc[i, '证券名称'],
        trade_class=pd_data.loc[i, '业务名称'], trade_price=pd_data.loc[i, '成交价格'],
        trade_volume=pd_data.loc[i, '成交数量'],  trade_amount=pd_data.loc[i, '成交金额'],
        cash_move=pd_data.loc[i, '清算金额'], currency='RMB',
    )
    # if obj.date != datetime.date(2018, 7, 27):
    #     continue
    print(obj)
    # print(pd_data.iloc[i, ])
    # print(pd_data.loc[i, '牛卡号'])
    env.data_base.execute(DataBaseName.management, obj.form_insert_sql('原始普通流水记录'))

env.exit()
