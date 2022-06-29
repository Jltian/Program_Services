# # -*- encoding: UTF-8 -*-
# import datetime
# import os
#
# import pandas as pd
#
# from structures import DataList
# from utils.Constants import *
#
#
# class ValuationBoard(object):
#     """把何梦洁的估值表格作为数据源"""
#     file_product_map = {
#         '久铭2号估值表.xlsx': '久铭2号', '久铭3号估值表.xlsx': '久铭3号',
#         '久铭全球1号估值表.xlsx': '全球1号', '久铭收益1号估值表.xlsx': '收益1号',
#         '久铭双盈1号估值表.xlsx': '双盈1号', '久铭稳利2号估值表.xlsx': '稳利2号',
#         '稳健2号估值表.xlsx': '稳健2号', '稳健3号估值表.xlsx': '稳健3号', '稳健5号估值表.xlsx': '稳健5号',
#         '稳健6号估值表.xlsx': '稳健6号', '稳健7号估值表.xlsx': '稳健7号', '稳健8号估值表.xlsx': '稳健8号',
#         '稳健9号估值表.xlsx': '稳健9号', '稳健10号估值表.xlsx': '稳健10号', '稳健11号估值表.xlsx': '稳健11号',
#         '稳健12号估值表.xlsx': '稳健12号', '稳健15号估值表.xlsx': '稳健15号', '稳健16号估值表.xlsx': '稳健16号',
#         '稳健17号估值表.xlsx': '稳健17号', '稳健18号估值表.xlsx': '稳健18号', '稳健19号估值表.xlsx': '稳健19号',
#         '稳健21号估值表.xlsx': '稳健21号', '稳健22号估值表.xlsx': '稳健22号', '稳健31号估值表.xlsx': '稳健31号',
#         '稳健32号估值表.xlsx': '稳健32号', '稳健33号估值表.xlsx': '稳健33号',
#     }
#     __product_file_map__ = None
#
#     def __init__(self, path: str):
#         from core.Environment import Environment
#         from utils import get_logger
#         self.env = Environment.get_instance()
#         self.log = get_logger(self.__class__.__name__)
#         self.data = dict()
#         self.__path__ = path
#
#     @property
#     def product_file_map(self):
#         if ValuationBoard.__product_file_map__ is None:
#             new_d = dict()
#             for file, product in self.file_product_map.items():
#                 new_d[product] = file
#             ValuationBoard.__product_file_map__ = new_d
#         return ValuationBoard.__product_file_map__
#
#     def __sub_path__(self, *args):
#         return os.path.join(self.__path__, *args)
#
#     def __load_product__(self, product: str, date: datetime.date):
#         if product in self.data:
#             pd_data = self.data[product]
#         else:
#             self.log.debug_running('opening', self.product_file_map[product])
#             pd_data = pd.read_excel(self.__sub_path__(self.product_file_map[product]), sheet_name='资产负债表', )
#             pd_data = pd_data[pd_data['日期'] <= pd.Timestamp(date + datetime.timedelta(days=1))]
#             pd_data = pd_data[pd_data['日期'] >= pd.Timestamp(date - datetime.timedelta(days=10))]
#             self.data[product] = pd_data
#         assert isinstance(pd_data, pd.DataFrame)
#         return pd_data
#
#     def __derive_pd_content__(self, pd_data: pd.DataFrame, date: datetime.date, tag: str, shift: int = 0):
#         column_list = list(pd_data.columns)
#         pd_data_line = pd_data[pd_data['日期'] == pd.Timestamp(date)]
#         if len(pd_data_line.index) == 1:
#             pd_data_line = pd_data_line.iloc[0,]
#         elif len(pd_data_line.index) == 2:
#             pd_data_line = pd_data_line.iloc[0,]
#         elif len(pd_data_line.index) == 0:
#             pd_data_line = pd_data[pd_data['日期'] == pd.Timestamp(date - datetime.timedelta(days=1))]
#             if len(pd_data_line.index) == 2:
#                 pd_data_line = pd_data_line.iloc[1,]
#             else:
#                 raise NotImplementedError(str(pd_data_line.head()))
#         else:
#             raise NotImplementedError(str(pd_data_line.head()))
#         try:
#             return float(pd_data_line[column_list.index(tag) + shift])
#         except ValueError as col_not_find:
#             # self.log.debug(str(pd_data.columns))
#             raise col_not_find
#
#     def __search_pd_column__(self, pd_data: pd.DataFrame, key: str):
#         assert len(key) > 0
#         for col in pd_data.columns:
#             if key in col:
#                 return col
#         raise KeyError
#
#     def hist_product_net_value_per_share(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product, date=date)
#         return self.__derive_pd_content__(pd_data, date, '今日单位净值', shift=0)
#
#     def hist_product_net_value(self, product: str, date: datetime.datetime):
#         pd_data = self.__load_product__(product, date=date)
#         return self.__derive_pd_content__(pd_data, date, '申赎前资产类合计', shift=0)
#
#     def hist_product_accumulated_management_fee_payable(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product, date=date)
#         try:
#             if product in ('全球1号', '收益1号', ):
#                 accumulated_fee_tag = '累计固定管理费'
#             elif product in ('稳健18号',):
#                 accumulated_fee_tag = '累计管理费用'
#             else:
#                 accumulated_fee_tag = '累计应付管理费'
#             return self.__derive_pd_content__(pd_data, date, accumulated_fee_tag, shift=0)
#         except ValueError as amf:
#             if self.env.product_board.management_fee_rate(product, date) >= 0.000001:
#                 raise amf
#             else:
#                 return 0
#
#     def hist_product_management_fee_payable(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product, date=date)
#         try:
#             if product in ('全球1号',):
#                 fee_payable_tag = '应付固定管理费'
#             elif product in ('收益1号',):
#                 fee_payable_tag = '固定管理费'
#             elif product in ('稳健18号',):
#                 fee_payable_tag = '应付管理费'
#             else:
#                 fee_payable_tag = '应付管理费'
#             return self.__derive_pd_content__(pd_data, date, fee_payable_tag, shift=0)
#         except ValueError as amf:
#             if self.env.product_board.management_fee_rate(product, date) >= 0.000001:
#             # if self.env.data_base.read_pd_query(
#             #         DataBaseName.transfer_agent_new,
#             #         """select `最新管理费率`('{}', '{}') as 最新管理费率;""".format(date.strftime('%Y-%m-%d'), product)
#             # ).loc[0, '最新管理费率'] > 0:
#                 raise amf
#             else:
#                 return 0
#
#     def hist_product_daily_management_fee_payable(self, product: str, date: datetime.date):
#         return self.hist_product_accumulated_management_fee_payable(
#             product=product, date=date,
#         ) - self.hist_product_accumulated_management_fee_payable(
#             product=product, date=date - datetime.timedelta(days=1))
#
#     def hist_product_daily_management_profit_payable(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product, date=date)
#         paid_tag, for_pay_tag = '已付业绩报酬', '业绩报酬'
#         last_for_pay = self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), for_pay_tag)
#         for_pay = self.__derive_pd_content__(pd_data, date, for_pay_tag)
#         if not is_valid_float(for_pay):
#             return 0
#         elif is_valid_float(last_for_pay):
#             return self.__derive_pd_content__(pd_data, date, paid_tag) \
#                    + for_pay \
#                    - self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), paid_tag) \
#                    - last_for_pay
#         else:
#             return self.__derive_pd_content__(pd_data, date, for_pay_tag)
#
#     def hist_product_management_fee_receivable(self, product: str, fund_name: str, date: datetime.date):
#         pd_data = self.__load_product__(product, date=date)
#         def find_tag(pd_data: pd.DataFrame, fund_name: str):
#             for col in pd_data.columns:
#                 if '应收' in col and '管理费' in col and fund_name.replace('指数', '') in col and '累计' not in col:
#                     return col
#             for col in pd_data.columns:
#                 if '返还' in col and '管理费' in col and fund_name.replace('指数', '') in col and '累计' not in col:
#                     return col
#             return None
#         try:
#             tag = find_tag(pd_data, fund_name)
#             if tag is None:
#                 if (product, fund_name) in [
#                     ('稳健6号', '中证500指数'), ('稳健6号', '沪深300指数'),
#                 ]:
#                     return self.__derive_pd_content__(pd_data, date, '已收{}管理费'.format(fund_name), shift=1)
#                 elif (product, fund_name) in [('稳健12号', '稳健7号'), ]:
#                     return self.__derive_pd_content__(pd_data, date, '应收{}'.format(fund_name))
#                 else:
#                     raise ValueError(fund_name)
#             else:
#                 return self.__derive_pd_content__(pd_data, date, tag, shift=0)
#         except ValueError as rmf:
#             if self.env.product_board.management_fee_rate(fund_name, date) >= 0.000001:
#                 raise rmf
#             else:
#                 return 0
#
#     def hist_product_accumulated_management_fee_receivable(self, product: str, fund_name: str, date: datetime.date):
#         pd_data = self.__load_product__(product, date=date)
#
#         def find_tag(pd_data: pd.DataFrame, fund_name: str):
#             for col in pd_data.columns:
#                 if '累计应收' in col and '管理费' in col and fund_name.replace('指数', '') in col:
#                     return col
#             return None
#         try:
#             tag = find_tag(pd_data, fund_name)
#             if tag is None:
#                 if (product, fund_name) in [
#                     ('稳健6号', '中证500指数'), ('稳健6号', '沪深300指数'),
#                 ]:
#                     return self.__derive_pd_content__(pd_data, date, '已收{}管理费'.format(fund_name), shift=-1)
#                 elif (product, fund_name) in [('稳健12号', '稳健7号'), ]:
#                     raise NotImplementedError
#                 elif (product, fund_name) in [
#                     ('稳健3号', '稳健7号'), ('稳健5号', '稳健7号'), ('稳利2号', '稳健1号'), ('收益1号', '久铭2号'),
#                     ('久铭2号', '稳健23号', )
#                 ]:
#                     return 0
#                 else:
#                     raise ValueError('{} {}'.format(product, fund_name))
#             else:
#                 return self.__derive_pd_content__(pd_data, date, tag, shift=0)
#         except ValueError as rmf:
#             if self.env.product_board.management_fee_rate(fund_name, date) >= 0.000001:
#                 raise rmf
#             else:
#                 return 0
#
#     def hist_product_daily_management_fee_receivable(self, product: str, fund_name: str, date: datetime.date):
#         if (product, fund_name) in [('稳健12号', '稳健7号'), ]:
#             today_rec = self.hist_product_management_fee_receivable(product=product, fund_name=fund_name, date=date,)
#             last_rec = self.hist_product_management_fee_receivable(
#                 product=product, fund_name=fund_name, date=date - datetime.timedelta(days=1),
#             )
#         else:
#             today_rec = self.hist_product_accumulated_management_fee_receivable(
#                 product=product, fund_name=fund_name, date=date,
#             )
#             last_rec = self.hist_product_accumulated_management_fee_receivable(
#                 product=product, fund_name=fund_name, date=date - datetime.timedelta(days=1)
#             )
#         if not is_valid_float(last_rec):
#             last_rec = 0
#         if not is_valid_float(today_rec):
#             raise NotImplementedError('{} {} {} {}'.format(product, fund_name, date, last_rec))
#         assert today_rec >= last_rec, '{} {} {} {} {}'.format(product, fund_name, date, today_rec, last_rec)
#         return today_rec - last_rec
#
#     def __get_fund_column_name__(self, product: str, fund_name: str):
#         if (product, fund_name) in [
#             ('收益1号', '稳健21号'), ('稳健6号', '稳健18号'), ('稳健6号', '稳健22号'), ('稳健16号', '稳健21号'),
#             ('稳健7号', '稳健22号'), ('稳健7号', '稳健16号'), ('收益1号', '稳健22号'),
#         ]:
#             key_tag = fund_name
#         elif product in ('稳健3号', '稳健2号', '稳健5号', '稳健7号', '稳健18号', ):
#             key_tag = '{}市值'.format(fund_name)
#         elif product == '稳健6号' and '稳健' in fund_name:
#             key_tag = '{}市值'.format(fund_name)
#         else:
#             key_tag = '{}基金市值'.format(fund_name)
#         return key_tag
#
#     def hist_product_fund_holding_market_value(self, product: str, fund_name: str, date: datetime.date):
#         pd_data = self.__load_product__(product, date=date)
#         if (product, fund_name) in [('收益1号', '久铭2号'), ]:
#             key_tag = self.__search_pd_column__(pd_data, fund_name)
#         else:
#             key_tag = self.__get_fund_column_name__(product=product, fund_name=fund_name)
#         return self.__derive_pd_content__(pd_data, date=date, tag=key_tag, shift=0)
#
#     def hist_product_fund_holding_net_value_per_unit(self, product: str, fund_name: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         if fund_name in ('中海久铭1号', ):
#             key_tag = '中海-久铭1号信托计划'
#         elif fund_name in ('启元18号', ):
#             key_tag = '启元18号'
#         elif fund_name == '浦江之星289号':
#             key_tag = self.__search_pd_column__(pd_data, '浦江之星')
#         elif fund_name == '同晖1号':
#             key_tag = self.__search_pd_column__(pd_data, '合晟同晖')
#         elif fund_name in ('浦睿1号', '久铭2号'):
#             key_tag = self.__search_pd_column__(pd_data, fund_name)
#         else:
#             key_tag = self.__get_fund_column_name__(product=product, fund_name=fund_name)
#         return self.__derive_pd_content__(pd_data, date=date, tag=key_tag, shift=3)
#
#     def hist_product_bond_holding_price(self, product: str, bond_name: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         if bond_name == '17宝武EB':
#             if product in ('稳健6号', ):
#                 key_tag = '可交换债收盘'
#             else:
#                 key_tag = '宝武eb收盘'
#         else:
#             raise NotImplementedError(bond_name)
#         return self.__derive_pd_content__(pd_data, date=date, tag=key_tag, shift=0)
#
#     # def hist_product_meigu_market_value(self, product: str, date: datetime.date):
#     #     pd_data = self.__load_product__(product=product, date=date)
#     #     return self.__derive_pd_content__(pd_data, date, '美股市值（cny)', shift=0)
#
#     def hist_product_meigu_daily_interest_payable(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '美股市值（cny)'
#         today_paid = (self.__derive_pd_content__(pd_data, date, tag, shift=3) -
#                       self.__derive_pd_content__(pd_data, date, tag, shift=4)) * self.__derive_pd_content__(
#             pd_data, date, tag, shift=-2)
#         last_paid = (self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=3)
#                      - self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=4)
#                      ) * self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=-2)
#         if not is_valid_float(self.__derive_pd_content__(pd_data, date, tag, shift=-2)):
#             return 0.0
#         if not is_valid_float(last_paid) and not is_valid_float(today_paid):
#             return 0.0
#         if not is_valid_float(last_paid):
#             last_paid = 0.0
#         if not is_valid_float(today_paid):
#             return 0.0
#         return (today_paid - last_paid) + self.hist_product_meigu_interest_paid(product, date)
#
#     def hist_product_meigu_interest_paid(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '美股市值（cny)'
#         last_paid = self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=4)
#         today_paid = self.__derive_pd_content__(pd_data, date, tag, shift=4)
#         if not is_valid_float(last_paid):
#             last_paid = 0.0
#         if not is_valid_float(today_paid):
#             today_paid = 0.0
#         if abs(last_paid - today_paid) < 0.01:
#             return 0.0
#         else:
#             return (today_paid - last_paid) * self.__derive_pd_content__(pd_data, date, tag, shift=-2)
#
#     def hist_product_meigu_deposit(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '美股保证金（cny)'
#         amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
#         if is_valid_float(amount):
#             return amount
#         else:
#             return 0.0
#
#     def hist_product_meigu_total_value(self, product: str, date: datetime.date):
#         return self.hist_product_meigu_market_value(product, date) + self.hist_product_meigu_deposit(
#             product, date) - self.hist_product_meigu_interest_payable(product, date)
#
#     def hist_product_meigu_market_value(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '美股市值（cny)'
#         amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
#         if is_valid_float(amount):
#             return amount
#         else:
#             return 0.0
#
#     def hist_product_meigu_interest_payable(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '美股市值（cny)'
#         amount = self.__derive_pd_content__(pd_data, date, tag, shift=2)
#         if is_valid_float(amount):
#             return amount
#         else:
#             return 0.0
#
#     def hist_product_ganggu_daily_interest_payable(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '港股市值（cny)'
#         today_paid = (self.__derive_pd_content__(pd_data, date, tag, shift=3) -
#                       self.__derive_pd_content__(pd_data, date, tag, shift=4)) * self.__derive_pd_content__(
#             pd_data, date, tag, shift=-2)
#         last_paid = (self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=3)
#                      - self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=4)
#                      ) * self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=-2)
#         if not is_valid_float(self.__derive_pd_content__(pd_data, date, tag, shift=-2)):
#             return 0.0
#         if not is_valid_float(last_paid) and not is_valid_float(today_paid):
#             return 0.0
#         if not is_valid_float(last_paid):
#             last_paid = 0.0
#         if not is_valid_float(today_paid):
#             return 0.0
#         return (today_paid - last_paid) + self.hist_product_ganggu_interest_paid(product, date)
#
#     def hist_product_ganggu_interest_payable(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '港股市值（cny)'
#         amount = self.__derive_pd_content__(pd_data, date, tag, shift=2)
#         if is_valid_float(amount):
#             return amount
#         else:
#             return 0.0
#
#     def hist_product_ganggu_interest_paid(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '港股市值（cny)'
#         last_paid = self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=4)
#         today_paid = self.__derive_pd_content__(pd_data, date, tag, shift=4)
#         if not is_valid_float(last_paid):
#             last_paid = 0.0
#         if not is_valid_float(today_paid):
#             today_paid = 0.0
#         if abs(last_paid - today_paid) < 0.01:
#             return 0.0
#         else:
#             return (today_paid - last_paid) * self.__derive_pd_content__(pd_data, date, tag, shift=-2)
#
#     def hist_product_ganggu_total_value(self, product: str, date: datetime.date):
#         return self.hist_product_ganggu_market_value(product, date) + self.hist_product_ganggu_deposit(
#             product, date) - self.hist_product_ganggu_interest_payable(product, date)
#
#     def hist_product_ganggu_deposit(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '港股保证金（cny)'
#         amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
#         if is_valid_float(amount):
#             return amount
#         else:
#             return 0.0
#
#     def hist_product_ganggu_market_value(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '港股市值（cny)'
#         amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
#         if is_valid_float(amount):
#             return amount
#         else:
#             return 0.0
#
#     def hist_product_bank_cash(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = '银行存款'
#         return self.__derive_pd_content__(pd_data, date, tag, shift=0)
#
#     def hist_product_ping_an_cash(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         if product in ('全球1号', '收益1号'):
#             tag = '募集户存款（平安）'
#         else:
#             tag = '平安募集户'
#         amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
#         if not is_valid_float(amount):
#             amount = 0
#         return amount
#
#     def hist_product_guo_jun_cash(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         if product == '稳健17号':
#             tag = '证券存出保证金（国君）'
#         else:
#             tag = '证券存出保证金'
#         return self.__derive_pd_content__(pd_data, date, tag, shift=0)
#
#     def hist_product_stock_market_value(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         if product == '稳健15号':
#             tag = '证券市值'
#         else:
#             tag = '股票市值'
#         return self.__derive_pd_content__(pd_data, date, tag, shift=0)
#
#     def hist_product_stock_new_value(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         try:
#             tag = self.__search_pd_column__(pd_data, '新股')
#             return self.__derive_pd_content__(pd_data, date, tag, shift=0)
#         except KeyError:
#             return 0.0
#
#     def hist_product_bond_baowu_interest_receivable(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         try:
#             tag = '宝武eb收盘'
#             return self.__derive_pd_content__(pd_data, date, tag, shift=1) - self.__derive_pd_content__(
#                 pd_data, date - datetime.timedelta(days=1), tag, shift=1)
#         except ValueError:
#             return 0.0
#
#     def hist_vat(self, product: str, date: datetime.date):
#         pd_data = self.__load_product__(product=product, date=date)
#         tag = self.__search_pd_column__(pd_data, '预提增值税')
#         vat = self.__derive_pd_content__(pd_data, date, tag, shift=0)
#         if not is_valid_float(vat):
#             vat = 0.0
#         return vat
#
#     def load_product_net_value(self):
#         from sheets.Information import ProductNetValue
#         for file_name, product in self.file_product_map.items():
#
#             net_value_list = DataList(ProductNetValue)
#
#             pd_data = pd.read_excel(self.__sub_path__(file_name), sheet_name='资产负债表', )
#
#             if product in ('稳利2号', '稳健3号'):
#                 share_tag, net_value_per_unit_tag = '基金份额', '今日单位净值'
#             else:
#                 share_tag, net_value_per_unit_tag = '基金现份额', '今日单位净值'
#
#             last_net_value = None
#             for index in pd_data.index:
#                 if not is_valid_float(float_check(pd_data.loc[index, '资产类合计'])):
#                     continue
#
#                 try:
#                     new_net_value = ProductNetValue(
#                         product=product, date=pd_data.loc[index, '日期'], net_value=pd_data.loc[index, '资产类合计'],
#                         fund_shares=round(pd_data.loc[index, share_tag], 2),
#                         # net_value_per_unit=pd_data.loc[index, '今日单位净值（保留4位小数）'],
#                         net_value_per_unit=round(pd_data.loc[index, net_value_per_unit_tag], 4),
#                     )
#                 except KeyError as e:
#                     print(file_name)
#                     print(pd_data.columns)
#                     raise KeyError(e)
#                 if last_net_value is not None:
#                     if new_net_value.date == last_net_value.date:
#                         raise NotImplementedError('new_net_value: {}, last_net_value: {}'.format(
#                             new_net_value, last_net_value))
#                     else:
#                         assert new_net_value.date > last_net_value.date, 'new_net_value: {}, last_net_value: {}'.format(
#                             new_net_value, last_net_value)
#                 if is_valid_float(new_net_value.net_value_per_unit):
#                     net_value_list.append(new_net_value)
#
#                 last_net_value = new_net_value
#
#             # 导入数据库
#             self.env.data_base.execute(
#                 DataBaseName.management,
#                 "DELETE FROM `产品净值表` WHERE 产品 = '{}'".format(product),
#             )
#             for obj in net_value_list:
#                 self.env.data_base.execute(
#                     DataBaseName.management, getattr(obj, 'form_insert_sql').__call__('产品净值表'))
#
#     # def load_management_fee_payable(self):
#     #     from sheets.Information import ManagementFeePayable
#     #     for file_name, product in self.file_product_map.items():
#     #         if not self.env.data_base.read_pd_query(
#     #                 DataBaseName.transfer_agent_new,
#     #                 """select `最新管理费率`('2018-01-02', '{}') as 最新管理费率;""".format(product)
#     #         ).loc[0, '最新管理费率'] > 0:
#     #             continue
#     #
#     #         management_fee_payable = DataList(ManagementFeePayable)
#     #
#     #         pd_data = pd.read_excel(self.__sub_path__(file_name), sheet_name='资产负债表', )
#     #
#     #         if product in ('全球1号',):
#     #             accumulated_fee_tag, fee_payable_tag = '累计固定管理费', '应付固定管理费'
#     #         elif product in ('收益1号',):
#     #             accumulated_fee_tag, fee_payable_tag = '累计固定管理费', '固定管理费'
#     #         elif product in ('稳健18号',):
#     #             accumulated_fee_tag, fee_payable_tag = '累计管理费用', '应付管理费'
#     #         else:
#     #             accumulated_fee_tag, fee_payable_tag = '累计应付管理费', '应付管理费'
#     #
#     #         last_fee = None
#     #         for index in pd_data.index:
#     #             if not is_valid_float(float_check(pd_data.loc[index, '资产类合计'])):
#     #                 continue
#     #
#     #             try:
#     #                 new_fee = ManagementFeePayable(
#     #                     product=product, date=pd_data.loc[index, '日期'],
#     #                     daily_fee=None,
#     #                     accumulated_fee=float_check(pd_data.loc[index, accumulated_fee_tag]),
#     #                     fee_payable=float_check(pd_data.loc[index, fee_payable_tag]),
#     #                 )
#     #             except KeyError as e:
#     #                 print(file_name)
#     #                 print(pd_data.columns)
#     #                 raise e
#     #             if new_fee.accumulated_fee > 0:
#     #                 if last_fee is None:
#     #                     new_fee.daily_fee = new_fee.accumulated_fee
#     #                 else:
#     #                     if new_fee.date == last_fee.date:
#     #                         raise NotImplementedError('new_fee: {}, last_fee: {}'.format(new_fee, last_fee))
#     #                     else:
#     #                         assert new_fee.date > last_fee.date, 'new_fee: {}, last_fee: {}'.format(new_fee, last_fee)
#     #                     new_fee.daily_fee = new_fee.accumulated_fee - last_fee.accumulated_fee
#     #
#     #             if is_valid_float(new_fee.daily_fee):
#     #                 if new_fee.daily_fee >= 0.01:
#     #                     management_fee_payable.append(new_fee)
#     #             else:
#     #                 if is_valid_float(new_fee.accumulated_fee):
#     #                     if abs(new_fee.accumulated_fee - new_fee.fee_payable) < 0.01:
#     #                         new_fee.daily_fee = 0.0
#     #                         # management_fee_payable.append(new_fee)
#     #                     else:
#     #                         pass
#     #                 else:
#     #                     pass
#     #
#     #             last_fee = new_fee
#     #
#     #         self.env.data_base.execute(
#     #             DataBaseName.management,
#     #             "DELETE FROM `产品管理费计提表` WHERE 产品 = '{}'".format(product),
#     #         )
#     #         for obj in management_fee_payable:
#     #             self.env.data_base.execute(
#     #                 DataBaseName.management, getattr(obj, 'form_insert_sql').__call__('产品管理费计提表'))
#
#     def load_fund_net_value(self):
#         from sheets.Information import FundNetValue
#
#         net_value_list = DataList(FundNetValue)
#
#         for file_name, product in self.file_product_map.items():
#
#             # if product not in ('稳健6号', '稳健15号'):
#             #     continue
#
#             pd_data = pd.read_excel(self.__sub_path__(file_name), sheet_name='资产负债表', )
#             column_list = list(pd_data.columns)
#
#             if product == '稳健6号':
#                 fund_tag_list = [
#                     ('同晖1号', column_list[column_list.index('合晟同晖1号') + 3])
#                 ]
#             elif product == '稳健15号':
#                 fund_tag_list = [
#                     ('浦江之星289号', column_list[column_list.index('中海-浦江之星289号') + 3])
#                 ]
#             else:
#                 continue
#
#             for index in pd_data.index:
#
#                 if not is_valid_float(float_check(pd_data.loc[index, '资产类合计'])):
#                     continue
#
#                 for tag in fund_tag_list:
#
#                     try:
#                         new_net_value = FundNetValue(
#                             date=pd_data.loc[index, '日期'], fund_name=tag[0],
#                             net_value_per_unit=pd_data.loc[index, tag[1]],
#                         )
#                     except KeyError as e:
#                         print(file_name)
#                         print(pd_data.columns)
#                         raise KeyError(e)
#                     if is_valid_float(new_net_value.net_value_per_unit):
#                         net_value_list.append(new_net_value)
#
#         # 导入数据库
#         self.env.data_base.execute(
#             DataBaseName.management,
#             "DELETE FROM `录入基金净值表`;",
#         )
#         for obj in net_value_list:
#             self.env.data_base.execute(
#                 DataBaseName.management, getattr(obj, 'form_insert_sql').__call__('录入基金净值表'))
#
#     def load_management_fee_receivable(self):
#         from sheets.Information import ManagementFeeReceivable
#         for file_name, product in self.file_product_map.items():
#
#             management_fee_receivable = DataList(ManagementFeeReceivable)
#
#             pd_data = pd.read_excel(self.__sub_path__(file_name), sheet_name='资产负债表', )
#
#             if product == '久铭2号':
#                 tag_list = [
#                     ('稳健6号', '累计应收管理费返还（稳健6号）', '管理费返还（稳健6号）'),
#                     ('稳利2号', '累计应收稳利2号管理费', '应收稳利2号管理费'),
#                     ('稳健3号', '累计应收稳健3号管理费', '应收稳健3号管理费'),
#                     ('稳健5号', '累计应收稳健5号管理费', '应收稳健5号管理费'),
#                 ]
#             elif product == '久铭3号':
#                 tag_list = [
#                     ('久铭2号', '累计应收久铭2号管理费返还', '应收久铭2号管理费返还',),
#                     ('中证500指数', '累计应收管理费返还（中证500）', '应收中证500指数管理费'),
#                 ]
#             elif product == '双盈1号':
#                 tag_list = [
#                     ('稳健6号', '累计应收管理费返还（稳健6号）', '应收管理费返还（稳健6号）'),
#                     ('沪深300指数', '累计应收管理费返还（沪深300）', '应收沪深300管理费'),
#                 ]
#             elif product == '稳健3号':
#                 tag_list = [
#                     ('稳健18号', '累计应收管理费返还（稳健18号）', '应收管理费返还稳健18号'),
#                     ('久铭2号', '累计应收管理费返还（久铭2号）', '应收管理费返还久铭2号'),
#                 ]
#             elif product == '稳健6号':
#                 tag_list = [
#                     ('稳健18号', '累计应收管理费返还（稳健18号）', '应收管理费返还稳健18号'),
#                 ]
#             elif product == '稳健7号':
#                 tag_list = [
#                     ('久铭1号', '累计应收管理费返还（久铭1号）', '应收久铭1号管理费',),
#                 ]
#             elif product == '稳健18号':
#                 tag_list = [
#                     ('久铭2号', '累计应收久铭2号管理费', '应收久铭2号管理费'),
#                     ('久铭6号', '累计应收管理费返还（久铭6号）', '应收久铭6号管理费'),
#                     ('久铭7号', '累计应收管理费返还（久铭7号）', '应收久铭7号管理费'),
#                     ('久铭8号', '累计应收管理费返还（久铭8号）', '应收久铭8号管理费'),
#                 ]
#             elif product == '稳健19号':
#                 tag_list = [
#                     ('稳健18号', '累计应收管理费返还（稳健18号）', '应收管理费返还稳健18号'),
#                     ('沪深300指数', '累计应收管理费返还（沪深300指数）', '应收沪深300管理费'),
#                 ]
#             elif product in (
#                     '全球1号', '收益1号', '稳利2号', '稳健5号', '稳健2号', '稳健8号', '稳健9号', '稳健10号', '稳健11号',
#                     '稳健12号', '稳健15号', '稳健16号', '稳健17号', '稳健21号', '稳健22号', '稳健31号', '稳健32号',
#                     '稳健33号',
#             ):
#                 tag_list = list()
#             else:
#                 column_list = list()
#                 for tag in pd_data.columns:
#                     if '返还' in tag:
#                         column_list.append(tag)
#                 print(product, column_list)
#                 column_list = list()
#                 for tag in pd_data.columns:
#                     if '费' in tag or '管理' in tag:
#                         column_list.append(tag)
#                 print(product, column_list)
#                 raise NotImplementedError
#
#             last_index = None
#             for index in pd_data.index:
#
#                 # TODO: 检查返还新特例
#                 try:
#                     for tag in tag_list:
#                         if last_index is not None:
#                             if is_valid_float(pd_data.loc[last_index, tag[1]]):
#                                 fee_return = pd_data.loc[index, tag[1]] - pd_data.loc[last_index, tag[1]]
#                             elif not is_valid_float(pd_data.loc[index, tag[1]]):
#                                 fee_return = 0.0
#                             else:
#                                 fee_return = pd_data.loc[index, tag[1]]
#                         else:
#                             if not is_valid_float(pd_data.loc[index, tag[1]]):
#                                 fee_return = 0.0
#                             else:
#                                 fee_return = pd_data.loc[index, tag[1]]
#                         new_fee = ManagementFeeReceivable(
#                             investor=tag[0], date=pd_data.loc[index, '日期'], invested=product,
#                             fee_return=fee_return,
#                             accumulated_fee_return=pd_data.loc[index, tag[1]],
#                             fee_return_receivable=pd_data.loc[index, tag[2]],
#                         )
#                         if not is_valid_float(fee_return):
#                             if is_valid_float(new_fee.accumulated_fee_return):
#                                 raise NotImplementedError(str(new_fee))
#                         if new_fee.fee_return >= 0.1:
#                             management_fee_receivable.append(new_fee)
#                 except KeyError as e:
#                     print(file_name)
#                     print(pd_data.columns)
#                     raise KeyError(e)
#
#                 last_index = index
#
#             # 导入数据库
#             self.env.data_base.execute(
#                 DataBaseName.management,
#                 "DELETE FROM `产品管理费返还表` WHERE 产品 = '{}'".format(product),
#             )
#             for obj in management_fee_receivable:
#                 sql = getattr(obj, 'form_insert_sql').__call__('产品管理费返还表')
#                 self.env.data_base.execute(DataBaseName.management, sql)
#
#     def __print_patterned_column_list__(self, pd_data: pd.DataFrame, tag: str):
#         column_list = list()
#         for col in pd_data.columns:
#             if tag in col:
#                 column_list.append(col)
#         print(column_list)
#
#
# if __name__ == '__main__':
#     import os
#     from core.Environment import Environment
#
#     env = Environment()
#
#     ds = ValuationTableDataSource(os.path.join(env.root_path(), '..', '2018.12.14'))
#     ds.load_fund_net_value()
#
#     # from sheets.Information import ProductInfo
#     # from sheets.entry.Position import EntryPosition
#     # pro_list = DataList.from_pd(EntryPosition, env.data_base.read_pd_query(
#     #     DataBaseName.management,
#     #     """SELECT * FROM `会计产品持仓表`;"""
#     # ))
#     # for obj in pro_list:
#     #     assert isinstance(obj, EntryPosition)
#     #     sql = """UPDATE `录入基金交易流水` SET `产品代码` = '{}' WHERE `产品名称` = '{}';""".format(
#     #         obj.security_code, obj.security_name
#     #     )
#     #     env.data_base.execute(DataBaseName.management, sql)
#     #     print(sql)
#
#     # name_code_map = {
#     #     '启元18号': 'ST1188', '长安鑫垚': '004907.OF', '长安鑫恒': '004898.OF', '贝溢一号': 'SW3945',
#     # }
#     # for name, code in name_code_map.items():
#     #     sql = """UPDATE `2018上半年基金交易流水` SET `产品代码` = '{}' WHERE `产品名称` = '{}';""".format(
#     #         code, name
#     #     )
#     #     env.data_base.execute(DataBaseName.management, sql)
#     #     sql = """UPDATE `录入基金交易流水` SET `产品代码` = '{}' WHERE `产品名称` = '{}';""".format(
#     #         code, name
#     #     )
#     #     env.data_base.execute(DataBaseName.management, sql)
#
#     env.exit()