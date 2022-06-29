# -*- encoding: UTF-8 -*-
import re

from sheets.Elements import BaseInfo, EntryGenerable
from utils.Constants import *


class BankFlowing(BaseInfo, EntryGenerable):
    """银行标准流水"""
    inner2outer_map = {
         'product': '产品', 'date': '日期', 'institution': '银行', 'trade_class': '类型',
         'opposite': '对方', 'subject': '标的', 'trade_amount': '发生金额', 'comment': '备注',
         'tag_program': '程序化标识',
    }

    @property
    def opposite(self):
        opposite = self.get_attr('opposite')
        if '美股' in opposite and opposite != '中信美股':
            opposite = '中信美股'
        if '港股' in opposite and opposite != '中信港股':
            opposite = '中信港股'
        if opposite in ('华泰收益互换', ):
            opposite = '华泰互换'
        if opposite in ('港股收益互换', '美股收益互换'):
        # if '收益互换' in opposite:
            raise RuntimeError(self.__dict__)
        if '信用' in opposite:
            opposite = opposite.replace('信用', '两融')
        assert isinstance(opposite, str), str(self.__dict__)
        return opposite

    @property
    def trade_amount(self):
        trade_amount = float_check(self.get_attr('trade_amount'))
        assert is_valid_float(trade_amount), str(self.__dict__)
        return trade_amount

    def generate_journal_entry(self):
        from structures import EventType
        from sheets.entry.Account import EntryAccount
        from sheets.flowing.VATPaid import VATPaid
        new_journal_entry_list = list()
        tag = self.trade_class.strip()

        if tag == '申购':             # 自有基金被申购
            assert self.trade_amount > 0, str(self)     # 申购款必定大于零
            # TODO: 申购申请  +应收申购款-其他应付款 -> 收到申购款 +银行存款-应收申购款 -> 申购确认 +其他应付款-基金
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='其他应付款', account_level_2='未确认申购款', account_level_3=self.opposite,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag in ('银证转账', '银行转账'):
            if '中信美股' in self.opposite or '中信港股' in self.opposite or '华泰互换' in self.opposite:
                if self.trade_amount < 0:
                    new_journal_entry_list.extend([
                        self.__ggje__().update(
                            account_name='收益互换', account_level_2='成本', account_level_3=self.opposite,
                            debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                        self.__ggje__().update(
                            account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                            debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
                    ])
                elif self.trade_amount > 0:
                    new_journal_entry_list.extend([
                        self.__ggje__().update(
                            account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                            debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                        self.__ggje__().update(
                            account_name='收益互换', account_level_2='成本', account_level_3=self.opposite,
                            debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                        # self.__ggje__().update(
                        #     account_name='收益互换', account_level_2='估值增值', account_level_3=self.opposite,
                        #     debit_credit=SIDE_CREDIT_CN, amount=0),
                        # self.__ggje__().update(
                        #     account_name='投资收益', account_level_2='衍生工具收益', account_level_3='收益互换',
                        #     account_level_4=self.opposite, debit_credit=SIDE_CREDIT_CN, amount=0),
                    ])
                else:
                    raise NotImplementedError(self)
            elif '期货' in self.opposite:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                        debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                    self.__ggje__().update(
                        account_name='结算备付金', account_level_2='期货账户', account_level_3=self.opposite,
                        debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                ])
            else:
                if '两融' in self.opposite:
                    account_level_2 = '信用账户'
                elif '期权' in self.opposite:
                    account_level_2 = '期权账户'
                else:
                    account_level_2 = '普通账户'
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                        debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2=account_level_2, account_level_3=self.opposite,
                        debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                ])
        elif tag == '基金投资':
            if self.trade_amount > 0:
                try:
                    acc = self.env.entry_gen.accounts.find_value(
                        product=self.product, account_name='其他应收款', sub_account='基金赎回款',
                        base_account=self.subject,
                    )
                    assert isinstance(acc, EntryAccount)
                except ValueError:
                    from structures import DataList
                    acc_list = self.env.entry_gen.accounts.find_value_where(
                        product=self.product, account_name='其他应收款', sub_account='基金赎回款',
                        # base_account=self.subject,
                    )
                    acc = None
                    # assert isinstance(acc_list, DataList)
                    for sub_acc in acc_list:
                        assert isinstance(sub_acc, EntryAccount)
                        if not is_valid_str(sub_acc.base_account):
                            continue
                        if sub_acc.base_account in self.subject or self.subject in sub_acc.base_account:
                            acc = sub_acc
                            break
                    if isinstance(acc, EntryAccount):
                        pass
                    else:
                        raise RuntimeError('未找到相关记录 {} \n {}'.format(self, str(
                            self.env.entry_gen.accounts.find_value_where(product=self.product, account_name='其他应收款',)
                        )))
                except KeyError:
                    raise RuntimeError(self)
                assert acc.base_account in self.subject or self.subject in acc.base_account, '{}\n{}'.format(acc, self)
                assert abs(acc.realtime_net_value / self.trade_amount) > 0.7, '{}\n{}'.format(self, acc)
                if self.opposite == '久铭':
                    # if abs(acc.start_net_value) > 10:
                    #     start_net_value = acc.start_net_value
                    # else:
                    #     start_net_value = acc.realtime_net_value
                    # new_journal_entry_list.extend([
                    #     self.__ggje__().update(
                    #         account_name='银行存款', account_level_2=self.institution, debit_credit=SIDE_DEBIT_CN,
                    #         amount=self.trade_amount),
                    #     self.__ggje__().update(
                    #         account_name='投资收益', account_level_2='基金投资收益',
                    #         account_level_3=self.institution, debit_credit=SIDE_DEBIT_CN,
                    #         amount=start_net_value - self.trade_amount),
                    #     self.__ggje__().update(
                    #         account_name='其他应收款', account_level_2=self.opposite, account_level_3=self.subject,
                    #         debit_credit=SIDE_CREDIT_CN, amount=start_net_value),
                    # ])
                    new_journal_entry_list.extend([
                        self.__ggje__().update(
                            account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                            debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                        self.__ggje__().update(
                            account_name='其他应收款', account_level_2='基金赎回款', account_level_3=self.subject,
                            debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                    ])
                else:
                    assert acc.start_net_value - self.trade_amount >= 0, '基金赎回费问题 {}\n{}'.format(self, acc)
                    new_journal_entry_list.extend([
                        self.__ggje__().update(
                            account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                            debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                        self.__ggje__().update(
                            account_name='交易费用', account_level_2=self.opposite, account_level_3=self.subject,
                            debit_credit=SIDE_DEBIT_CN, amount=acc.start_net_value - self.trade_amount),
                        self.__ggje__().update(
                            account_name='其他应收款', account_level_2='基金赎回款', account_level_3=self.subject,
                            debit_credit=SIDE_CREDIT_CN, amount=acc.start_net_value),
                    ])
            else:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                        debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount).force_match(),
                    self.__ggje__().update(
                        account_name='其他应收款', account_level_2='未确认基金投资款', account_level_3=self.subject,
                        debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                ])

        elif tag in ('网银汇款手续费', '印鉴变更手续费', '贷记凭证手续费', '补打手续费'):
            assert self.trade_amount < 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='其他费用', account_level_2='手续费', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            ])

        elif tag == '增值税及附加':
            assert self.trade_amount < 0, str(self)
            vat_amount = abs(self.trade_amount) / (1 + TAX_RATE_BT + TAX_RATE_ES + TAX_RATE_LES)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2='增值税', account_level_3='税费支出',
                    account_level_4='已交税费',
                    debit_credit=SIDE_DEBIT_CN, amount=vat_amount),
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2='增值税附加城建税', account_level_3='税费支出',
                    account_level_4='已交税费', debit_credit=SIDE_DEBIT_CN, amount=vat_amount * TAX_RATE_BT),
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2='增值税附加教育费', account_level_3='税费支出',
                    account_level_4='已交税费', debit_credit=SIDE_DEBIT_CN, amount=vat_amount * TAX_RATE_ES),
                self.__ggje__().update(
                    abstract=tag, account_name='应交税费', account_level_2='增值税附加地方教育费', account_level_3='税费支出',
                    account_level_4='已交税费',
                    debit_credit=SIDE_DEBIT_CN, amount=vat_amount * TAX_RATE_LES),
                self.__ggje__().update(
                    abstract=tag, account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            ])
            self.env.trigger_event(
                event_type=EventType.VATGen,
                data=VATPaid(
                    product=self.product, date=self.date, institution=self.institution, account_name='应交税费',
                    vat=vat_amount, building_tax=vat_amount * TAX_RATE_BT,
                    education_surcharge=vat_amount * TAX_RATE_ES,
                    local_education_surcharge=vat_amount * TAX_RATE_LES,
                    total_tax=abs(self.trade_amount),
                )
            )
        elif tag == '管理费返还':
            assert self.trade_amount > 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='其他应收款', account_level_2='管理费返还', account_level_3=self.subject,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '业绩报酬返还':
            assert self.trade_amount > 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='其他应收款', account_level_2='业绩报酬', account_level_3=self.subject,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
        elif tag == '利息归本':
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='应收利息', sub_account='银行存款利息', base_account=self.institution,
                )
                assert isinstance(acc, EntryAccount)
                interests = acc.net_value
            except ValueError:
                interests = 0.0

            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='利息收入', account_level_2='存款利息收入', account_level_3=self.institution,
                    account_level_4='活期存款', debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount - abs(interests)),
                self.__ggje__().update(
                    account_name='应收利息', account_level_2='银行存款利息', account_level_3=self.institution,
                    account_level_4='活期存款', debit_credit=SIDE_CREDIT_CN, amount=abs(interests)),
            ])
        # elif tag in ('募集户利息结转', '募集利息结转'):
        #     # try:
        #     #     acc = self.env.entry_gen.accounts.find_value(
        #     #         product=self.product, account='应收利息', sub_account='募集户',
        #     #     )
        #     #     assert isinstance(acc, EntryAccount), str(type(acc))
        #     #     interests = acc.start_net_value
        #     # except KeyError:
        #     #     raise RuntimeError('Sell {} while no holding.'.format(str(self)))
        #
        #     new_journal_entry_list.extend([
        #         self.__ggje__().update(account_name='银行存款', account_level_2=self.institution,
        #                                debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
        #         self.__ggje__().update(account_name='应收利息', account_level_2='募集户',
        #                                debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
        #     ])
        # elif tag == '募集转专用账户':
        #     new_journal_entry_list.extend([
        #         self.__ggje__().update(account_name='银行存款', account_level_2=self.institution,
        #                                debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
        #         self.__ggje__().update(account_name='银行存款', account_level_2=self.opposite,
        #                                debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
        #     ])
        elif tag in ('赎回', '赎回业绩报酬'):
            assert self.trade_amount < 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(account_name='应付赎回款', account_level_2=self.opposite,
                                       debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            ])
        elif tag == '基金现金分红':
            # 基金投资现金分红
            if self.trade_amount > 0:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                        debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                    self.__ggje__().update(
                        account_name='其他应收款', account_level_2='基金分红', account_level_3=self.subject,
                        debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                ])
            # 久铭基金分红
            else:
                new_journal_entry_list.extend([
                    self.__ggje__().update(account_name='损益平准金', account_level_2='已实现',
                                           debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                    self.__ggje__().update(
                        account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
                ])
        elif tag == '管理费':
            assert self.trade_amount < 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(account_name='应付管理人报酬', account_level_2='固定管理费',
                                       debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            ])
        elif tag == '基金投资撤销':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='其他应收款', account_level_2=self.opposite, account_level_3=self.subject,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
            raise NotImplementedError(self)
        elif tag == '基金转入':
            new_journal_entry_list.extend([
                self.__ggje__().update(abstract=tag, account_name='银行存款', account_level_2=self.institution,
                                       debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(abstract=tag, account_name='应收申购款',
                                       debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])  # 平安募集户 转 托管银行
            raise NotImplementedError(self)
        elif tag == '基金转出':
            new_journal_entry_list.extend([
                self.__ggje__().update(account_name='银行存款', account_level_2=self.institution,
                                       debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                self.__ggje__().update(account_name='应付赎回款', account_level_2=self.opposite,
                                       debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
            ])
            raise NotImplementedError(self)
        elif tag in ('业绩报酬', '基金转出业绩报酬'):
            assert self.trade_amount < 0, str(self.__dict__)
            # new_journal_entry_list.extend([
            #     self.__ggje__().update(
            #         account_name='应付管理人报酬', account_level_2='业绩报酬',
            #         debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)).force_match(),
            #     self.__ggje__().update(
            #         account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
            #         debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            # ])
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='应付赎回款', account_level_2='上海久铭投资管理有限公司',
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)).force_match(),
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            ])
        elif tag in ('托管费', '运营服务费', '手续费', ):
            assert self.trade_amount < 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount, ),
                self.__ggje__().update(
                    account_name='其他费用', account_level_2='', account_level_3=self.opposite,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount, ),
            ])
            # 确定收款方和缴费原因
            raise NotImplementedError(self)
        elif tag in ('新股中签', '新股缴款'):
            assert self.trade_amount < 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='证券清算款', account_level_2='新股申购', account_level_3=self.opposite,
                    account_level_4=re.sub(r'\d', '', self.subject),
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                self.__ggje__().update(
                    account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            ])
        elif tag in ('转托管户', ):
            if self.trade_amount < 0:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='银行存款', account_level_2=self.opposite, account_level_3='活期存款',
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                    self.__ggje__().update(
                        account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
                ])
            else:
                raise NotImplementedError(self)
        elif tag == '份额转换差额':
            if self.trade_amount > 0:
                obj = self.env.entry_gen.accounts.find_value(
                    product=self.product, account_name='应付赎回款', sub_account=self.opposite)
                assert isinstance(obj, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                        debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
                    self.__ggje__().update(
                        account_name='应付赎回款', account_level_2=self.opposite,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(obj.realtime_net_value)),
                    self.__ggje__().update(
                        account_name='应收申购款', account_level_2='待转换',
                        debit_credit=SIDE_CREDIT_CN, amount=abs(obj.realtime_net_value) + self.trade_amount),
                ])
            elif self.trade_amount < 0:
                obj = self.env.entry_gen.accounts.find_value(
                    product=self.product, account_name='应付赎回款', sub_account='待转换')
                assert isinstance(obj, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='应付赎回款', account_level_2='待转换',
                        debit_credit=SIDE_DEBIT_CN, amount=abs(obj.realtime_net_value)),
                    self.__ggje__().update(
                        account_name='银行存款', account_level_2=self.institution, account_level_3='活期存款',
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
                    self.__ggje__().update(
                        account_name='其他应收款', account_level_2='基金赎回款', account_level_3=self.opposite,
                        debit_credit=SIDE_CREDIT_CN, amount=abs(obj.realtime_net_value) + self.trade_amount),
                ])
            else:
                raise NotImplementedError(self)
        # elif tag == '平安募集户调整':
        #     new_journal_entry_list.extend([
        #         self.__ggje__().update(account_name='银行存款', account_level_2='平安',
        #                                debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
        #     ])      # 用于手动调整平安募集户 注意这不是标准操作！！！
        #     # raise NotImplementedError(self)
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
