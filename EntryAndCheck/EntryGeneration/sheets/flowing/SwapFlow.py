# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import Flowing
from sheets.entry.Account import EntryAccount
from sheets.entry.Position import EntryPosition
from structures.Event import EventType
from utils.Constants import *


class SwapFlow(Flowing):
    inner2outer_map = {
        'product': 'product', 'date': 'date', 'institution': 'institution', 'amount': 'amount',
        'trade_class': 'trade_class',
    }

    def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
                 trade_class: str = '', amount: float = None,
                 ):
        Flowing.__init__(self, product=product, institution=institution, date=date)
        self.amount = float_check(amount)
        self.trade_class = str_check(trade_class)

    def generate_journal_entry(self):
        new_journal_entry_list = list()
        tag = self.trade_class.strip()

        if abs(self.amount) < 0.01:
            return list()

        if tag == '备付金变动':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='收益互换浮盈', account_name='结算备付金', account_level_2=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.amount),
                self.__ggje__().update(
                    abstract='收益互换浮盈', account_name='投资收益', account_level_2='收益互换',
                    account_level_3=self.institution, debit_credit=SIDE_CREDIT_CN, amount=self.amount),
            ])
            raise NotImplementedError(self)
        elif tag == '利息支付':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='收益互换利息支付', account_name='应付利息', account_level_2=self.institution,
                    account_level_3='短期借款',
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount)),
                self.__ggje__().update(
                    abstract='收益互换利息支付', account_name='结算备付金', account_level_2=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount)),
            ])
            raise NotImplementedError(self)
        elif tag == '收益互换估值增值':
            # assert self.institution in ('中信美股', '中信港股', ), str(self)
            if self.institution in ('中信美股', '中信港股',):
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract=tag, account_name='收益互换', account_level_2='估值增值', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=self.amount),
                    # self.__ggje__().update(
                    #     abstract=tag, account_name='收益互换', account_level_2='成本', account_level_3=self.institution,
                    #     debit_credit=SIDE_CREDIT_CN, amount=self.amount),
                    self.__ggje__().update(
                        abstract=tag, account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                        account_level_4='中信互换', debit_credit=SIDE_CREDIT_CN, amount=self.amount),
                ])
            else:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract=tag, account_name='收益互换', account_level_2='估值增值', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=self.amount),
                    self.__ggje__().update(
                        abstract=tag, account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                        account_level_4=self.institution, debit_credit=SIDE_CREDIT_CN, amount=self.amount),
                ])

        else:
            raise NotImplementedError(tag)
        return new_journal_entry_list


