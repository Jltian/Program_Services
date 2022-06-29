# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import Contract, Flowing, BaseInfo, SecurityInfo
from utils.Constants import *


class InterestsFlow(BaseInfo):
    """存款借款利息"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',  'account_name': '科目',
        'daily_interest': '当日利息',
    }
    # '产品', '日期', '机构','科目编号','科目', '当日利息'

    # def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
    #              account_name: str = '', daily_interest: float = None, ):
    #     if institution == '':
    #         institution = ''
    #     if institution == '':
    #         institution = ''
    #
    #     AccountClass.__init__(self, account_name=account_name, )
    #     Flowing.__init__(self, product=product, institution=institution, date=date)
    #     self.daily_interest = float_check(daily_interest)

    @property
    def institution(self):
        institution = str_check(self.get_attr('institution'))
        if institution == '美股收益互换':
            institution = '中信美股'
        if institution == '港股收益互换':
            institution = '中信港股'
        assert is_valid_str(institution), str(self.__dict__)
        return institution

    @property
    def daily_interest(self):
        daily_interest = float_check(self.get_attr('daily_interest'))
        assert is_valid_float(daily_interest), str(self.__dict__)
        return daily_interest

    @classmethod
    def init_from(cls, acc, i_rate):
        from sheets.entry.Account import EntryAccount
        from sheets.Information import InterestRate
        assert isinstance(acc, EntryAccount) and isinstance(i_rate, InterestRate)
        if acc.account_name == '银行存款':
            institution = acc.sub_account
        elif acc.account_name == '存出保证金':
            institution = acc.base_account
        elif acc.account_name == '短期借款':
            institution = acc.base_account
            raise NotImplementedError(acc)
        else:
            raise NotImplementedError(acc)
        if acc.account_name == '短期借款':
            if institution in ('长江两融', '招商两融'):
                if acc.date.isoweekday() in (6, 7, ):
                    multiplier = 0
                elif acc.date.isoweekday() in (5, ):
                    multiplier = 3
                else:
                    multiplier = 1
            else:
                raise NotImplementedError(acc)
        else:
            multiplier = 1
        daily_interest = multiplier * acc.net_value * i_rate.interest_rate / i_rate.days_counted
        if acc.account_name in ('银行存款', '存出保证金'):
            if - 1.0 < daily_interest <= 0:
                daily_interest = 0.0
            else:
                assert daily_interest >= 0, '{}\n{}'.format(acc, i_rate)
        else:
            assert daily_interest <= 0.0, '{}\n{}'.format(acc, i_rate)
        return cls(
            product=acc.product, date=acc.date, institution=institution, account_name=acc.account_name,
            daily_interest=daily_interest,
        )

    def generate_journal_entry(self):
        new_journal_entry_list = list()
        if round(abs(self.daily_interest), 2) < 0.01:
            return new_journal_entry_list

        if self.account_name in ('银行存款', ):
            assert self.daily_interest > 0, str(self.__dict__)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='存款利息计提', account_name='应收利息', account_level_2='银行存款利息',
                    account_level_3=self.institution, account_level_4='活期存款',
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.daily_interest)),
                self.__ggje__().update(
                    abstract='存款利息计提', account_name='利息收入', account_level_2='存款利息收入',
                    account_level_3=self.institution, account_level_4='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.daily_interest), ),
            ])
        elif self.account_name in ('存出保证金', ):
            assert self.daily_interest > 0, str(self.__dict__)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='存款利息计提', account_name='应收利息', account_level_2='存出保证金利息',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.daily_interest)),
                self.__ggje__().update(
                    abstract='存款利息计提', account_name='利息收入', account_level_2='存款利息收入',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.daily_interest), ),
            ])
        elif self.account_name in ('短期借款',):
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='借款利息计提', account_name='利息支出', account_level_2='借款利息支出',
                    account_level_3=self.institution, account_level_4='借款',
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.daily_interest)),
                self.__ggje__().update(
                    abstract='借款利息计提', account_name='应付利息', account_level_2='短期借款利息',
                    account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.daily_interest)),
            ])
        else:
            raise NotImplementedError(self)
        return new_journal_entry_list


class BondIntersetsFlow(BaseInfo, SecurityInfo):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'security_name': '标的名称', 'security_code': '标的代码',
        'hold_amount': '持有数量', 'daily_interest_receivable': '当日应收利息',
    }
    # '产品','日期', '标的名称', '标的代码','持有数量','当日应收利息'

    # def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
    #              security_name: str = '', security_code: str = '',
    #              hold_amount: float = None, daily_interest_receivable: float = ''):
    #     Contract.__init__(self, security_code=security_code, security_name=security_name)
    #     Flowing.__init__(self, product=product, institution=institution, date=date)
    #     self.hold_amount = float_check(hold_amount)
    #     self.daily_interest_receivable = float_check(daily_interest_receivable)
    @property
    def hold_amount(self):
        hold_amount = float_check(self.get_attr('hold_amount'))
        assert is_valid_float(hold_amount), str(self.__dict__)
        return hold_amount

    @property
    def daily_interest_receivable(self):
        daily_interest_receivable = float_check(self.get_attr('daily_interest_receivable'))
        assert is_valid_float(daily_interest_receivable), str(self.__dict__)
        return daily_interest_receivable

    @classmethod
    def init_from(cls, obj):
        from sheets.entry.Position import EntryPosition
        if isinstance(obj, EntryPosition):
            assert obj.account_name == '债券投资', '{}'.format(obj.account_name)
            daily_interest_receivable = obj.hold_volume * obj.env.wind_board.float_field(
                'self.bond_interest_on_date', obj.security_code, obj.date,
            )
            if daily_interest_receivable < 0.0:
                daily_interest_receivable = obj.hold_volume * obj.market_board.accrued_interest(
                    security_code=obj.security_code, date=obj.date
                )
            if daily_interest_receivable < 0:
                # 假如当天债券付息
                raise RuntimeError('未知债券付息 {}\n{}'.format(daily_interest_receivable, obj))
            return cls(
                product=obj.product, date=obj.date, institution=obj.institution,
                security_name=obj.security_name, security_code=obj.security_code,
                hold_amount=obj.hold_volume,
                daily_interest_receivable=daily_interest_receivable
            )
        else:
            raise NotImplementedError(type(obj))

    def generate_journal_entry(self):
        new_journal_entry_list = list()
        daily_interest_receivable = round(self.daily_interest_receivable, 2)
        assert daily_interest_receivable >= 0, str(self)
        if abs(daily_interest_receivable) < 0.01:
            return new_journal_entry_list

        new_journal_entry_list.extend([
            self.__ggje__().update(
                abstract='债券利息计提', account_name='应收利息', account_level_2='债券利息',
                account_level_3=self.institution, account_level_4=self.security_name,
                debit_credit=SIDE_DEBIT_CN, amount=round(self.daily_interest_receivable, 2)),
            self.__ggje__().update(
                abstract='债券利息计提', account_name='利息收入', account_level_2='债券利息收入',
                account_level_3=self.institution, account_level_4=self.security_name,
                debit_credit=SIDE_CREDIT_CN, amount=round(self.daily_interest_receivable, 2)),
        ])
        return new_journal_entry_list

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.date,
            account_level_4=self.security_code_name,
        )
