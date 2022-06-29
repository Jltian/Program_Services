# -*- encoding: UTF-8 -*-

from sheets.Elements import AccountClass, BaseInfo, SecurityInfo
from utils.Constants import *

from jetend.DataCheck import *


class DailyValueAddedFlowing(AccountClass, BaseInfo, SecurityInfo):
    """估值增值"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'account_code': '科目编号', 'account_name': '科目名称', 'security_code': '标的代码', 'security_name': '标的名称',
        'holding_volume': '持有数量', 'weighted_cost': '加权成本', 'tax_cost': '计税成本',
        'closing_price': '收盘价', 'market_value': '市值',
        'lastday_weighted_cost': '前一日加权成本', 'lastday_total_cost': '前一日成本',
        'lastday_holding_volume': '前一日持有数量',
        'lastday_closing_price': '前一日收盘价', 'lastday_market_value': '前一日市值',
    }

    # def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
    #              account_code: int = None,
    #              security_code: str = '', security_name: str = '', holding_volume: float = None,
    #              weighted_cost: float = None, tax_cost: float = None,
    #              closing_price: float = None, market_value: float = None,
    #              lastday_weighted_cost: float = None, lastday_holding_volume: float = None,
    #              lastday_closing_price: float = None, lastday_market_value: float = None,
    #              ):
    #     AccountClass.__init__(self, account_code=account_code)
    #     Contract.__init__(self, security_code=security_code, security_name=security_name)
    #     Flowing.__init__(self, product=product, institution=institution, date=date)
    #
    #     self.holding_volume = float_check(holding_volume)
    #     self.weighted_cost = float_check(weighted_cost)
    #     self.tax_cost = float_check(tax_cost)
    #     self.closing_price = float_check(closing_price)
    #     self.market_value = float_check(market_value)
    #
    #     self.lastday_weighted_cost = float_check(lastday_weighted_cost)
    #     self.lastday_holding_volume = float_check(lastday_holding_volume)
    #     self.lastday_closing_price = float_check(lastday_closing_price)
    #     self.lastday_market_value = float_check(lastday_market_value)

    @property
    def holding_volume(self):
        holding_volume = float_check(self.get_attr('holding_volume'))
        assert is_valid_float(holding_volume), str(self.__dict__)
        assert holding_volume >= 0, str(self.__dict__)
        return holding_volume

    @property
    def weighted_cost(self):
        weighted_cost = safe_division(self.total_cost, self.holding_volume)
        # weighted_cost = float_check(self.get_attr('weighted_cost'))
        assert is_valid_float(weighted_cost), str(self.__dict__)
        assert weighted_cost >= 0, str(self.__dict__)
        return weighted_cost

    @property
    def closing_price(self):
        closing_price = float_check(self.get_attr('closing_price'))
        assert is_valid_float(closing_price), str(self.__dict__)
        return closing_price

    @property
    def market_value(self):
        market_value = float_check(self.get_attr('market_value'))
        assert is_valid_float(market_value), str(self.__dict__)
        return market_value

    @property
    def total_cost(self):
        total_cost = float_check(self.get_attr('total_cost'))
        # return self.weighted_cost * self.holding_volume
        assert is_valid_float(total_cost), str(self.__dict__)
        assert total_cost > - 0.01, str(self.__dict__)
        return total_cost

    @property
    def lastday_holding_volume(self):
        lastday_holding_volume = float_check(self.get_attr('lastday_holding_volume'))
        assert is_valid_float(lastday_holding_volume), str(self.__dict__)
        assert lastday_holding_volume >= 0, str(self.__dict__)
        return lastday_holding_volume

    @property
    def lastday_total_cost(self):
        lastday_total_cost = float_check(self.get_attr('lastday_total_cost'))
        assert is_valid_float(lastday_total_cost), str(self.__dict__)
        return lastday_total_cost

    @property
    def lastday_weighted_cost(self):
        lastday_weighted_cost = safe_division(self.lastday_total_cost, self.lastday_holding_volume)
        # lastday_weighted_cost = float_check(self.get_attr('lastday_weighted_cost'))
        assert is_valid_float(lastday_weighted_cost), str(self.__dict__)
        assert lastday_weighted_cost >= 0, str(self.__dict__)
        return lastday_weighted_cost

    @property
    def lastday_market_value(self):
        lastday_market_value = float_check(self.get_attr('lastday_market_value'))
        assert is_valid_float(lastday_market_value), str(self.__dict__)
        return lastday_market_value

    @classmethod
    def init_from(cls, pos):
        from sheets.entry.Position import EntryPosition
        assert isinstance(pos, EntryPosition)
        try:
            return cls(
                date=pos.date, product=pos.product, institution=pos.institution, account_name=pos.account_name,
                security_name=pos.security_name, security_code=pos.security_code,
                holding_volume=pos.hold_volume, total_cost=pos.total_cost,
                closing_price=pos.close_price, market_value=pos.market_value,
                lastday_holding_volume=pos.last_hold_volume, lastday_total_cost=pos.lastday_total_cost,
                lastday_closing_price=pos.last_close_price, lastday_market_value=pos.last_market_value,
            )
        except KeyError as k_r:
            print(pos.product, pos.security_code, pos.security_name)
            raise k_r

    def generate_journal_entry(self):
        new_journal_entry_list = list()
        if not is_valid_float(self.lastday_closing_price) and not is_valid_float(self.lastday_holding_volume):
            value_add = (self.closing_price - self.weighted_cost) * self.holding_volume
        else:
            if self.holding_volume > self.lastday_holding_volume:
                # 今天的价值增值 - 昨天的价值增值
                # value_add = (self.closing_price - self.lastday_closing_price) * self.lastday_holding_volume \
                #             + (self.holding_volume - self.lastday_holding_volume) * self.closing_price \
                #             - (self.holding_volume * self.weighted_cost
                #                - self.lastday_holding_volume * self.lastday_weighted_cost)
                # value_add = self.holding_volume * (self.closing_price - self.weighted_cost) + (
                #     self.lastday_weighted_cost - self.lastday_closing_price) * self.lastday_holding_volume
                value_add = self.market_value - self.total_cost + self.lastday_total_cost - self.lastday_market_value
            else:
                if abs(self.holding_volume) < 0.01:
                    value_add = 0
                else:
                    value_add = (self.closing_price - self.lastday_closing_price) * self.holding_volume

        assert is_valid_float(value_add), str(self)
        if abs(round(value_add, 2)) < 0.01:
            return list()

        if self.account_code == 1102:
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='股票估值增值', account_name='股票投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=value_add),
                self.__ggje__().update(
                    abstract='股票估值增值', account_name='公允价值变动损益', account_level_2=self.institution,
                    account_level_3=self.security_name, debit_credit=SIDE_CREDIT_CN, amount=value_add),
            ])
        elif self.account_code == 1103:
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='债券估值增值', account_name='债券投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=value_add),
                self.__ggje__().update(
                    abstract='债券估值增值', account_name='公允价值变动损益', account_level_2=self.institution,
                    account_level_3=self.security_name, debit_credit=SIDE_CREDIT_CN, amount=value_add),
            ])
        elif self.account_code == 1105:
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='基金估值增值', account_name='基金投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=value_add),
                self.__ggje__().update(
                    abstract='基金估值增值', account_name='公允价值变动损益', account_level_2=self.institution,
                    account_level_3=self.security_name, debit_credit=SIDE_CREDIT_CN, amount=value_add),
            ])
        elif self.account_code == 1106:
            if '期权' in self.institution:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract='期权估值增值', account_name='权证投资', account_level_2='估值增值',
                        account_level_3=self.institution, account_level_4=self.security_code,
                        debit_credit=SIDE_DEBIT_CN, amount=value_add),
                    self.__ggje__().update(
                        abstract='期权估值增值', account_name='公允价值变动损益', account_level_2=self.institution,
                        account_level_3=self.security_code, debit_credit=SIDE_CREDIT_CN, amount=value_add),
                ])
            elif '期货' in self.institution:
                # new_journal_entry_list.extend([
                #     self.__ggje__().update(
                #         abstract='期货估值增值', account_name='存出保证金', account_level_2='期货账户',
                #         account_level_3=self.institution, debit_credit=SIDE_DEBIT_CN, amount=value_add * rate),
                #     self.__ggje__().update(
                #         abstract='期货估值增值', account_name='结算备付金', account_level_2='期货账户',
                #         account_level_3=self.institution, debit_credit=SIDE_DEBIT_CN, amount=value_add * (1 - rate)),
                #     self.__ggje__().update(
                #         abstract='期货估值增值', account_name='投资收益', account_level_2='衍生投资收益',
                #         account_level_3=self.institution, account_level_4=self.security_code,
                #         debit_credit=SIDE_CREDIT_CN, amount=value_add)
                # ])
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract='期货估值增值', account_name='权证投资', account_level_2='估值增值',
                        account_level_3=self.institution, account_level_4=self.security_code,
                        debit_credit=SIDE_DEBIT_CN, amount=value_add),
                    self.__ggje__().update(
                        abstract='期货估值增值', account_name='公允价值变动损益', account_level_2=self.institution,
                        account_level_3=self.security_code, debit_credit=SIDE_CREDIT_CN, amount=value_add),
                    ])
            else:
                raise NotImplementedError(self.institution)
        else:
            raise NotImplementedError(self.account_code)
        return new_journal_entry_list

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.date, account_level_5=self.security_code_name,
        )

    def future_leverage_ratio(self):
        raise NotImplementedError(self)
        # sql = """SELECT `买持`, `结算价`, `保证金占用` FROM `原始期货持仓记录`
        # WHERE `日期` = '{}' and `产品` = '{}' and `期货合约` = '{}';""".format(
        #     self.date, self.product, self.security_code)
        # sql = """SELECT * FROM `原始期货持仓记录`
        #         WHERE `日期` >= '{}' and `产品` = '{}' and `期货合约` = '{}';""".format(
        #     self.date, self.product, self.security_code)
        # pd_data = self.env.data_base.read_pd_query(DataBaseName.management, sql)
        # try:
        #     leverage_ratio = pd_data.loc[0, '保证金占用'] / (
        #             pd_data.loc[0, '买持'] * pd_data.loc[0, '结算价']
        #             * self.env.market_board.contract_multiplier(SECURITY_TYPE_OPTION, self.security_code, self.date)
        #     )
        # except KeyError as f_k_error:
        #     print(pd_data)
        #     print(sql)
        #     print(self)
        #     raise f_k_error
        #
        # return leverage_ratio
