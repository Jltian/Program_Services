# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import BaseInfo, SecurityInfo, ValueAddedTaxInfo
from utils.Constants import *


class VATBondInterests(BaseInfo, SecurityInfo, ValueAddedTaxInfo):
    """债券利息收入应付增值税"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'security_code': '标的代码', 'security_name': '标的名称',
        'holding_volume': '持有数量', 'interest_receivable': '当日应收利息',
        'vat': '应交增值税', 'building_tax': '应交城建税',
        'education_surcharge': '应交教育费附加', 'local_education_surcharge': '应交地方教育费附加',
        'total_tax': '应交税金',
    }
    # 科目, 已交税金, 剩余应交税金, ID
    account_code, account_name = 1103, '债券投资'

    # def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
    #              security_code: str = '', security_name: str = '',
    #              holding_volume: float = None, interest_receivable: float = None,
    #              vat: float = None, building_tax: float = None,
    #              education_surcharge: float = None, local_education_surcharge: float = None,
    #              total_tax: float = None):
    #     Contract.__init__(self, security_code=security_code, security_name=security_name)
    #     Flowing.__init__(self, product=product, date=date, institution=institution)
    #     ValueAddedTax.init_property(self, vat=vat, building_tax=building_tax, education_surcharge=education_surcharge,
    #                            local_education_surcharge=local_education_surcharge, total_tax=total_tax)
    #     self.holding_volume = float_check(holding_volume)
    #     self.interest_receivable = round(float_check(interest_receivable), 6)

    @property
    def interest_receivable(self):
        interest_receivable = float_check(self.get_attr('interest_receivable'))
        assert is_valid_float(interest_receivable), str(self.__dict__)
        return interest_receivable

    @property
    def vat(self):
        vat = float_check(self.get_attr('vat'))
        if is_valid_float(vat):
            return round(vat, 4)
        else:
            return self.interest_receivable * TAX_RATE_VAT / (1 + TAX_RATE_VAT)

    @classmethod
    def init_from(cls, obj):
        from sheets.flowing.InterestsFlow import BondIntersetsFlow
        assert isinstance(obj, BondIntersetsFlow)
        return cls(
            product=obj.product, date=obj.date, institution=obj.institution,
            security_code=obj.security_code, security_name=obj.security_name, holding_volume=obj.hold_amount,
            interest_receivable=obj.daily_interest_receivable,
            vat=obj.daily_interest_receivable * TAX_RATE_VAT / (1 + TAX_RATE_VAT),
            # building_tax=obj.daily_interest_receivable * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_BT,
            # education_surcharge=obj.daily_interest_receivable * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_ES,
            # local_education_surcharge=obj.daily_interest_receivable * TAX_RATE_VAT / (
            #         1 + TAX_RATE_VAT) * TAX_RATE_LES,
        )

    def generate_journal_entry(self):
        new_journal_entry_list = list()

        if abs(self.vat) < 0.01:
            return list()

        new_journal_entry_list.extend([
            self.__ggje__().update(
                account_name='利息收入', account_level_2='债券利息增值税抵减', account_level_3=self.institution,
                account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN, amount=self.vat,
            ),
            self.__ggje__().update(
                account_name='应交税费', account_level_2='增值税', account_level_3='债券利息收入',
                account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                amount=self.vat),
            self.__ggje__().update(
                account_name='税金及附加', account_level_2='增值税附加', account_level_3='城建税',
                debit_credit=SIDE_DEBIT_CN, amount=self.building_tax),
            self.__ggje__().update(
                account_name='应交税费', account_level_2='增值税附加城建税', account_level_3='债券利息收入',
                account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                amount=self.building_tax),
            self.__ggje__().update(
                account_name='税金及附加', account_level_2='增值税附加', account_level_3='教育费附加',
                debit_credit=SIDE_DEBIT_CN, amount=self.education_surcharge),
            self.__ggje__().update(
                account_name='应交税费', account_level_2='增值税附加教育费', account_level_3='债券利息收入',
                account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                amount=self.education_surcharge, ),
            self.__ggje__().update(
                account_name='税金及附加', account_level_2='增值税附加', account_level_3='地方教育费附加',
                debit_credit=SIDE_DEBIT_CN, amount=self.local_education_surcharge),
            self.__ggje__().update(
                account_name='应交税费', account_level_2='增值税附加地方教育费', account_level_3='债券利息收入',
                account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                amount=self.local_education_surcharge),
        ])
        return new_journal_entry_list

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.date, abstract='债券利息应付增值税计提',
            account_level_5=self.security_code_name,
        )
