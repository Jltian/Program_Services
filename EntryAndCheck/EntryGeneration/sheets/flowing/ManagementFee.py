# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import Flowing, BaseInfo
from utils.Constants import *


class ManagementFeePayableFlow(BaseInfo):
    """
    应付管理费计提
    计算方式 产品净值 * 管理费率
    """
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'fee_type': 'fee_type', 'daily_fee': '当日管理费',
    }

    @property
    def fee_type(self):
        return str_check(self.get_attr('fee_type'))

    @property
    def daily_fee(self):
        return float_check(self.get_attr('daily_fee'))

    def generate_journal_entry(self):
        new_journal_entry_list = list()
        if abs(round(self.daily_fee, 2)) < 0.01:
            return new_journal_entry_list

        tag = self.fee_type.strip()
        if tag == '应付管理费计提':
            assert self.daily_fee > 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='应付管理费计提', account_name='管理人报酬', account_level_2='固定管理费',
                    debit_credit=SIDE_DEBIT_CN, amount=abs(round(self.daily_fee, 2))),
                self.__ggje__().update(
                    abstract='应付管理费计提', account_name='应付管理人报酬', account_level_2='固定管理费',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(round(self.daily_fee, 2))),
            ])
        # elif tag == '业绩报酬计提':
        #     assert self.daily_fee > 0, str(self)
        #     new_journal_entry_list.extend([
        #         self.__ggje__().update(
        #             abstract='业绩报酬计提', account_name='管理人报酬', account_level_2='业绩报酬',
        #             debit_credit=SIDE_DEBIT_CN, amount=self.daily_fee, ),
        #         self.__ggje__().update(
        #             abstract='业绩报酬计提', account_name='应付管理人报酬', account_level_2='业绩报酬',
        #             debit_credit=SIDE_CREDIT_CN, amount=self.daily_fee, ),
        #     ])
        else:
            raise NotImplementedError(tag)
        return new_journal_entry_list


class ManagementFeeReceivableFlow(Flowing):
    """
    管理费返还

    投资自有产品的时候为了避免管理费重复收取进行管理费返还

    计算方式 被投产品持有份额 * 单位净值 * 管理费率
    """
    inner2outer_map = {
        'investor': '产品', 'date': '日期', 'invested': '被投产品', 'fee_return': '当日返还管理费',
    }
    # 产品, 日期, 机构, 标的名称, 管理费返还

    def __init__(self, investor: str = '', date: datetime.date = None, invested: str = '', fee_return: float = None, ):
        Flowing.__init__(self, product=investor, date=date)
        self.investor = str_check(investor)
        self.invested = str_check(invested)
        self.fee_return = float_check(fee_return)

    def generate_journal_entry(self):
        new_journal_entry_list = list()
        if abs(round(self.fee_return, 2)) < 0.01:
            return new_journal_entry_list

        new_journal_entry_list.extend([
            self.__ggje__().update(
                abstract='应收管理费返还', account_name='其他应收款', account_level_2='管理费返还',
                account_level_3=self.invested,
                debit_credit=SIDE_DEBIT_CN, amount=abs(round(self.fee_return, 2))),
            self.__ggje__().update(
                abstract='应收管理费返还', account_name='公允价值变动损益', account_level_2='久铭',
                account_level_3=self.invested, debit_credit=SIDE_CREDIT_CN, amount=abs(round(self.fee_return, 2))),
        ])
        return new_journal_entry_list
