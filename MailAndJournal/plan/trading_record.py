import pymysql
import pandas as pd
import numpy as np
from decimal import Decimal
import datetime

import save_to_excel

conn = pymysql.connect(host='192.168.1.31', database='jm_fundmanagement', user='root', password='jm3389', charset='utf8',
                       port=3306)
conn1 = pymysql.connect(host='192.168.1.31', database='jiuming_valuation', user='root', password='jm3389', charset='utf8',
                        port=3306)
conn2 = pymysql.connect(host='192.168.1.31', database='jiuming_journal', user='root', password='jm3389', charset='utf8',
                        port=3306)
conn3 = pymysql.connect(host='192.168.1.31', database='jiuming_ta_new', user='root', password='jm3389', charset='utf8',
                        port=3306)
conn4 = pymysql.connect(host='192.168.1.31', database='jingjiu_ta', user='root', password='jm3389', charset='utf8',
                        port=3306)

start_time = '2020-08-18'
end_time = '2020-08-28'


def date_sql(time):
    return "\'" + time + "\'"


def date_to_path(time):
    LIST = time.split('-')
    m = LIST[1]
    d = LIST[2]
    return m + d


sql1 = 'select * from `基金交易流水` where 日期 between  {} and {}'.format(date_sql(start_time), date_sql(end_time))
sql2 = 'select * from `行情表`'
sql3 = 'select * from `净值表`'
sql4 = 'select * from `产品要素表`'
sql5 = 'select * from `静久净值表`'

valuation_flow = pd.read_sql(sql1, conn2)
journal_flow = pd.read_sql(sql1, conn2)
net_value_frame2 = pd.read_sql(sql3, conn3)
net_value_frame3 = pd.read_sql(sql5, conn4)
net_value_frame = pd.merge(net_value_frame2, net_value_frame3, on='日期')
product_id = pd.read_sql(sql4, conn3)
product_id2 = pd.read_sql(sql4, conn4)

valuation_flow = valuation_flow[['投资人', '机构名称', '产品代码', '产品名称', '交易类型', '日期', '发生金额', '净值', '份额']]
journal_flow = journal_flow[['投资人', '机构名称', '产品代码', '产品名称', '交易类型', '日期', '发生金额', '净值', '份额']]

frame = [valuation_flow, journal_flow]
flow = pd.concat(frame, sort=False)
flow = flow.drop_duplicates(subset=['投资人', '机构名称', '产品名称', '交易类型', '日期'], keep='first')
flow = flow.sort_values(by='日期', ascending=True)
flow = flow.reset_index(drop=True)

diction = {}
diction2 = {}
for ind in range(len(product_id)):
    diction[product_id['产品简称'][ind]] = product_id['产品代码'][ind]
for ind in range(len(product_id2)):
    diction2[product_id2['产品简称'][ind]] = product_id2['产品代码'][ind]
diction.update(diction2)
diction.update(
    {'久铭50指数': 'SCJ125', '长安鑫垚': '004908.OF', '长安鑫垚C类': '004908.OF', '长安鑫恒C类': '004898.OF',
     '泰达宏利货币B': '000700.OF', '长安鑫恒': '004898.OF', '浦睿1号': 'Y180555.OF', '久铭创新稳健1号': 'SGF044',
     '合晟同晖1号': 'S22497', '嘉实快线货币A': '000917', }
)

for ind in range(len(flow)):
    if len(flow['产品名称'][ind]) >= 6 and '指数' not in flow['产品名称'][ind]:
        flow.loc[ind, '产品名称'] = flow.loc[ind, '产品名称'].replace('久铭', '')
    else:
        pass
    if '静康' in flow['投资人'][ind]:
        flow.loc[ind, '机构名称'] = '静康'
    else:
        flow.loc[ind, '机构名称'] = '久铭'
    flow.loc[ind, '产品代码'] = diction[flow['产品名称'][ind]]

