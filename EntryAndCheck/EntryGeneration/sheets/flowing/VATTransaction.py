# -*- encoding: UTF-8 -*-

from sheets.Elements import AccountClass, BaseInfo, TradeInfo, ValueAddedTaxInfo
from jetend.DataCheck import *


class VATTransaction(AccountClass, BaseInfo, TradeInfo, ValueAddedTaxInfo):
    """价差收入应付增值税"""
    inner2outer_map = {
        'product': '产品', 'date': '日期',  'institution': '机构',
        'account_name': '科目', 'account_code': '科目编号',
        'security_code': '标的代码', 'security_name': '标的名称',
        'tax_cost': '计税成本', 'trade_volume': '卖出数量', 'trade_price': '卖出价格',
        'value_add_amount': '价差收入', 'vat': '应交增值税', 'building_tax': '应交城建税',
        'education_surcharge': '应交教育费附加', 'local_education_surcharge': '应交地方教育费附加',
        'total_tax': '应交税金',
    }

    @property
    def tax_cost(self):
        tax_cost = float_check(self.get_attr('tax_cost'))
        assert is_valid_float(tax_cost), str(self.__dict__)
        return tax_cost

    # def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
    #              account_code: int = None, account_name: str = '',
    #              security_code: str = '', security_name: str = '',
    #              tax_cost: float = None, trade_volume: float = None, trade_price: float = None,
    #              value_add_amount: float = None, vat: float = None, building_tax: float = None,
    #              education_surcharge: float = None, local_education_surcharge: float = None,
    #              total_tax: float = None,
    #              ):
    #     AccountClass.__init__(self, account_code=account_code, account_name=account_name)
    #     Contract.__init__(self, security_code=security_code, security_name=security_name)
    #     Flowing.__init__(self, product=product, institution=institution, date=date)
    #     ValueAddedTax.init_property(self, vat=vat, building_tax=building_tax, education_surcharge=education_surcharge,
    #                            local_education_surcharge=local_education_surcharge, total_tax=total_tax)
    #     self.tax_cost = float_check(tax_cost)
    #     self.trade_price, self.trade_volume = float_check(trade_price), float_check(trade_volume)
    #     self.value_add_amount = float_check(value_add_amount)

    # def generate_journal_entry(self):
    #     new_journal_entry_list = list()
    #     new_journal_entry_list.extend([
    #         self.__ggje__().update(abstract='价差收入应付增值税', account_name='投资收益', account_level_2='增值税抵减',
    #                                account_level_3=self.institution, account_level_4=self.security_code,
    #                                debit_credit=SIDE_DEBIT_CN, amount=self.vat),
    #         self.__ggje__().update(abstract='价差收入应付增值税', account_name='应交税费', account_level_2='应交增值税',
    #                                account_level_3='价差收入',
    #                                debit_credit=SIDE_CREDIT_CN, amount=self.vat),
    #         self.__ggje__().update(abstract='应交城建税', account_name='税金及附加', account_level_2='城建税',
    #                                debit_credit=SIDE_DEBIT_CN, amount=self.building_tax),
    #         self.__ggje__().update(abstract='应交城建税', account_name='应交税费', account_level_2='附加税',
    #                                account_level_3='城建税',
    #                                debit_credit=SIDE_CREDIT_CN, amount=self.building_tax),
    #         self.__ggje__().update(abstract='应交教育费附加', account_name='税金及附加', account_level_2='教育费附加',
    #                                debit_credit=SIDE_DEBIT_CN, amount=self.education_surcharge),
    #         self.__ggje__().update(abstract='应交教育费附加', account_name='应交税费', account_level_2='附加税',
    #                                account_level_3='教育费附加',
    #                                debit_credit=SIDE_CREDIT_CN, amount=self.education_surcharge),
    #         self.__ggje__().update(abstract='应交地方教育费附加', account_name='税金及附加', account_level_2='地方教育费附加',
    #                                debit_credit=SIDE_DEBIT_CN, amount=self.local_education_surcharge),
    #         self.__ggje__().update(abstract='应交地方教育费附加', account_name='应交税费', account_level_2='附加税',
    #                                account_level_3='地方教育费附加',
    #                                debit_credit=SIDE_CREDIT_CN, amount=self.local_education_surcharge),
    #     ])
    #     return new_journal_entry_list
