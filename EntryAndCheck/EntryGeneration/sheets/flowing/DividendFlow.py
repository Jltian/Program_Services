# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import BaseInfo, SecurityInfo
from utils.Constants import *


class DividendFlowing(BaseInfo, SecurityInfo):
    """股利"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'security_code': '股票代码', 'security_name': '股票名称',
        'trade_class': '操作类型', 'dividend_mode': '派息方式',
        'cash_amount': '现金数量', 'share_amount': '股份数量', 'currency': '币种',
    }
    # ID, check_status

    def __init__(
            self, product: str = '', date: datetime.date = None, institution: str = '',
            security_code: str = '', security_name: str = '',
            trade_class: str = '', dividend_mode: str = '',
            cash_amount: float = None, currency: str = '', share_amount: float = None,
    ):
        BaseInfo.__init__(self, product=product, date=date, institution=institution)
        SecurityInfo.__init__(self)
        self.__dict__.update({
            'security_code': str_check(security_code.upper()),
            'security_name': str_check(security_name.upper()),
        })
        self.trade_class = str_check(trade_class)
        self.dividend_mode = str_check(dividend_mode)
        self.cash_amount = float_check(cash_amount)
        self.share_amount = float_check(share_amount)
        self.currency = str_check(CURRENCY_MAP[currency.upper()])

    def generate_journal_entry(self):
        new_journal_entry_list = list()

        if self.trade_class == '除权除息':
            if self.currency == 'RMB':
                cash_amount = self.cash_amount
            elif self.currency == 'HKD':
                cash_amount = self.cash_amount * self.env.wind_board.exchange_settle_rate(
                    'HKD', 'CNY', 'HKS', self.date)
            else:
                raise NotImplementedError(self)

            if self.dividend_mode == '债券付息':
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract=self.trade_class, account_name='其他应收款', account_level_2='债券利息',
                        account_level_3=self.institution, account_level_4=self.security_name,
                        debit_credit=SIDE_DEBIT_CN, amount=cash_amount,
                    ),
                    # self.__ggje__().update(
                    #     abstract=self.trade_class, account_name='应交税费', account_level_2='债券利息收入',
                    #     account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN,
                    #     amount=cash_amount,
                    # ),
                    self.__ggje__().update(
                        abstract=self.trade_class, account_name='应收利息', account_level_2='债券利息',
                        account_level_3=self.institution, account_level_4=self.security_name,
                        debit_credit=SIDE_CREDIT_CN, amount=cash_amount),
                ])
            elif self.dividend_mode == '现金派息':
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract=self.trade_class, account_name='应收股利', account_level_2=self.institution,
                        account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN, amount=cash_amount),
                    self.__ggje__().update(
                        abstract=self.trade_class, account_name='投资收益', account_level_2='股利收益',
                        account_level_3=self.institution, account_level_4=self.security_name,
                        debit_credit=SIDE_CREDIT_CN, amount=cash_amount),
                ])
            else:
                raise NotImplementedError(self)
        elif self.trade_class == '内部结转股利收益':
            assert self.currency == 'RMB', self
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=self.trade_class, account_name='证券清算款', account_level_2='股利收益',
                    account_level_3=self.institution, account_level_4=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_amount)),
                self.__ggje__().update(
                    abstract=self.trade_class, account_name='投资收益', account_level_2='股利收益',
                    account_level_3=self.institution, account_level_4=self.security_name,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_amount)),
            ])

        else:
            raise NotImplementedError(self)
        # if self.ex_date == d:
        #     pos_list = env.positions.find_value_where(account='股票投资', underlying_code=self.security_code,
        #                                               date=self.ex_date)
        #     for pos in pos_list:
        #         assert isinstance(pos, Position)
        #         product, number, institution = pos.product, pos.hold_volume, pos.institution
        #         if self.cash_dividend > 0:
        #             new_journal_entry_list.extend([
        #                 self.__ggje__().update(
        #                 product=product, date=self.ex_date, abstract=self.dividend_mode,
        #                 account_name='应收股利', account_level_2=institution, debit_credit=SIDE_DEBIT_CN,
        #                 amount=number * self.cash_dividend),
        #                 self.__ggje__().update(
        #                 product=product, date=self.ex_date, abstract=self.dividend_mode,
        #                 account_name='投资收益', account_level_2='股利收益', account_level_3=institution,
        #                 account_level_4=self.security_code, debit_credit=SIDE_CREDIT_CN,
        #                 amount=number * self.cash_dividend),
        #             ])
        #
        #         if self.capital_stock > 0:
        #             env.trigger_event(event_type=EventType.PositionUpdate,
        #                               data=Trade(product=self.product, institution=self.institution,
        #                                          security_name=self.security_name,
        #                                          security_code=self.security_code, security_type=SECURITY_TYPE_FUTURE,
        #                                          trade_direction=DIRECTION_BUY,
        #                                          trade_volume=number*self.capital_stock,
        #                                          trade_price=0,
        #                                          trade_amount=0,
        #                                          trade_offset=OFFSET_OPEN))
        #
        #         if self.stock_dividend > 0:
        #             env.trigger_event(event_type=EventType.PositionUpdate,
        #                               data=Trade(product=self.product, institution=self.institution,
        #                                          security_name=self.security_name,
        #                                          security_code=self.security_code, security_type=SECURITY_TYPE_FUTURE,
        #                                          trade_direction=DIRECTION_BUY,
        #                                          trade_volume=number*self.stock_dividend,
        #                                          trade_price=0,
        #                                          trade_amount=0,
        #                                          trade_offset=OFFSET_OPEN))
        #     raise NotImplementedError(self)
        #
        return new_journal_entry_list