for flow_ind in range(0, len(flow)):
    for value_ind in range(0, len(net_value_frame)):
        if flow['日期'][flow_ind] == net_value_frame['日期'][value_ind]:
            date = flow['日期'][flow_ind]
            try:
                try:
                    flow.loc[flow_ind, '净值'] = np.nan
                    flow.loc[flow_ind, '净值'] = net_value_frame[flow['产品名称'][flow_ind]][value_ind]
                except TypeError:
                    pass
                if flow['净值'][flow_ind] is None:
                    flow.loc[flow_ind, '净值'] = net_value_frame3[flow['产品名称'][flow_ind]][value_ind]
            except KeyError:
                pass
    if np.isnan(flow.loc[flow_ind, '净值']):
        print('缺少{}净值,时间：{}'.format(flow.loc[flow_ind, '产品名称'], flow.loc[flow_ind, '日期']))
        flow.loc[flow_ind, '净值'] = \
            input("请输入{}产品，{}日期的净值".format(flow.loc[flow_ind, '产品名称'], flow.loc[flow_ind, '日期']))
        # raise AssertionError

for flow_ind in range(0, len(flow)):
    if flow.loc[flow_ind, '交易类型'] == '申购' or flow.loc[flow_ind, '交易类型'] == '基金转入':
        assert np.isnan(flow.loc[flow_ind, '份额']), \
            '日期{} ,产品{} ,交易类型{} ,份额{}应为空值'.format(flow.loc[flow_ind, '日期'], flow.loc[flow_ind, '投资人'],
                                                flow.loc[flow_ind, '交易类型'], flow.loc[flow_ind, '份额'])
    elif flow.loc[flow_ind, '交易类型'] == '赎回' or flow.loc[flow_ind, '交易类型'] == '基金转出':
        assert np.isnan(flow.loc[flow_ind, '发生金额']) , \
            '日期{} ,产品{} ,交易类型{} ,发生金额应为空值'.format(flow.loc[flow_ind, '日期'], flow.loc[flow_ind, '投资人'],
                                                  flow.loc[flow_ind, '交易类型'])
    else:
        print('日期{} ,产品{} ,交易类型{} 未知的交易类型'.format(flow.loc[flow_ind, '日期'], flow.loc[flow_ind, '投资人'],
                                                  flow.loc[flow_ind, '交易类型']))
        raise AssertionError

flow.rename(columns={'投资人': '产品', '机构名称': '机构', '产品代码': '证券代码', '产品名称': '证券名称', '交易类型': '交易类别'},
            inplace=True)
flow = flow[['产品', '机构', '日期', '证券代码', '证券名称', '交易类别', '发生金额', '净值', '份额']]

for flow_ind in range(len(flow)):
    if np.isnan(flow['发生金额'][flow_ind]):
        flow.loc[flow_ind, '发生金额'] = float(flow['净值'][flow_ind]) * float(flow['份额'][flow_ind])
    elif np.isnan(flow['份额'][flow_ind]):
        flow.loc[flow_ind, '份额'] = flow['发生金额'][flow_ind] / flow['净值'][flow_ind]
    else:
        raise AssertionError
decimals = pd.Series([2, 3, 2], index=['发生金额', '净值', '份额'])
for flow_ind in range(len(flow)):
    flow.loc[flow_ind, '发生金额'] = Decimal(flow['发生金额'][flow_ind]).quantize(Decimal('0.00'))
    flow.loc[flow_ind, '净值'] = Decimal(flow['净值'][flow_ind]).quantize(Decimal('0.000'))
    flow.loc[flow_ind, '份额'] = Decimal(flow['份额'][flow_ind]).quantize(Decimal('0.00'))

jiuming_flow = flow[flow['机构'] != '静康']
jingkang_flow = flow[flow['机构'] == '静康']
jiuming_flow = jiuming_flow.reset_index(drop=True)
jingkang_flow = jingkang_flow.reset_index(drop=True)

path_jiuming = r'D:\Documents\实习生-金融工程\Desktop\交易记录\场外基金交易记录\场外基金交易记录{}-{}.xlsx'.format(date_to_path(start_time),
                                                                                        date_to_path(end_time))
save_to_excel.tosheet(path_jiuming, jiuming_flow)

path_jingkang = r'D:\Documents\实习生-金融工程\Desktop\交易记录\静康场外基金交易记录\静康场外基金交易记录{}-{}.xlsx'.format(date_to_path(start_time),
                                                                                             date_to_path(end_time))
save_to_excel.tosheet(path_jingkang, jingkang_flow)
