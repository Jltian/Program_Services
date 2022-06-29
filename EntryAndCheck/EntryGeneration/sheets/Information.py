# -*- encoding: UTF-8 -*-
import datetime

from structures import DataObject
from sheets.Elements import Contract
from utils.Constants import *


class DividendInfo(Contract, DataObject):
    """股利信息表"""
    inner2outer_map = {
        'security_code': '股票代码', 'security_name': '股票名称', 'dividend_mode': '派息方式',
        'cash_dividend': '每股份股利_原始币种', 'dividend_unit': '股份', 'currency': '币种', 'stock_dividend': '每股红股',
        'capital_stock': '每股转增', 'benchmark_date': '股本基准日期', 'announcement_date': '股东大会公告日',
        'registration_date': '股权登记日', 'ex_date': '除权日', 'dividend_date': '派息日', 'listing_date': '红股上市日',
    }

    def __init__(self, security_code: str = '', security_name: str = '', dividend_mode: str = '',
                 cash_dividend: float = None, currency: str = '', dividend_unit: float = None,
                 stock_dividend: float = None, capital_stock: float = None,
                 benchmark_date: datetime.date = None, announcement_date: datetime.date = None,
                 registration_date: datetime.date = None, ex_date: datetime.date = None,
                 dividend_date: datetime.date = None, listing_date: datetime.date = None, ):
        Contract.__init__(self, security_code=security_code.upper(), security_name=security_name.upper())
        DataObject.__init__(self)
        self.dividend_mode = str_check(dividend_mode)
        self.cash_dividend = float_check(cash_dividend)
        self.dividend_unit = float_check(dividend_unit)
        self.currency = str_check(currency)
        self.stock_dividend = float_check(stock_dividend)
        self.capital_stock = float_check(capital_stock)
        self.benchmark_date = date_check(benchmark_date)
        self.announcement_date = date_check(announcement_date)
        self.registration_date = date_check(registration_date)
        self.ex_date = date_check(ex_date)
        self.dividend_date = date_check(dividend_date)
        self.listing_date = date_check(listing_date)


class ManagementFeePayable(DataObject):
    """产品管理费计提表"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'daily_fee': '管理费', 'accumulated_fee': '累计管理费',
        'fee_return': '返还管理费',
    }

    def __init__(self, product: str = '', date: datetime.date = None, daily_fee: float = None,
                 accumulated_fee: float = None, fee_return: float = None):
        DataObject.__init__(self)
        self.product, self.date = str_check(product), date_check(date)
        self.daily_fee = float_check(daily_fee)
        self.accumulated_fee = float_check(accumulated_fee)
        self.fee_return = float_check(fee_return)


class ManagementFeeReceivable(DataObject):
    inner2outer_map = {
        'investor': '投资者', 'date': '日期', 'fund': '基金产品', 'fee_return': '返还管理费',
    }

    def __init__(self, investor: str = '', date: datetime.date = None, fund: str = '',
                 fee_return: float = None):
        DataObject.__init__(self)
        self.fund, self.date = str_check(fund), date_check(date)
        self.investor = str_check(investor)
        self.fee_return = float_check(fee_return)


class ProductNetValue(DataObject):
    """产品净值表"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'net_value': '总净值', 'fund_shares': '总份额',
        'net_value_per_unit': '单位净值',
    }

    def __init__(self, product: str = '', date: datetime.date = None,
                 net_value: float = None, fund_shares: float = None,
                 net_value_per_unit: float = None):
        DataObject.__init__(self)
        self.product = str_check(product)
        self.date = date_check(date)
        self.net_value = float_check(net_value)
        self.fund_shares = float_check(fund_shares)
        self.net_value_per_unit = float_check(net_value_per_unit)


class FundNetValue(DataObject):
    """基金净值表"""
    inner2outer_map = {
        'fund_name': '基金名称', 'date': '日期', 'net_value_per_unit': '单位净值',
    }

    def __init__(self, date: datetime.date = None, fund_name: str = '',
                 net_value_per_unit: float = None):
        DataObject.__init__(self)
        self.fund_name = str_check(fund_name)
        self.date = date_check(date)
        self.net_value_per_unit = float_check(net_value_per_unit)


class SecurityInfo(DataObject):
    """证券信息"""
    inner2outer_map = {
        'code': '合约代码', 's_type': '类型', 'full_code': '合约识别代码', 'name': '合约简称',
        'name_eng': '合约英文', 'full_code_eng': '合约英文代码',
        'exchange': '交易所代码', 'change_time': '修改日期', 'underlying_code': '标的代码',
    }

    def __init__(self, code: str='', s_type: str='', full_code: str='', full_code_eng: str='',
                 name: str='', name_eng: str='', underlying_code: str='',
                 exchange: str='', change_time: datetime.datetime=None, **kwargs):
        super(SecurityInfo, self).__init__()
        self.code = str_check(code)
        self.s_type = str_check(s_type)
        self.full_code = str_check(full_code)
        self.full_code_eng = str_check(full_code_eng)
        self.name = str_check(name)
        self.name_eng = str_check(name_eng)
        self.underlying_code = str_check(underlying_code)
        self.exchange = str_check(exchange)
        # self.change_time = datetime_check(change_time)
        self.change_time = change_time


class InterestRate(DataObject):
    """利率信息表"""
    inner2outer_map = {
        'account': '科目', 'account_code': '科目编号','institution': '机构',
        'days_counted': '计息天数', 'interest_rate': '利率',
    }

    def __init__(self, account: str='', account_code: int=None, institution: str='',
                 days_counted: float=None, interest_rate: float=None):
        super(InterestRate, self).__init__()
        self.account = str_check(account)
        self.account_code = int_check(account_code)
        self.institution = str_check(institution)
        self.days_counted = float_check(days_counted)
        self.interest_rate = float_check(interest_rate)


class ProductInfo(DataObject):
    inner2outer_map = {
        'pro_id': '产品_id', 'name': '产品简称', 'full_name': '产品全称', 'code': '产品代码', 'confirm_delay': '确认日',
    }

    def __init__(self, pro_id: int=None, name: str= '', full_name: str= '', code: str= '', confirm_delay: int=None):
        super(ProductInfo, self).__init__()
        self.pro_id = int_check(pro_id)
        self.name = str_check(name)
        self.full_name = str_check(full_name)
        self.code = str_check(code)
        self.confirm_delay = int_check(confirm_delay)


if __name__ == '__main__':
    pass
