# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import Flowing, Trading
from utils.Constants import *


class TaConfirmFlow(Flowing, Trading):
    """自有产品申赎确认"""
    inner2outer_map = {
         'investor': '投资人', 'trade_class': '业务类型', 'date': '日期',
         'product': '产品', 'amount': '资金数目', 'price': '单位净值', 'volume': '基金份额',
         'confirm_date': '确认日',
     }

    def __init__(self, investor: str= '', trade_class: str = '', date: datetime.date = None,
                 product: str = '', amount: float = None, price: float = None, volume: float = None,
                 confirm_date: datetime.date = None, **kwargs):
        Flowing.__init__(self, product=product, date=date, institution='久铭')
        Trading.__init__(self, trade_volume=volume, trade_amount=amount, trade_price=price,
                         cash_move=amount, currency='RMB')
        self.investor = str_check(investor)
        self.trade_class = str_check(trade_class)
        self.price = float_check(price)
        self.volume = float_check(volume)
        self.confirm_date = date_check(confirm_date)

    @property
    def institution(self):
        raise NotImplementedError

    @property
    def amount(self):
        return abs(self.trade_amount)

    def generate_journal_entry(self):
        new_journal_entry_list = list()
        tag = self.trade_class.strip()

        # 周五确认
        if self.confirm_date in (datetime.date(2018, 1, 2), ):
            return list()

        if tag == '申购':
            assert self.volume > 0, str(self)
            assert self.amount > 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='其他应付款', account_level_2='未确认申购款', account_level_3=self.investor,
                    debit_credit=SIDE_DEBIT_CN, amount=self.amount),
                self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                       debit_credit=SIDE_CREDIT_CN, amount=self.amount - self.volume),
                self.__ggje__().update(account_name='实收基金', debit_credit=SIDE_CREDIT_CN, amount=self.volume),
            ])
        elif tag in ('赎回', ):
            assert self.volume < 0, str(self)
            if self.investor == '上海久铭投资管理有限公司' and self.confirm_date == datetime.date(2018, 12, 21):
                return list()
            new_journal_entry_list.extend([
                self.__ggje__().update(account_name='实收基金', debit_credit=SIDE_DEBIT_CN, amount=abs(self.volume)),
                self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                       debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount) - abs(self.volume)),
                self.__ggje__().update(account_name='应付赎回款', account_level_2=self.investor,
                                       debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount)),
            ])
        elif tag in ('赎回业绩报酬', '基金转出业绩报酬'):
            assert self.volume < 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(account_name='实收基金', debit_credit=SIDE_DEBIT_CN, amount=abs(self.volume)),
                self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                       debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount) - abs(self.volume)),
                self.__ggje__().update(
                    account_name='应付管理人报酬', account_level_2='业绩报酬',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount)),
            ])
        elif tag == '份额转入':
            assert self.volume > 0, str(self)
            assert self.amount > 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='证券清算款', account_level_2='待交收基金转让款', account_level_3='久铭',
                    account_level_4=self.product, debit_credit=SIDE_DEBIT_CN, amount=self.amount),
                self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                       debit_credit=SIDE_CREDIT_CN, amount=self.amount - self.volume),
                self.__ggje__().update(account_name='实收基金', debit_credit=SIDE_CREDIT_CN, amount=self.volume),
            ])
        elif tag == '份额转出':
            assert self.volume < 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(account_name='实收基金',  # account_level_2=self.investor,
                                       debit_credit=SIDE_DEBIT_CN, amount=abs(self.volume)),
            ])
            new_journal_entry_list.extend([
                self.__ggje__().update(account_name='实收基金', debit_credit=SIDE_DEBIT_CN, amount=abs(self.volume)),
                self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                       debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount) - abs(self.volume)),
                self.__ggje__().update(
                    account_name='证券清算款', account_level_2='待交收基金转让款', account_level_3='久铭',
                    account_level_4=self.product, debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount)),
            ])
        elif tag == '基金转入':
            new_journal_entry_list.extend([
                self.__ggje__().update(account_name='应收申购款', account_level_2='待转换',
                                       debit_credit=SIDE_DEBIT_CN, amount=self.amount),
                self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                       debit_credit=SIDE_CREDIT_CN, amount=self.amount - self.volume),
                self.__ggje__().update(account_name='实收基金',
                                       debit_credit=SIDE_CREDIT_CN, amount=self.volume),
            ])
        elif tag == '基金转出':
            new_journal_entry_list.extend([
                self.__ggje__().update(account_name='实收基金', debit_credit=SIDE_DEBIT_CN, amount=abs(self.volume)),
                self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                       debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount) - abs(self.volume)),
                self.__ggje__().update(account_name='应付赎回款', account_level_2='待转换',
                                       debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount)),
            ])
        elif tag == '计提业绩报酬':
            if self.volume < 0:     # 赎回业绩报酬
                new_journal_entry_list.extend([
                    self.__ggje__().update(account_name='实收基金', debit_credit=SIDE_DEBIT_CN, amount=abs(self.volume)),
                    self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                           debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount) - abs(self.volume)),
                    self.__ggje__().update(
                        account_name='应付管理人报酬', account_level_2='业绩报酬',
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount)),
                ])
                # if '久铭' in self.investor:
                #     raise NotImplementedError(self)
            elif self.volume > 0:       # 业绩报酬直接转给公司
                assert '久铭' in self.investor, str(self)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='应付管理人报酬', account_level_2='业绩报酬',
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount)),
                    self.__ggje__().update(
                        account_name='实收基金', debit_credit=SIDE_CREDIT_CN, amount=abs(self.volume)),
                    self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                           debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount) - abs(self.volume)),
                ])
            else:
                raise NotImplementedError(self)
            # if self.investor == '上海久铭投资管理有限公司' and self.confirm_date == datetime.date(2018, 12, 21):
            #     pass
            # else:
            #     # new_journal_entry_list.extend([
            #     #     self.__ggje__().update(account_name='管理人报酬', account_level_2='业绩报酬',
            #     #                            account_level_3='久铭',
            #     #                            debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount)),
            #     #     self.__ggje__().update(account_name='应付管理人报酬',
            #     #                            debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount)),
            #     # ])

        elif tag == '分红':
            pass
        else:
            raise NotImplementedError(self)
        return new_journal_entry_list

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.running_date,
            abstract=self.trade_class.strip(),
            account_level_4=self.investor,
        )

    @property
    def running_date(self):
        return self.confirm_date
