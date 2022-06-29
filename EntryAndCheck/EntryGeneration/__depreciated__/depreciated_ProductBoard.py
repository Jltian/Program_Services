# # -*- encoding: UTF-8 -*-
# import datetime
#
# from sqlalchemy.orm.exc import NoResultFound
# from utils.Constants import *
#
#
# class ProductCache(object):
#     def __init__(self, product: str, date: datetime.date, field: str, value: str):
#         self.product, self.date, self.field, self.value = product, date, field, value
#
#
# def define_product_cache_table(meta):
#     from sqlalchemy import MetaData, Table, Column, String, Date
#     assert isinstance(meta, MetaData)
#     return Table(
#         'ProductCache', meta,
#         Column('product', String, primary_key=True),
#         Column('date', Date, primary_key=True),
#         Column('field', String, primary_key=True),
#         Column('value', String),
#     )
#
#
# class ProductBoard(object):
#
#     def __init__(self):
#         from core.Environment import Environment
#         env = Environment.get_instance()
#
#         self.env = env
#         self.db = env.data_base
#         self.cache = env.local_cache
#         product_cache_table = define_product_cache_table(self.cache.metadata)
#         self.cache.map(ProductCache, product_cache_table)
#         self.cache.metadata.create_all(checkfirst=True)
#
#     def management_fee_rate(self, product: str, date: datetime.date):
#         """管理费率"""
#         try:
#             mfr = self.cache.session.query(ProductCache).filter_by(
#                 product=product, date=date, field='management_fee_rate',
#             ).one().value
#             mfr = float_check(mfr)
#         except NoResultFound:
#             mfr = self.env.data_base.read_pd_query(
#                     DataBaseName.transfer_agent_new,
#                     """select `最新管理费率`('{}', '{}') as 最新管理费率;""".format(date.strftime('%Y-%m-%d'), product)
#             ).loc[0, '最新管理费率']
#             self.cache.add(ProductCache(product=product, date=date, field='management_fee_rate', value=str(mfr)))
#         return mfr
#
#
# if __name__ == '__main__':
#     pass
