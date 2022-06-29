# # -*- encoding: UTF-8 -*-
# import datetime
#
# from jetend.structures import Sqlite
#
# from sqlalchemy.orm.exc import NoResultFound
# from utils.Constants import *
#
#
# class MarketCache(object):
#     def __init__(self, field: str, date: datetime.date, security_type: str, security_code: str, value: str):
#         self.field, self.date, self.security_type = field, date, security_type
#         self.security_code, self.value = security_code, value
#
#
# def define_price_cache_table(meta):
#     from sqlalchemy import MetaData, Table, Column, String, Date
#     assert isinstance(meta, MetaData)
#     return Table(
#         'MarketCache', meta,
#         Column('field', String, primary_key=True),
#         Column('date', Date, primary_key=True),
#         Column('security_type', String, primary_key=True),
#         Column('security_code', String, primary_key=True),
#         Column('value', String),
#     )
#
#
# class MarketBoard(object):
#     security_type_map = {
#         '债券投资': SECURITY_TYPE_BOND,
#         '基金投资': SECURITY_TYPE_FUND,
#         '股票投资': SECURITY_TYPE_STOCK,
#         '权证投资': SECURITY_TYPE_OPTION,
#         '应收利息': SECURITY_TYPE_BOND_INTEREST,
#     }
#     security_code_name_map = {
#         'S22497': '同晖1号', 'PuJiang289': '浦江之星289号',
#     }
#
#     def __init__(self):
#         from core.Environment import Environment
#         env = Environment.get_instance()
#
#         self.env = env
#         self.db = env.data_base
#         self.cache = Sqlite()
#         price_cache_table = define_price_cache_table(self.cache.metadata)
#         self.cache.map(MarketCache, price_cache_table)
#         self.cache.metadata.create_all(checkfirst=True)
#
#         self.product_code_name_map = env.product_info_list.map_attr('code', 'name')
#         self.security_code_set = env.security_info_list.collect_distinct_attr('full_code')
#
#     def exchange_settle_rate(self, ex_from: str, ex_to: str, date: datetime.date):
#         if (ex_from, ex_to) == ('HKD', 'CNY'):
#             tag = 'HKDCNYSET.HKS'
#         else:
#             raise NotImplementedError(str((ex_from, ex_to)))
#         try:
#             exchange_settle_rate = self.cache.session.query(MarketCache).filter_by(
#                 field='exchange_settle_rate', date=date, security_type='exchange', security_code=tag,
#             ).one().value
#             exchange_settle_rate = float_check(exchange_settle_rate)
#         except NoResultFound:
#             exchange_settle_rate = self.wsd('close', tag, date)
#             self.cache.add(MarketCache(
#                 'exchange_settle_rate', date, 'exchange', tag, str(exchange_settle_rate)))
#         return exchange_settle_rate
#
#     def exchange_rate(self, ex_from: str, ex_to: str, date: datetime.date):
#         raise NotImplementedError
#
#     def future_leverage_ratio(self, security_code: str, date: datetime.date):
#         """期货保证金杠杆比例"""
#         try:
#             leverage_ratio = self.cache.session.query(MarketCache).filter_by(
#                     field='leverage_ratio', date=date, security_code=security_code, security_type=SECURITY_TYPE_FUTURE,
#                 ).one().value
#             leverage_ratio = float_check(leverage_ratio)
#         except NoResultFound:
#             pd_data = self.db.read_pd_query(
#                 DataBaseName.management,
#                 """SELECT `买持`, `结算价`, `保证金占用` FROM `原始期货持仓记录`
#                 WHERE `日期` = '{}' and `期货合约` = '{}';""".format(date, security_code)
#             )
#             leverage_ratio = pd_data.loc[0, '保证金占用'] / (
#                     pd_data.loc[0, '买持'] * pd_data.loc[0, '结算价']
#                     * self.contract_multiplier(SECURITY_TYPE_OPTION, security_code, date)
#             )
#             self.cache.add(MarketCache(
#                 'leverage_ratio', date, SECURITY_TYPE_FUTURE, security_code, str(leverage_ratio)))
#         return leverage_ratio
#
#     def ipo_date(self, security_type: str, security_code: str, date: datetime.date):
#         """股票发行日 -> None/datetime.date"""
#         security_type = self.__clean_security_type__(security_type)
#         if security_type == SECURITY_TYPE_STOCK:
#             try:
#                 ipo_date = self.cache.session.query(MarketCache).filter_by(
#                     field='ipo_date', date=date, security_code=security_code, security_type=security_type,
#                 ).one().value
#             except NoResultFound:
#                 ipo_date = self.wsd('ipo_date', security_code, date)
#                 if ipo_date is None:
#                     ipo_date = ''
#                 elif isinstance(ipo_date, str):
#                     ipo_date = ipo_date
#                 elif isinstance(ipo_date, datetime.date):
#                     ipo_date = ipo_date.strftime('%Y%m%d')
#                 else:
#                     raise NotImplementedError(type(ipo_date))
#                 self.cache.add(MarketCache(
#                     'ipo_date', date, security_type, security_code, ipo_date
#                 ))
#             return date_check(ipo_date, date_format='%Y%m%d')
#         else:
#             raise NotImplementedError(security_type)
#
#     # def div_exdate(self, security_type: str, security_code: str, date: datetime.date):
#     #     """股利除权日 -> None/datetime.date"""
#     #     security_type = self.__clean_security_type__(security_type)
#     #     if security_type == SECURITY_TYPE_STOCK:
#     #         try:
#     #             div_exdate = self.cache.session.query(MarketCache).filter_by(
#     #                 field='ipo_date', date=date, security_code=security_code, security_type=security_type,
#     #             ).one().value
#     #         except NoResultFound:
#     #             div_exdate = self.__wsd__('div_exdate', security_code, date)
#     #             if div_exdate is None:
#     #                 div_exdate = ''
#     #             elif isinstance(div_exdate, str):
#     #                 div_exdate = div_exdate
#     #             elif isinstance(div_exdate, datetime.date):
#     #                 div_exdate = div_exdate.strftime('%Y%m%d')
#     #             else:
#     #                 raise NotImplementedError(type(div_exdate))
#     #             self.cache.add(MarketCache(
#     #                 'ipo_date', date, security_type, security_code, div_exdate
#     #             ))
#     #         return date_check(div_exdate, date_format='%Y%m%d')
#     #     else:
#     #         raise RuntimeError('security type {} has no div_date.'.format(security_type))
#
#     # def close_price(self, security_type: str, security_code: str, date: datetime.date):
#     #     security_type = self.__clean_security_type__(security_type)
#     #     try:
#     #         close_str = self.cache.session.query(MarketCache).filter_by(
#     #             field='close', date=date, security_code=security_code, security_type=security_type,
#     #         ).one().value
#     #         close = float_check(close_str)
#     #     except NoResultFound:
#     #         if security_type == SECURITY_TYPE_STOCK:
#     #             close = self.wsd('close', security_code, date, '')
#     #         elif security_type == SECURITY_TYPE_OPTION:
#     #             close = self.wsd('settle', security_code, date)
#     #         elif security_type == SECURITY_TYPE_BOND:
#     #             close = self.wsd('cleanprice', security_code, date)
#     #         elif security_type == SECURITY_TYPE_FUND:
#     #             if security_code in self.product_code_name_map:
#     #                 security_name = self.product_code_name_map[security_code]
#     #                 close = self.env.info_board.find_product_net_value_by_name(security_name)
#     #                 # try:
#     #                 #     close = self.db.read_pd_query(
#     #                 #         DataBaseName.transfer_agent_new,
#     #                 #         """SELECT `{}` as 单位净值 FROM `净值表` WHERE `日期` = '{}';""".format(
#     #                 #             self.product_code_name_map[security_code], date)).loc[0, '单位净值']
#     #                 # except KeyError as k_r:
#     #                 #     close = self.db.read_pd_query(
#     #                 #         DataBaseName.transfer_agent_new,
#     #                 #         """SELECT `{}` as 单位净值 FROM `净值表` WHERE `日期` < '{}' ORDER BY `日期` DESC;""".format(
#     #                 #             self.product_code_name_map[security_code], date
#     #                 #         )).loc[0, '单位净值']
#     #                 # close = round(close, 4)
#     #             elif security_code in self.security_code_set :
#     #                 close = self.wsd('nav', security_code, date, option='')
#     #             elif security_code in self.security_code_name_map:
#     #                 from pymysql.err import ProgrammingError
#     #                 try:
#     #                     close = self.db.read_pd_query(
#     #                         DataBaseName.management,
#     #                         """SELECT `单位净值` FROM `录入基金净值表` WHERE `日期` = '{}' and `基金名称` = '{}';""".format(
#     #                             date, self.security_code_name_map[security_code])).loc[0, '单位净值']
#     #                 except KeyError or ProgrammingError:
#     #                     raise RuntimeError('基金 {} {} 未录入 {} 净值'.format(
#     #                         security_code, self.security_code_name_map[security_code], date))
#     #             else:
#     #                 raise NotImplementedError(security_code)
#     #         elif security_type == SECURITY_TYPE_BOND_INTEREST:
#     #             close = self.wsd('self.bond_interest_on_date', security_code, date, option='Currency=CNY')
#     #         else:
#     #             raise NotImplementedError(security_type)
#     #         self.cache.add(MarketCache('close', date, security_type, security_code, str_check(close)))
#     #     assert is_valid_float(close), '{} {} {}'.format(security_type, security_code, date)
#     #     return close
#
#     def contract_multiplier(self, security_type: str, security_code: str, date: datetime.date):
#         security_type = self.__clean_security_type__(security_type)
#         if security_type in (SECURITY_TYPE_STOCK, SECURITY_TYPE_BOND, SECURITY_TYPE_FUND):
#             c_multiplier = 1.0
#         elif security_type in (SECURITY_TYPE_OPTION, ):
#             try:
#                 c_multiplier_str = self.cache.session.query(MarketCache).filter_by(
#                     field='contract_multiplier', date=date, security_code=security_code, security_type=security_type
#                 ).one().value
#                 c_multiplier = float_check(c_multiplier_str)
#             except NoResultFound:
#                 c_multiplier = self.wsd('contractmultiplier', security_code, date)
#                 self.cache.add(MarketCache(
#                     'contract_multiplier', date, security_type, security_code, str(c_multiplier)))
#         else:
#             raise NotImplementedError(security_type)
#         return c_multiplier
#
#     def accrued_interest(self, security_code: str, date: datetime.date,):
#         try:
#             accrued_interest = self.cache.session.query(MarketCache).filter_by(
#                 field='accruedinterest', date=date, security_code=security_code, security_type=SECURITY_TYPE_BOND
#             ).one().value
#             accrued_interest = float_check(accrued_interest)
#         except NoResultFound:
#             accrued_interest = self.wsd('self.accruedinterest', security_code, date)
#             self.cache.add(MarketCache(
#                 'accruedinterest', date, SECURITY_TYPE_BOND, security_code, str(accrued_interest)
#             ))
#         return accrued_interest
#
#     def wsd(self, tag: str, security_code: str, date: datetime.date, option: str = ''):
#         if tag.lower() == 'self.bond_interest_on_date':
#             this_dirty_price = self.wsd('dirtyprice', security_code, date, option)
#             this_clean_price = self.wsd('cleanprice', security_code, date, option)
#             last_dirty_price = self.wsd('dirtyprice', security_code, date - datetime.timedelta(days=1), option)
#             last_clean_price = self.wsd('cleanprice', security_code, date - datetime.timedelta(days=1), option)
#             return (this_dirty_price - this_clean_price) - (last_dirty_price - last_clean_price)
#         elif tag.lower() == 'self.accruedinterest':
#             this_dirty_price = self.wsd('dirtyprice', security_code, date, option)
#             this_clean_price = self.wsd('cleanprice', security_code, date, option)
#             return this_dirty_price - this_clean_price
#         else:
#             if date + datetime.timedelta(days=5) <= datetime.date.today():
#                 date_end = date + datetime.timedelta(days=10)
#             else:
#                 date_end = datetime.date.today()
#             result, times = self.__wsd__(
#                 tag, security_code, date - datetime.timedelta(days=15), date_end, option
#             )
#             date_str = date.strftime('%Y%m%d')
#             try:
#                 # 存在当日数据
#                 data_index = times.index(date_str)
#                 return result.Data[0][data_index]
#             except ValueError:
#                 # 不存在当日数据 使用前一个有效日数据
#                 for i in range(len(times) - 1, -1, -1):
#                     if times[i] < date_str:
#                         return result.Data[0][i]
#                 raise ValueError(times)
#
#     def __wsd__(self, tag: str, security_code: str, start_date: datetime.date,
#                 end_date: datetime.date, option: str = ''):
#         result = self.env.wind_engine.wsd(
#             security_code, tag, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'), option
#         )
#
#         times = list()
#         for item in result.Times:
#             if isinstance(item, str):
#                 times.append(item)
#             elif isinstance(item, datetime.date):
#                 times.append(item.strftime('%Y%m%d'))
#             else:
#                 raise NotImplementedError
#
#         if result.ErrorCode != 0:
#             raise RuntimeError('{} {}'.format(result.ErrorCode, result.Data))
#
#         return result, times
#
#     def __clean_security_type__(self, security_type: str):
#         if security_type in SECURITY_TYPE_RANGE:
#             return security_type
#         else:
#             return self.security_type_map[security_type]
#
#
# if __name__ == '__main__':
#     pass
