# -*- encoding: UTF-8 -*-
from sheets.Elements import AccountClass, BaseInfo
from utils.Constants import *

from jetend.DataCheck import *


class JournalEntry(AccountClass, BaseInfo):
    """
    录入凭证
    银行存款 - 机构 - 存款性质
    结算备付金 - 账户性质 - 机构
    存出保证金 - 账户性质 - 机构
    股票投资 - 成本/增值 - 机构 - 标的
    债券投资 - 成本/增值 - 机构 - 标的
    基金投资 - 成本/增值 - 机构 - 标的
    权证投资 - 成本/增值 - 机构 - 标的
    收益互换 - 成本/增值 - 机构
    应收股利 - 机构 - 标的
    应收利息 - 利息性质 - 机构 - 标的
    应收申购款 - 对方
    短期借款 - 借款原因 - 机构
    其他应收款 - 收款原因 - 对方
    应付赎回款 - 对方
    应付管理人报酬 - 报酬类别
    应交税费 - 税费类别 - 交税原因 - 标的
    应付利息 - 付息原因 - 对方
    其他应付款 - 付款原因 - 对方
    证券清算款 - 清算原因 - 机构 - 标的
    实收基金
    损益平准金 - 实现情况
    利息收入 - 利息收入原因 - 机构 - 标的
    公允价值变动损益 - 机构 - 标的
    投资收益 - 投资种类 - 机构 - 标的
    管理人报酬 - 报酬类别
    交易费用 - 机构 - 标的
    利息支出 - 利息支出原因 - 机构 - 标的
    其他费用 - 缴费原因 - 机构
    所得税费用 - 交税原因 - 机构 - 标的
    税金及附加 - 税费类别 - 交税原因 - 标的
    """
    inner2outer_map = {
        'entry_no': '凭证号', 'product': '产品', 'date': '日期', 'abstract': '摘要',
        'account_code': '科目编码', 'account_name': '科目名称',
        'account_level_2': '二级科目', 'account_level_3': '三级科目',
        'account_level_4': '四级科目', 'account_level_5': '五级科目',
        'debit_credit': '借贷', 'amount': '金额', 'buy_sell': '买卖', 'volume': '数量',
    }
    __id_count__ = 0

    @property
    def entry_no(self):
        """凭证号"""
        entry_no = str_check(self.get_attr('entry_no'))
        if not is_valid_str(entry_no):
            JournalEntry.__id_count__ = JournalEntry.__id_count__ + 1
            entry_no = '{}-{}-{}'.format(self.date.strftime('%Y%m%d'), self.product, JournalEntry.__id_count__)
            self.set_attr('entry_no', entry_no)
        assert is_valid_str(entry_no), str(self.__dict__)
        return entry_no

    @property
    def institution(self):
        raise RuntimeError('凭证没有institution属性')

    @property
    def abstract(self):
        abstract = str_check(self.get_attr('abstract'))
        assert is_valid_str(abstract), '凭证缺失摘要信息 {}'.format(self.__dict__)
        return abstract

    def update(
            self, abstract='', account_name='', account_level_2='', account_level_3='',
            account_level_4='', account_level_5='', debit_credit='', amount=None,
            buy_sell: str = '', volume: float = None,
    ):
        if is_valid_str(abstract):
            self.set_attr('abstract', str_check(abstract))
        else:
            pass
        self.set_attr('account_name', str_check(account_name))
        self.set_attr('account_level_2', str_check(account_level_2))
        self.set_attr('account_level_3', str_check(account_level_3))
        self.set_attr('account_level_4', str_check(account_level_4))
        self.set_attr('account_level_5', str_check(account_level_5))
        self.set_attr('debit_credit', str_check(debit_credit))
        self.set_attr('amount', float_check(amount))
        self.set_attr('buy_sell', str_check(buy_sell))
        self.set_attr('volume', str_check(volume))
        return self

    @property
    def debit_credit(self):
        debit_credit = str_check(self.get_attr('debit_credit'))
        assert is_valid_str(debit_credit), '凭证缺失借贷方向 {}'.format(self.__dict__)
        assert debit_credit in (SIDE_CREDIT_CN, SIDE_DEBIT_CN), str(self.__dict__)
        return debit_credit

    @property
    def amount(self):
        amount = float_check(self.get_attr('amount'))
        assert is_valid_float(amount), '凭证缺失金额信息 {}'.format(self.__dict__)
        return round(amount, 4)

    @property
    def buy_sell(self):
        buy_sell = str_check(self.get_attr('buy_sell'))
        assert buy_sell in (DIRECTION_BUY, DIRECTION_SELL, EMPTY_STRING), str(self.__dict__)
        return buy_sell

    @property
    def volume(self):
        return round(float_check(self.get_attr('volume')), 2)

    @property
    def account_name(self):
        account_name = str_check(self.get_attr('account_name'))
        assert is_valid_str(account_name), str(self.__dict__)
        return account_name

    @property
    def account_level_2(self):
        account_level_2 = str_check(self.get_attr('account_level_2'))
        if self.account_name not in ACCOUNT_NAME_LEVEL_ONE:
            assert is_valid_str(account_level_2), str(self.__dict__)
        else:
            assert not is_valid_str(account_level_2), '该凭证二级科目必须为空 {}'.format(self.__dict__)
        return account_level_2

    @property
    def account_level_3(self):
        account_level_3 = str_check(self.get_attr('account_level_3'))
        if self.account_name in ACCOUNT_NAME_LEVEL_THREE or self.account_name in ACCOUNT_NAME_LEVEL_FOUR:
            assert is_valid_str(account_level_3), str(self.__dict__)
        else:
            assert not is_valid_str(account_level_3), '该凭证三级科目必须为空 {}'.format(self.__dict__)
        return account_level_3

    @property
    def account_level_4(self):
        account_level_4 = str_check(self.get_attr('account_level_4'))
        if self.account_name in ACCOUNT_NAME_LEVEL_FOUR:
            assert is_valid_str(account_level_4), str(self.__dict__)
        else:
            assert not is_valid_str(account_level_4), '该凭证四级科目必须为空 {}'.format(self.__dict__)
        return account_level_4

    def force_match(self):
        self.set_attr('force_match', True)
        return self

    @property
    def is_force_match(self):
        try:
            return self.get_attr('force_match')
        except AttributeError:
            return False
