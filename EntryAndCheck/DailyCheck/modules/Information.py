# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime

from jetend.Interface import AttributeObject
from jetend.DataCheck import *


class FundFlow(AttributeObject):
    inner2outer_map = {
        'investor': '投资人', 'trade_class': '交易类型', 'date': '日期', 'institution': '机构名称',
        'security_code': '产品代码', 'security_name': '产品名称',
        'trade_amount': '发生金额', 'trade_price': '净值', 'trade_volume': '份额',
        'currency': '币种', 'confirmation_date': '确认日期',
    }

    @property
    def date(self):
        date = self.get_attr('date')
        assert isinstance(date, datetime.date), '{} {}'.format(date, type(date))
        return date

    @property
    def security_name(self):
        security_name = self.get_attr('security_name')
        if len(security_name) <= 8:
            pass
        else:
            security_name = self.env.info_board.find_product_name_by_name(security_name)
        return security_name


class TaFlow(AttributeObject):
    """在途申赎流水"""
    inner2outer_map = {
        'investor': 'name', 'id_number': 'idnumber', 'date': 'date', 'security_name': 'product_name',
        'trade_class': 'type', 'trade_amount': 'amount', 'trade_price': 'netvalue', 'trade_volume': 'share',
        'sales_agency': 'sales_agency', 'trade_fee': 'fee',
        'confirmation_date': 'confirmation_date', 'check_status': 'check_status',
    }

    @property
    def date(self):
        date = self.get_attr('date')
        assert isinstance(date, datetime.date), '{} {}'.format(date, type(date))
        return date

    @property
    def security_name(self):
        security_name = self.get_attr('security_name')
        if len(security_name) <= 8:
            pass
        else:
            security_name = self.env.info_board.find_product_name_by_name(security_name)
            self.set_attr('security_name', security_name)
        return security_name

    @security_name.setter
    def security_name(self, value: str):
        self.set_attr('security_name', value)

    @property
    def investor(self):
        investor = self.get_attr('investor')
        if self.id_number is None:
            return investor
        if len(self.id_number) > 6 or '久铭' not in investor:     # 非久铭产品
            pass
        else:
            try:
                investor = self.env.info_board.find_product_name_by_name(investor)
            except RuntimeError as r_error:   # 处理其他基金作为申购人
                if '久铭' in investor:
                    raise r_error
                else:
                    pass
            except TypeError as t_error:
                print(self.__dict_data__)
                raise t_error
            self.set_attr('investor', investor)
        return investor

    @investor.setter
    def investor(self, value: str):
        self.set_attr('investor', value)

    @property
    def env(self):
        from modules.Modules import Modules
        return Modules.get_instance()


class TradeFeeRate(AttributeObject):
    inner2outer_map = {
        'product': '产品', 'institution': '券商', 'security_type': '种类', 'fee_rate': '费率',
        'update_date': '更新日期', 'yearly_fee_rate': '港股通组合费(年度费率)',
    }

    @property
    def update_date(self):
        update_date = self.get_attr('update_date')
        if not isinstance(update_date, datetime.date):
            update_date = date_check(update_date)
            self.set_attr('update_date', update_date)
        assert isinstance(update_date, datetime.date)
        return update_date
