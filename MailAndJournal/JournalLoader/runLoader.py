# -*- encoding: UTF-8 -*-
import os
import datetime

from extended.wrapper.MySQL import MySQL
from RealtimeLoader import RealTimeLoader

current_day = datetime.date(2022, 6, 28)
last_day = datetime.date(2022, 6, 27)

# ---- ---- #

base_folder = r'D:\FundValuation\读取缓存'
manual_folder = r'D:\FundValuation\DebugOut'
db = MySQL('root', 'jm3389', '192.168.1.31', 3306)
loader = RealTimeLoader(
    db=db,
    path_view=r'D:\FundValuation\MassCacheDir\久铭产品交割单',
    path_collection=r'D:\FundValuation\MassCacheDir\整理产品对账单',
    path_valuation_copy=r'D:\FundValuation\Documents\历史数据\产品估值表副本',
)
# 输出读取结果至
# db.read_pd_query(
#     'jm_fundmanagement', """
#     SELECT 账户类型, 产品, 日期, 现金资产
#     FROM 原始普通账户资金记录 WHERE 日期 = '{}'
#     ;""".format(current_day)
# ).to_excel(
#     os.path.join(r'D:\MassCacheDSDSir\久铭产品交割单', '原始普通账户资金记录.xlsx'),
#     index=False,
# )
# db.read_pd_query(
#     'jm_fundmanagement', """
#     SELECT 账户类型, 产品, 日期, 现金资产
#     FROM 原始两融账户资金记录 WHERE 日期 = '{}'
#     ;""".format(current_day)
# ).to_excel(
#     os.path.join(r'D:\MassCacheDir\久铭产品交割单', '原始两融账户资金记录.xlsx'),
#     index=False,
# )

db.read_pd_query(
    'jm_fundmanagement', """
    SELECT 账户类型, 产品, 日期, 现金资产
    FROM 原始普通账户资金记录 WHERE 日期 = '{}'
    ;""".format(current_day)
).to_excel(
    os.path.join(r'D:\FundValuation\MassCacheDir\久铭产品交割单', '原始普通账户资金记录.xlsx'),
    index=False,
)
db.read_pd_query(
    'jm_fundmanagement', """
    SELECT 账户类型, 产品, 日期, 现金资产
    FROM 原始两融账户资金记录 WHERE 日期 = '{}'
    ;""".format(current_day)
).to_excel(
    os.path.join(r'D:\FundValuation\MassCacheDir\久铭产品交割单', '原始两融账户资金记录.xlsx'),
    index=False,
)



loader.loading(
    os.path.join(base_folder, '久铭产品交割单{}'.format(current_day.strftime('%Y%m%d'))),
    current_day, last_day,
)

# from Loader import JournalLoader
#
# base_folder = r'D:\NutStore\久铭产品交割单\暂存\2019年'
# current_day = datetime.date(2019, 8, 1)
# last_day = datetime.date(2019, 7, 31)
#
# loader = JournalLoader(MySQL('root', 'jm3389', '192.168.1.31', 3306))
# # ---- ---- #
#
# loader.load_account_statement(os.path.join(
#     base_folder, '久铭产品交割单{}'.format(current_day.strftime('%Y%m%d'))),
#     current_day, last_day,
# )
# loader.load_valuation_sheet(os.path.join(
#     base_folder, '久铭产品交割单{}'.format(current_day.strftime('%Y%m%d'))),
#     current_day, last_day,
# )
