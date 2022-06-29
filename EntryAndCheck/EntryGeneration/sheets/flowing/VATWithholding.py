# -*- encoding: UTF-8 -*-

from sheets.Elements import AccountClass, BaseInfo, ValueAddedTaxInfo
from utils.Constants import *


class VATSum(AccountClass, BaseInfo, ValueAddedTaxInfo):
    """增值税预估"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'vat_type': '增值税类型',
        'vat': '预提增值税', 'building_tax': '预提城建税', 'education_surcharge': '预提教育费附加',
        'local_education_surcharge': '预提地方教育费附加', 'total_tax': '预提税金',
    }

    def update_by(self, obj):
        from sheets.Elements import ValueAddedTaxInfo
        assert isinstance(obj, ValueAddedTaxInfo)
        self.set_attr('vat', self.get_attr('vat') + obj.vat)
        self.set_attr(
            'building_tax',
            self.get_attr('building_tax') + obj.building_tax
        )
        self.set_attr(
            'education_surcharge',
            self.get_attr('education_surcharge') + obj.education_surcharge
        )
        self.set_attr(
            'local_education_surcharge',
            self.get_attr('local_education_surcharge') + obj.local_education_surcharge
        )
        self.set_attr('total_tax', None)
        return self

    @property
    def institution(self):
        raise RuntimeError('无机构信息'.format(self.__dict__))

    def generate_journal_entry(self):
        new_journal_entry_list = list()

        if abs(self.total_tax) < 0.01:
            return list()

        if self.vat_type == '预提':
            tag = '增值税预提'
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='公允价值变动损益', account_level_2='预估增值税抵减',
                    account_level_3='增值税预提', debit_credit=SIDE_DEBIT_CN, amount=self.vat),
                self.__ggje__().update(
                    abstract=tag, account_name='预提费用', account_level_2='预提增值税', account_level_3='增值税',
                    debit_credit=SIDE_CREDIT_CN, amount=self.vat),
                self.__ggje__().update(
                    abstract=tag, account_name='预估税金及附加', account_level_2='城建税',
                    debit_credit=SIDE_DEBIT_CN, amount=self.building_tax),
                self.__ggje__().update(
                    abstract=tag, account_name='预提费用', account_level_2='预提附加税', account_level_3='城建税',
                    debit_credit=SIDE_CREDIT_CN, amount=self.building_tax),
                self.__ggje__().update(
                    abstract=tag, account_name='预估税金及附加', account_level_2='教育费附加',
                    debit_credit=SIDE_DEBIT_CN, amount=self.education_surcharge),
                self.__ggje__().update(
                    abstract=tag, account_name='预提费用', account_level_2='预提附加税', account_level_3='教育费附加',
                    debit_credit=SIDE_CREDIT_CN, amount=self.education_surcharge),
                self.__ggje__().update(
                    abstract=tag, account_name='预估税金及附加', account_level_2='地方教育费附加',
                    debit_credit=SIDE_DEBIT_CN, amount=self.local_education_surcharge),
                self.__ggje__().update(
                    abstract=tag, account_name='预提费用', account_level_2='预提附加税', account_level_3='地方教育费附加',
                    debit_credit=SIDE_CREDIT_CN, amount=self.local_education_surcharge),
            ])
        elif self.vat_type == '价差':
            tag = '价差收入应付增值税'
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='投资收益', account_level_2='价差收入', account_level_3='税金',
                    account_level_4='增值税抵减', debit_credit=SIDE_DEBIT_CN, amount=self.vat),
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2='增值税', account_level_3='价差收入',
                    account_level_4='应税标的', debit_credit=SIDE_CREDIT_CN, amount=self.vat),
                self.__ggje__().update(
                    abstract=tag, account_name='税金及附加', account_level_2='增值税附加', account_level_3='城建税',
                    debit_credit=SIDE_DEBIT_CN, amount=self.building_tax),
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2='增值税附加城建税', account_level_3='价差收入',
                    account_level_4='应税标的', debit_credit=SIDE_CREDIT_CN, amount=self.building_tax),
                self.__ggje__().update(
                    abstract=tag, account_name='税金及附加', account_level_2='增值税附加', account_level_3='教育费附加',
                    debit_credit=SIDE_DEBIT_CN, amount=self.education_surcharge),
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2='增值税附加教育费', account_level_3='价差收入',
                    account_level_4='应税标的', debit_credit=SIDE_CREDIT_CN, amount=self.education_surcharge),
                self.__ggje__().update(
                    abstract=tag, account_name='税金及附加', account_level_2='增值税附加', account_level_3='地方教育费附加',
                    debit_credit=SIDE_DEBIT_CN, amount=self.local_education_surcharge),
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2='增值税附加地方教育费', account_level_3='价差收入',
                    account_level_4='应税标的', debit_credit=SIDE_CREDIT_CN, amount=self.local_education_surcharge),
            ])
        else:
            raise NotImplementedError(self.vat_type)
        return new_journal_entry_list


class VATWithholding(AccountClass, BaseInfo, ValueAddedTaxInfo):
    """增值税预提明细条目"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'account_name': '科目', 'account_code': '科目编号',
        'security_code': '标的代码', 'security_name': '标的名称',
        'holding_volume': '持有数量', 'tax_cost': '计税成本',
        'closing_price': '收盘价', 'assets_value': '市值',
        'floating': '公允价值变动损益', 'vat': '预提增值税', 'building_tax': '预提城建税',
        'education_surcharge': '预提教育费附加', 'local_education_surcharge': '预提地方教育费附加',
        'total_tax': '预提税金',
    }

    @classmethod
    def init_from(cls, dva):
        from sheets.flowing.DailyValueAddedFlow import DailyValueAddedFlowing
        assert isinstance(dva, DailyValueAddedFlowing)
        floating = (dva.closing_price - dva.weighted_cost) * dva.holding_volume
        return cls(
            product=dva.product, institution=dva.institution, date=dva.date,
            account_code=dva.account_code, account_name=dva.account_name,
            security_code=dva.security_code, security_name=dva.security_name, holding_volume=dva.holding_volume,
            tax_cost=dva.weighted_cost, closing_price=dva.closing_price, assets_value=dva.market_value,
            floating=floating, vat=floating * TAX_RATE_VAT / (1 + TAX_RATE_VAT),
        )
