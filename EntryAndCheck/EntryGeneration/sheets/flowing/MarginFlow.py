# -*- encoding: UTF-8 -*-

from sheets.flowing.StockFlow import StockFlowing
from utils.Constants import *


class MarginFlow(StockFlowing):
    """当日两融交易流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'contract': '合同号', 'capital_account': '资金账号', 'shareholder_code': '股东代码',
        'security_code': '证券代码', 'security_name': '证券名称',
        'trade_class': '交易类别', 'trade_price': '成交价格',
        'trade_amount': '成交金额', 'trade_volume': '成交数量',
        'cash_move': '资金发生数', 'currency': '币种',
    }
    security_type = SECURITY_TYPE_STOCK

    def generate_journal_entry(self):
        from structures import EventType
        from sheets.entry.Account import EntryAccount
        from sheets.entry.Position import EntryPositionMove

        new_journal_entry_list = list()
        tag = self.trade_class.strip()

        if tag in ():
            pass
        elif tag in ('融资借款', ):
            assert self.cash_move > 0, str(self)
            raise NotImplementedError(self)
            # new_journal_entry_list.extend([
            #     self.__ggje__().update(
            #         account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
            #         debit_credit=SIDE_DEBIT_CN, amount=self.cash_move),
            #     self.__ggje__().update(
            #         account_name='短期借款', account_level_2='信用融资', account_level_3=self.institution,
            #         debit_credit=SIDE_CREDIT_CN, amount=self.cash_move),
            # ])
        elif tag in ('股息红利税补缴', '股息红利差异扣税'):
            assert self.cash_move < 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='股利收益', account_level_3=self.institution,
                    account_level_4='所得税抵减', debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)).force_match(),
            ])
        elif tag in ('卖券偿还融资费用', '直接偿还融资费用', ):
            from sheets.entry.Account import EntryAccount
            assert self.cash_move <= 0, self
            acc = self.env.entry_gen.accounts.find_value(
                account_name='其他应付款', sub_account='融资费用', base_account=self.institution)
            assert isinstance(acc, EntryAccount), str(acc)
            if acc.realtime_net_value < self.cash_move and self.cash_move - acc.realtime_net_value > 50:  # 还部分款
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='其他应付款', account_level_2='融资费用', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
                ])
            elif abs(self.cash_move - acc.realtime_net_value) < 50:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='其他应付款', account_level_2='融资费用', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=0 - acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='其他费用', account_level_2='融资费用误差', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=- self.cash_move + acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=0 - self.cash_move),
                ])
            else:
                raise NotImplementedError(self)
                # new_journal_entry_list.extend([
                # ])
        elif tag in (
                '偿还融资利息', '融资合约利息结息扣收', '卖券偿还融资利息', '直接偿还融资利息',
        ):
            from sheets.entry.Account import EntryAccount
            assert self.cash_move < 0, self
            acc = self.env.entry_gen.accounts.find_value(
                account_name='应付利息', sub_account='短期借款利息', base_account=self.institution)
            assert isinstance(acc, EntryAccount), str(acc)
            if acc.realtime_net_value < self.cash_move and self.cash_move - acc.realtime_net_value > 50:  # 还部分款
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='应付利息', account_level_2='短期借款利息', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
                ])
            elif abs(self.cash_move - acc.realtime_net_value) <= 50 or self.cash_move < acc.realtime_net_value:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='应付利息', account_level_2='短期借款利息', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=0 - acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='利息支出', account_level_2='借款利息支出', account_level_3=self.institution,
                        account_level_4='借款', debit_credit=SIDE_DEBIT_CN,
                        amount= - self.cash_move + acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=0 - self.cash_move),
                ])
            else:
                raise NotImplementedError('{}\n{}'.format(self, acc))

        elif tag in ('卖券偿还融资负债', '直接偿还融资负债', '偿还融资负债本金', '偿还融资负债本金'):
            from sheets.entry.Account import EntryAccount
            assert self.cash_move < 0, self
            acc = self.env.entry_gen.accounts.find_value(
                account_name='短期借款', sub_account='信用融资', base_account=self.institution)
            assert isinstance(acc, EntryAccount), str(acc)
            if acc.realtime_net_value < self.cash_move and self.cash_move - acc.realtime_net_value > 50:  # 还部分款
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='短期借款', account_level_2='信用融资', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
                ])
            elif abs(self.cash_move - acc.realtime_net_value) < 50:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='短期借款', account_level_2='信用融资', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=0 - acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='其他费用', account_level_2='融资费用误差', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount= - self.cash_move + acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=0 - self.cash_move),
                ])
            else:
                # 偿还负债的同时偿还费用，但费用直接并入负债流水
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='短期借款', account_level_2='信用融资', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(acc.realtime_net_value)),
                    self.__ggje__().update(
                        account_name='其他应付款', account_level_2='融资费用', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount= - self.cash_move + acc.realtime_net_value),
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
                ])

            # try:
            #     acc = self.env.entry_gen.accounts.find_value(
            #         product=self.product, account='应付利息', base_account=self.institution,
            #     )
            #     assert isinstance(acc, EntryAccount)
            #     if abs(abs(acc.realtime_net_value) - abs(self.cash_move)) < 5:
            #         new_journal_entry_list.extend([
            #             self.__ggje__().update(
            #                 account_name='应付利息', account_level_2='短期借款利息', account_level_3=self.institution,
            #                 debit_credit=SIDE_DEBIT_CN, amount=abs(acc.realtime_net_value)),
            #             self.__ggje__().update(
            #                 account_name='利息支出', account_level_2='借款利息支出',
            #                 account_level_3=self.institution, account_level_4='借款',
            #                 debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move) - abs(acc.realtime_net_value)),
            #             self.__ggje__().update(
            #                 account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
            #                 debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)).force_match(),
            #         ])
            #     else:
            #         if abs(acc.realtime_net_value) * 0.5 > abs(self.cash_move):
            #             assert self.cash_move < 0.0, str(self)
            #             new_journal_entry_list.extend([
            #                 self.__ggje__().update(
            #                     account_name='应付利息', account_level_2='短期借款利息', account_level_3=self.institution,
            #                     debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
            #                 self.__ggje__().update(
            #                     account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
            #                     debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
            #             ])
            #         else:
            #             raise NotImplementedError('{}\n{}'.format(self, acc))
            # except ValueError:
            #     raise RuntimeError('偿还未知借款利息 {} .'.format(str(self)))
        elif tag in ('利息归本', ):
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='应收利息', sub_account='存出保证金利息', base_account=self.institution,
                )
                assert isinstance(acc, EntryAccount)
                interests = acc.start_net_value
            except ValueError:
                interests = 0.0
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='利息收入', account_level_2='存款利息收入',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move) - abs(interests)),
                self.__ggje__().update(
                    account_name='应收利息', account_level_2='存出保证金利息',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(interests)),
            ])

        elif tag in ('融资买入', ):
            assert self.trade_price >= 0.01, str(self)
            assert abs(self.trade_amount) <= abs(self.cash_move), str(self.__dict__)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN,
                    amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, account_level_3=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move) - abs(self.trade_amount), ),
                self.__ggje__().update(
                    account_name='短期借款', account_level_2='信用融资', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='其他应付款', account_level_2='融资费用', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move) - abs(self.trade_amount), ),
            ])
            self.set_attr('offset', OFFSET_OPEN)
            self.set_attr('trade_direction', DIRECTION_BUY)
            self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))

        elif tag in ('担保品买入', '证券买入', ):
            assert self.trade_price >= 0.01, str(self)
            assert abs(self.trade_amount) <= abs(self.cash_move), str(self.__dict__)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN,
                    amount=self.trade_amount),
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, account_level_3=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move) - abs(self.trade_amount), ),
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)).force_match(),
            ])
            self.set_attr('offset', OFFSET_OPEN)
            self.set_attr('trade_direction', DIRECTION_BUY)
            self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))

        elif tag in ('还款卖出', '证券卖出', '担保品卖出', '卖券还款'):
            from sheets.entry.Position import EntryPosition
            assert self.trade_price >= 0.01, str(self)
            # assert abs(self.trade_amount) >= abs(self.cash_move) - 10, str(self.__dict__)
            pos = self.env.entry_gen.positions.find_value(
                product=self.product, institution=self.institution, security_code=self.security_code
            )
            assert isinstance(pos, EntryPosition)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move), ),
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, account_level_3=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount) - abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=pos.weight_average_cost * self.trade_volume).force_match(),
                self.__ggje__().update(
                    account_name='股票投资', account_level_2='估值增值', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume).force_match(),
                # self.__ggje__().update(
                #     account_name='投资收益', account_level_2='股票投资收益', account_level_3=self.institution,
                #     account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                #     amount=(self.trade_price - pos.last_close_price) * self.trade_volume, ),
                self.__ggje__().update(
                    account_name='公允价值变动损益', account_level_2=self.institution,
                    account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume, ),
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='股票投资收益', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=(self.calculated_trade_price - pos.weight_average_cost) * self.trade_volume, ),
            ])
            self.set_attr('offset', OFFSET_CLOSE)
            self.set_attr('trade_direction', DIRECTION_SELL)
            self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))

        elif tag in ('红利入账', ):
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='应收股利', sub_account=self.institution,
                    base_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                    self.__ggje__().update(
                        account_name='应收股利', account_level_2=self.institution, account_level_3=self.security_name,
                        debit_credit=SIDE_CREDIT_CN, amount=acc.start_net_value),
                    self.__ggje__().update(
                        account_name='投资收益', account_level_2='股利收益', account_level_3=self.institution,
                        account_level_4=self.security_name,
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move) - acc.start_net_value),
                ])
            except ValueError:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                    self.__ggje__().update(
                        account_name='投资收益', account_level_2='股利收益', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
                ])
        elif tag in ('股息入帐', '股息入账', ):
            # if self.date < datetime.date(2018, 5, 11):
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='应收股利', sub_account=self.institution,
                    base_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                    self.__ggje__().update(
                        account_name='应收股利', account_level_2=self.institution, account_level_3=self.security_name,
                        debit_credit=SIDE_CREDIT_CN, amount=acc.start_net_value),
                    self.__ggje__().update(
                        account_name='投资收益', account_level_2='股利收益', account_level_3=self.institution,
                        account_level_4=self.security_name,
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move) - acc.start_net_value),
                ])
            except ValueError:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='信用账户', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                    self.__ggje__().update(
                        account_name='证券清算款', account_level_2='股利收益', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
                ])
        elif tag in ('资金长冻', ):
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='其他费用', account_level_2='递延税费', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='其他应付款', account_level_2='递延税费', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
            ])
        elif tag in ('资金冻结取消', ):
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='其他应付款', account_level_2='递延税费', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='其他费用', account_level_2='递延税费', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
            ])
        elif tag in (
                # '担保品划入', '担保物转入',   # 转出端出凭证
                '证券转银行', '银行转取', '银行转证券', '银行转存','利息结算','资金冻结'
        ):
            pass
        elif tag in ('担保品划入', '担保物转入', ):
            # 转入成本和估值增值
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='股票投资', sub_account='成本', base_account='待转收',
                    note_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3='待转收',
                        account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                        amount=acc.net_value),
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN,
                        amount=acc.net_value),
                ])
            except ValueError:
                raise RuntimeError('未知成本 {} .'.format(str(self)))
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='股票投资', sub_account='估值增值', base_account='待转收',
                    note_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='估值增值', account_level_3='待转收',
                        account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                        amount=acc.net_value),
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='估值增值', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN,
                        amount=acc.net_value),
                ])
            except ValueError:
                raise RuntimeError('未知估值增值 {} .'.format(str(self)))
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='公允价值变动损益', sub_account='待转收',
                    base_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='公允价值变动损益', account_level_2='待转收', account_level_3=self.security_name,
                        debit_credit=SIDE_CREDIT_CN, amount=acc.net_value),
                    self.__ggje__().update(
                        account_name='公允价值变动损益', account_level_2=self.institution, account_level_3=self.security_name,
                        debit_credit=SIDE_DEBIT_CN, amount=acc.net_value),
                ])
            except ValueError:
                raise RuntimeError('未知变动损益 {} .'.format(str(self)))

            try:
                pos = self.env.entry_gen.positions.find_value(
                    product=self.product, institution='待转收', security_code=self.security_code,
                )
                pos.institution = self.institution
            except ValueError:
                raise RuntimeError('未知持仓 {}'.format(self))
        elif tag in ('托管转出', '担保品划出', ):
            # 转出成本项目
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='股票投资', sub_account='成本', base_account=self.institution,
                    note_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3='待转收',
                        account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN,
                        amount=acc.net_value),
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                        amount=acc.net_value),
                ])
            except ValueError:
                raise RuntimeError('未知成本 {} .'.format(str(self)))
            # 转出估值增值项目
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='股票投资', sub_account='估值增值', base_account=self.institution,
                    note_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='估值增值', account_level_3='待转收',
                        account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN,
                        amount=acc.net_value),
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='估值增值', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                        amount=acc.net_value),
                ])
            except ValueError:
                raise RuntimeError('未知估值增值 {} .'.format(str(self)))
            # 转出公允价值
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='公允价值变动损益', sub_account=self.institution,
                    base_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='公允价值变动损益', account_level_2='待转收', account_level_3=self.security_name,
                        debit_credit=SIDE_DEBIT_CN, amount=acc.net_value),
                    self.__ggje__().update(
                        account_name='公允价值变动损益', account_level_2=self.institution,
                        account_level_3=self.security_name,
                        debit_credit=SIDE_CREDIT_CN, amount=acc.net_value),
                ])
            except ValueError:
                raise RuntimeError('未知变动损益 {} .'.format(str(self)))
            # 修改持仓归属
            try:
                pos = self.env.entry_gen.positions.find_value(
                    product=self.product, institution=self.institution, security_code=self.security_code,
                )
                # assert isinstance(pos, EntryPosition)
                pos.institution = '待转收'
            except ValueError:
                raise RuntimeError('未知持仓 {}'.format(self))
        # elif tag in ('担保品划出', ):
        #     if (self.product, self.date.strftime('%Y%m%d'), self.security_name) in [
        #         ('久铭2号', '20190712', '中国化学'), ('稳健7号', '20190712', '中国化学'),
        #     ]:
        #         pass
        #     else:
        #         raise NotImplementedError(self)
        else:
            raise NotImplementedError(self)
        return new_journal_entry_list