class ModifyFlowing(Flowing):
    """调整流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'trade_class': '类型',
        'trade_amount': '发生金额', 'opposite': '对方', 'subject': '标的',
    }

    def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
                 trade_amount: float = None, trade_class: str = '', opposite: str = '', subject: str = ''):
        Flowing.__init__(self, product=product, institution=institution,
                         date=date)
        self.trade_amount = float_check(trade_amount)
        self.trade_class = str_check(trade_class)
        self.opposite, self.subject = str_check(opposite), str_check(subject)

    def generate_journal_entry(self):
        new_journal_entry_list = list()
        tag = self.trade_class.strip()

        if tag == '股票托管转出':
            # 转出成本和估值增值
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='股票投资', sub_account='成本', base_account=self.opposite,
                    note_account=self.subject,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3='待转收',
                        account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                        amount=acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3=self.opposite,
                        account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                        amount=acc.realtime_net_value),
                ])
            except ValueError:
                raise RuntimeError('未知成本 {} .'.format(str(self)))
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='股票投资', sub_account='估值增值', base_account=self.opposite,
                    note_account=self.subject,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='估值增值', account_level_3='待转收',
                        account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                        amount=acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='估值增值', account_level_3=self.opposite,
                        account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                        amount=acc.realtime_net_value),
                ])
            except ValueError:
                raise RuntimeError('未知估值增值 {} .'.format(str(self)))
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='公允价值变动损益', sub_account=self.opposite,
                    base_account=self.subject,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='公允价值变动损益', account_level_2='待转收', account_level_3=self.subject,
                        debit_credit=SIDE_DEBIT_CN, amount=acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='公允价值变动损益', account_level_2=self.opposite, account_level_3=self.subject,
                        debit_credit=SIDE_CREDIT_CN, amount=acc.realtime_net_value),
                ])
            except ValueError:
                raise RuntimeError('未知变动损益 {} .'.format(str(self)))

            try:
                pos = self.env.entry_gen.positions.find_value(
                    product=self.product, institution=self.institution, security_name=self.subject,
                )
                assert isinstance(pos, EntryPosition)
                pos.institution = '待转收'
            except ValueError:
                raise RuntimeError('未知持仓 {}'.format(self))
        elif tag == '调整成本转移':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='股票投资', account_level_2='成本',
                    account_level_3=self.institution, account_level_4='宁波银行',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='股票投资',
                    account_level_2='成本', account_level_3=self.institution, account_level_4='宁行A1配',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),

            ])
        elif tag == '成本转移后估值增值调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='公允价值变动损益', account_level_2=self.institution,
                    account_level_3='宁波银行', debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='股票投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4='宁波银行', debit_credit=SIDE_CREDIT_CN,
                    amount=self.trade_amount)
            ])
        elif tag == '股票托管转入':
            # 转出成本和估值增值
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='股票投资', sub_account='成本', base_account='待转收',
                    note_account=self.subject,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3='待转收',
                        account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                        amount=acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3=self.opposite,
                        account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                        amount=acc.realtime_net_value),
                ])
            except ValueError:
                raise RuntimeError('未知成本 {} .'.format(str(self)))
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='股票投资', sub_account='估值增值', base_account='待转收',
                    note_account=self.subject,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='估值增值', account_level_3='待转收',
                        account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                        amount=acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='估值增值', account_level_3=self.opposite,
                        account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                        amount=acc.realtime_net_value),
                ])
            except ValueError:
                raise RuntimeError('未知估值增值 {} .'.format(str(self)))
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='公允价值变动损益', sub_account='待转收',
                    base_account=self.subject,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='公允价值变动损益', account_level_2='待转收', account_level_3=self.subject,
                        debit_credit=SIDE_CREDIT_CN, amount=acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='公允价值变动损益', account_level_2=self.opposite, account_level_3=self.subject,
                        debit_credit=SIDE_DEBIT_CN, amount=acc.realtime_net_value),
                ])
            except ValueError:
                raise RuntimeError('未知变动损益 {} .'.format(str(self)))

            try:
                pos = self.env.entry_gen.positions.find_value(
                    product=self.product, institution='待转收', security_name=self.subject,
                )
                assert isinstance(pos, EntryPosition)
                pos.institution = self.opposite
            except ValueError:
                raise RuntimeError('未知持仓 {}'.format(self))
        elif tag == '收益互换账户转账':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='收益互换', account_level_2='成本', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='收益互换', account_level_2='成本', account_level_3=self.opposite,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '收益互换估值调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='收益互换', account_level_2='估值增值', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                    account_level_4=self.opposite, debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '补充计提融资利息':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='应付利息', account_level_2='短期借款利息',
                    account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='利息支出', account_level_2='借款利息支出',
                    account_level_3=self.institution, account_level_4='借款',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '银行费用补计':
            assert self.trade_amount > 0, self
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag,
                    account_name='其他费用', account_level_2='手续费', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag,
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])

        elif tag == '银行余额调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag,
                    account_name='其他费用', account_level_2='手续费', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag,
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])

        elif tag == '银行活期利息调整':
            # assert self.trade_amount > 0, self
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag,
                    account_name='应收利息', account_level_2='银行存款利息', account_level_3=self.institution,
                    account_level_4='活期存款',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag,
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '港股通交收资金差异补记':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag,
                    account_name='存出保证金', account_level_2=self.opposite, account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount).force_match(),
                self.__ggje__().update(
                    abstract=tag,
                    account_name='交易费用', account_level_2=self.institution, account_level_3=self.subject,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        # elif tag == '短期借款误差调整':
        #     new_journal_entry_list.extend([
        #         self.__ggje__().update(
        #             abstract=tag, account_name='应付利息', account_level_2='短期借款利息',
        #             account_level_3=self.institution,
        #             debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
        #         self.__ggje__().update(
        #             abstract=tag, account_name='利息支出', account_level_2='借款利息支出',
        #             account_level_3=self.institution, account_level_4='借款',
        #             debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
        #     ])
        # elif tag == '应付利息计提误差调整':
        #     new_journal_entry_list.extend([
        #         self.__ggje__().update(
        #             abstract=tag, account_name='应付利息', account_level_2=self.opposite,
        #             account_level_3=self.institution,
        #             debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
        #         self.__ggje__().update(
        #             abstract=tag, account_name='利息支出', account_level_2='借款利息支出',
        #             account_level_3=self.institution, account_level_4='借款',
        #             debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
        #     ])
        elif tag == '存出保证金利息计提误差调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='应收利息', account_level_2='存出保证金利息',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='利息收入', account_level_2='存款利息收入',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '存出保证金利息结算误差调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='存出保证金', account_level_2=self.opposite,
                    account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='利息收入', account_level_2='存款利息收入',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '存出保证金利息结算':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='存出保证金', account_level_2=self.opposite,
                    account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='应收利息', account_level_2='存出保证金利息',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        # 修正某些券商港股因T+2日交收造成的费用遗漏
        elif tag == '港股交易费用遗漏补录':
            assert self.trade_amount >= 0.0, self
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, account_level_3='遗漏补录',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='存出保证金', account_level_2=self.opposite,
                    account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        # 修正某些券商港股交易资金冻结交收时看不到修正流水
        elif tag == '港股交易资金冻结转回':
            assert self.trade_amount >= 0.0, self
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='存出保证金', account_level_2=self.opposite,
                    account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, account_level_3='超额冻结转回',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '应付管理费计提误差修正':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract='应付管理费计提误差修正', account_name='应付管理人报酬', account_level_2='固定管理费',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract='应付管理费计提误差修正', account_name='管理人报酬', account_level_2='固定管理费',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '存出保证金费用误差调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='存出保证金', account_level_2=self.opposite,
                    account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='交易费用', account_level_2=self.institution,
                    account_level_3='调整误差',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '结算备付金费用误差调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='结算备付金', account_level_2=self.opposite,
                    account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='交易费用', account_level_2=self.institution,
                    account_level_3='调整误差',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '中信收益互换平仓估值增值调整':
            if self.trade_amount > 0:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract=tag, account_name='收益互换', account_level_2='估值增值',
                        account_level_3=self.institution, debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                    # self.__ggje__().update(
                    #     abstract=tag, account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                    #     account_level_4='中信互换', debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                    self.__ggje__().update(
                        abstract=tag, account_name='收益互换', account_level_2='成本', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                ])
            else:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract=tag, account_name='收益互换', account_level_2='成本', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                    self.__ggje__().update(
                        abstract=tag, account_name='收益互换', account_level_2='估值增值',
                        account_level_3=self.institution, debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
                ])
                # new_journal_entry_list.extend([
                #     self.__ggje__().update(
                #         abstract=tag, account_name='收益互换', account_level_2='估值增值', account_level_3=self.institution,
                #         debit_credit=SIDE_DEBIT_CN, amount=self.amount),
                #     self.__ggje__().update(
                #         abstract=tag, account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                #         account_level_4='中信美股', debit_credit=SIDE_CREDIT_CN, amount=self.amount),
                # ])
        elif tag == '收益互换估值增值调整':
            # assert self.institution in ('中信美股', '中信港股', ), str(self)
            if self.institution in ('中信美股', '中信港股',):
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract=tag, account_name='收益互换', account_level_2='成本', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                    # self.__ggje__().update(
                    #     abstract=tag, account_name='收益互换', account_level_2='成本', account_level_3=self.institution,
                    #     debit_credit=SIDE_CREDIT_CN, amount=self.amount),
                    self.__ggje__().update(
                        abstract=tag, account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                        account_level_4=self.institution, debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                ])
            else:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract=tag, account_name='收益互换', account_level_2='估值增值', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=self.amount),
                    self.__ggje__().update(
                        abstract=tag, account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                        account_level_4=self.institution, debit_credit=SIDE_CREDIT_CN, amount=self.amount),
                ])
        elif tag == '递延税费调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='其他应付款', account_level_2='递延税费', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='其他费用', account_level_2='递延税费', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '增值税调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2='增值税', account_level_3='价差收入',
                    account_level_4='应税标的',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='投资收益', account_level_2='股利收益', account_level_3='调整项',
                    account_level_4='调整项',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '美港收益互换估值成本调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='收益互换', account_level_2='成本', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='收益互换', account_level_2='估值增值', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '中信美股收益互换估值增值调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='收益互换', account_level_2='估值增值',
                    account_level_3=self.institution, debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                # self.__ggje__().update(
                #     abstract=tag, account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                #     account_level_4='中信互换', debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='投资收益', account_level_2='股利收益', account_level_3='调整项',
                    account_level_4='调整项',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '中信港股收益互换估值增值调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='收益互换', account_level_2='估值增值',
                    account_level_3=self.institution, debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                # self.__ggje__().update(
                #     abstract=tag, account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                #     account_level_4='中信互换', debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='投资收益', account_level_2='股利收益', account_level_3='调整项',
                    account_level_4='调整项',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '华泰收益互换估值增值调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='收益互换', account_level_2='估值增值',
                    account_level_3=self.institution, debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                # self.__ggje__().update(
                #     abstract=tag, account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                #     account_level_4='中信互换', debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='投资收益', account_level_2='股利收益', account_level_3='调整项',
                    account_level_4='调整项',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])

        elif tag == '华泰收益互换估值成本调整':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='收益互换', account_level_2='估值增值', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='收益互换', account_level_2='成本', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '调整股票投资估值增值尾差':  # 原因：两种估值方法得出的资产总值不等，2022年5月23日wavezhou,hemengjie调整
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='投资收益', account_level_2='股票投资收益',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                    amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='股票投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                    amount=self.trade_amount)
            ])
        elif tag == '对冲股票投资成本与估值增值':  # 原因：两种估值方法得出的资产总值不等，2022年5月23日wavezhou,hemengjie调整
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='股票投资', account_level_2='成本',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                    amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='股票投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                    amount=self.trade_amount)
            ])
        # 调整股票投资成本尾差
        elif tag == '调整股票投资成本尾差':  # 原因：两种估值方法得出的资产总值不等，2022年5月23日wavezhou,hemengjie调整
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='投资收益', account_level_2='股票投资收益',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                    amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='股票投资', account_level_2='成本',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                    amount=self.trade_amount)
            ])
        # 调整基金投资估值增值尾差
        elif tag == '调整基金投资估值增值尾差':  # 原因：两种估值方法得出的资产总值不等，2022年5月23日wavezhou,hemengjie调整
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='投资收益', account_level_2='基金投资收益',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                    amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='基金投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                    amount=self.trade_amount)
            ])
        # 调整基金投资成本尾差
        elif tag == '调整基金投资成本尾差':  # 原因：两种估值方法得出的资产总值不等，2022年5月23日wavezhou,hemengjie调整
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='投资收益', account_level_2='基金投资收益',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                    amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='基金投资', account_level_2='成本',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                    amount=self.trade_amount)
            ])
        # 对冲基金投资成本与估值增值
        elif tag == '对冲基金投资成本与估值增值':  # 原因：两种估值方法得出的资产总值不等，2022年5月23日wavezhou,hemengjie调整
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='基金投资', account_level_2='成本',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_DEBIT_CN,
                    amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='基金投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4=self.subject, debit_credit=SIDE_CREDIT_CN,
                    amount=self.trade_amount)
            ])
        # 调整预提增值税
        elif tag == '调整预提增值税':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='预提费用', account_level_2='预提增值税', account_level_3='增值税',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='其他费用', account_level_2='费用误差', account_level_3='增值税',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        # 调整预提附加税
        elif tag == '调整预提附加税':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='预提费用', account_level_2='预提附加税', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='其他费用', account_level_2='费用误差', account_level_3='附加税',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        # 调整应交税费 - 增值税#应交税费明细科目对冲
        elif tag == '应交税费明细科目对冲':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2=self.institution, account_level_3='价差收入',
                    account_level_4='应税标的',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2=self.institution, account_level_3='税费支出',
                    account_level_4='已交税费',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        # 调整应交税费增值税
        elif tag == '调整应交税费增值税':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2=self.institution, account_level_3=self.opposite,
                    account_level_4=self.subject,debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='其他费用', account_level_2='费用误差', account_level_3='附加税',
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])

        else:
            raise NotImplementedError(self)
        return new_journal_entry_list

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.date, abstract=self.trade_class.strip(),
            account_level_5=self.trade_class.strip(),
        )
