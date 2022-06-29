# -*- encoding: UTF-8 -*-
import datetime

from sqlalchemy import Table
from sqlalchemy.orm import mapper
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm.exc import NoResultFound
from jetend.DataCheck import *

from extended.wrapper.Sqlite import Sqlite
from extended.wrapper.MySQL import MySQL


class jmMarketCache(object):
    def __init__(self, field: str, date: datetime.date, security_code: str, value: str):
        self.field, self.date = field, date
        self.security_code, self.value = security_code, value

    @staticmethod
    def define_price_cache_table(meta):
        from sqlalchemy import MetaData, Table, Column, String, Date
        assert isinstance(meta, MetaData)
        return Table(
            'jmMarketCache', meta,
            Column('field', String, primary_key=True),
            Column('date', Date, primary_key=True),
            Column('security_code', String, primary_key=True),
            Column('value', String),
        )


class jmMarketBoard(object):

    def __init__(self, wind_engine, db_cache, **kwargs):
        self.cache, self.cache_db_name = db_cache, None
        if isinstance(self.cache, Sqlite):
            price_cache_table = jmMarketCache.define_price_cache_table(self.cache.metadata)
            self.cache.map(jmMarketCache, price_cache_table)
        elif isinstance(self.cache, MySQL):
            self.cache_db_name = kwargs.get('db_name', 'test')
            price_cache_table = jmMarketCache.define_price_cache_table(self.cache.metadata('test'))
            self.cache.map(jmMarketCache, price_cache_table)
        else:
            raise NotImplementedError(self.cache)
        self.wind_engine = wind_engine

    @property
    def session(self):
        from sqlalchemy.orm import Session
        if isinstance(self.cache, Sqlite):
            s = self.cache.session
        elif isinstance(self.cache, MySQL):
            s = self.cache.session(self.cache_db_name)
        else:
            raise NotImplementedError(self.cache)
        assert isinstance(s, Session), '{} {}'.format(type(s), s)
        return s

    def add(self, obj):
        if isinstance(self.cache, Sqlite):
            self.cache.add(obj)
        elif isinstance(self.cache, MySQL):
            self.cache.add(self.cache_db_name, obj)
        else:
            raise NotImplementedError(self.cache)

    def exchange_settle_rate(self, ex_from: str, ex_to: str, exchange: str, date: datetime.date):
        """结算汇率 -> float"""
        if exchange.upper() == 'HKS':
            if (ex_from, ex_to) == ('HKD', 'CNY'):
                tag = 'HKDCNYSET.HKS'
            else:
                raise NotImplementedError(str((ex_from, ex_to)))
        elif exchange.upper() == 'HKZ':
            if (ex_from, ex_to) == ('HKD', 'CNY'):
                tag = 'HKDCNYSETS.HKZ'
            else:
                raise NotImplementedError(str((ex_from, ex_to)))
        else:
            raise NotImplementedError(exchange)
        try:
            exchange_settle_rate = self.session.query(jmMarketCache).filter_by(
                field='exchange_settle_rate', date=date, security_code=tag,
            ).one().value
            exchange_settle_rate = float_check(exchange_settle_rate)
        except NoResultFound:
            exchange_settle_rate = self.wsd('close', tag, date)
            self.add(jmMarketCache('exchange_settle_rate', date, tag, str(exchange_settle_rate)))
        return exchange_settle_rate

    # def exchange_settle_rate(self, ex_from: str, ex_to: str, date: datetime.date):
    #     """结算汇率 -> float"""
    #     if (ex_from, ex_to) == ('HKD', 'CNY'):
    #         tag = 'HKDCNYSET.HKS'
    #     else:
    #         raise NotImplementedError(str((ex_from, ex_to)))
    #     try:
    #         exchange_settle_rate = self.cache.session.query(jmMarketCache).filter_by(
    #             field='exchange_settle_rate', date=date, security_code=tag,
    #         ).one().value
    #         exchange_settle_rate = float_check(exchange_settle_rate)
    #     except NoResultFound:
    #         exchange_settle_rate = self.wsd('close', tag, date)
    #         self.cache.add(jmMarketCache('exchange_settle_rate', date, tag, str(exchange_settle_rate)))
    #     return exchange_settle_rate

    def exchange_rate(self, ex_from: str, ex_to: str, date: datetime.date):
        raise NotImplementedError

    def ipo_date(self, security_code: str, date: datetime.date):
        """股票发行日 -> datetime.date"""
        try:
            ipo_date = self.session.query(jmMarketCache).filter_by(
                field='ipo_date', date=date, security_code=security_code,
            ).one().value
        except NoResultFound:
            ipo_date = self.wsd('ipo_date', security_code, date)
            if ipo_date is None:
                ipo_date = ''
            elif isinstance(ipo_date, str):
                ipo_date = ipo_date
            elif isinstance(ipo_date, datetime.date):
                ipo_date = ipo_date.strftime('%Y%m%d')
            else:
                raise NotImplementedError(type(ipo_date))
            self.add(jmMarketCache('ipo_date', date, security_code, ipo_date, ))
        return date_check(ipo_date, date_format='%Y%m%d')

    def float_field(self, field: str, security_code: str, date: datetime.date, option: str = ''):
        try:
            float_str = self.session.query(jmMarketCache).filter_by(
                field=field, date=date, security_code=security_code,
            ).one().value
            float_digit = float_check(float_str)
        except NoResultFound:
            float_digit = self.wsd(field, security_code, date, option)
            self.add(jmMarketCache(field, date, security_code, str_check(float_digit)))
        assert is_valid_float(float_digit), '{} {} {}'.format(security_code, date, float_digit)
        return float_digit

    # def accrued_interest(self, security_code: str, date: datetime.date,):
    #     try:
    #         accrued_interest = self.cache.session.query(jmMarketCache).filter_by(
    #             field='accruedinterest', date=date, security_code=security_code, security_type=SECURITY_TYPE_BOND
    #         ).one().value
    #         accrued_interest = float_check(accrued_interest)
    #     except NoResultFound:
    #         accrued_interest = self.wsd('self.accruedinterest', security_code, date)
    #         self.cache.add(jmMarketCache(
    #             'accruedinterest', date, SECURITY_TYPE_BOND, security_code, str(accrued_interest)
    #         ))
    #     return accrued_interest

    def wsd(self, tag: str, security_code: str, date: datetime.date, option: str = ''):
        if tag.lower() == 'self.bond_interest_on_date':
            this_dirty_price = self.wsd('dirtyprice', security_code, date, option)
            this_clean_price = self.wsd('cleanprice', security_code, date, option)
            last_dirty_price = self.wsd('dirtyprice', security_code, date - datetime.timedelta(days=1), option)
            last_clean_price = self.wsd('cleanprice', security_code, date - datetime.timedelta(days=1), option)
            return (this_dirty_price - this_clean_price) - (last_dirty_price - last_clean_price)
        elif tag.lower() == 'self.accruedinterest':
            this_dirty_price = self.wsd('dirtyprice', security_code, date, option)
            this_clean_price = self.wsd('cleanprice', security_code, date, option)
            return this_dirty_price - this_clean_price
        else:
            if date + datetime.timedelta(days=5) <= datetime.date.today():
                date_end = date + datetime.timedelta(days=10)
            else:
                date_end = datetime.date.today()
            result, times = self.__wsd__(
                tag, security_code, date - datetime.timedelta(days=15), date_end, option
            )
            date_str = date.strftime('%Y%m%d')
            # print(security_code, date, tag, times, result.Data[0])
            try:
                # 存在当日数据
                data_index = times.index(date_str)
                return result.Data[0][data_index]
            except ValueError:
                # 不存在当日数据 使用前一个有效日数据
                for i in range(len(times) - 1, -1, -1):
                    if times[i] < date_str:
                        return result.Data[0][i]
                raise ValueError(times)

    def __wsd__(self, tag: str, security_code: str, start_date: datetime.date,
                end_date: datetime.date, option: str = ''):
        if not self.wind_engine.isconnected():
            self.wind_engine.start()
        result = self.wind_engine.wsd(
            security_code, tag, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'), option
        )

        times = list()
        for item in result.Times:
            if isinstance(item, str):
                times.append(item)
            elif isinstance(item, datetime.date):
                times.append(item.strftime('%Y%m%d'))
            else:
                raise NotImplementedError

        if result.ErrorCode != 0:
            raise RuntimeError('Wind Error: \nCommand: {} {} {} {} {}\nResponse: {} {}'.format(
                tag, security_code, start_date, end_date, option, result.ErrorCode, result.Data)
            )

        return result, times


if __name__ == '__main__':
    pass
