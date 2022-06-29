# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import BaseInfo, SecurityInfo, TradeInfo
from utils.Constants import *


class StockFlowing(BaseInfo, SecurityInfo, TradeInfo):
    """当日股票交易流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'contract': '合同号', 'capital_account': '资金账号', 'shareholder_code': '股东代码',
        'security_code': '证券代码', 'security_name': '证券名称',
        'trade_class': '交易类别', 'trade_price': '成交价格',
        'trade_amount': '成交金额', 'trade_volume': '成交数量',
        'cash_move': '资金发生数', 'currency': '币种',
    }
    security_type = SECURITY_TYPE_STOCK

    @property
    def security_code(self):
        security_code = str_check(self.get_attr('security_code')).upper()
        return security_code

    @property
    def security_name(self):
        security_code = self.security_code
        if '.' not in security_code:
            return str_check(self.get_attr('security_name'))
        else:
            try:
                security_name = self.env.info_board.find_security_name_by_code(self.security_code)
                return security_name
            except RuntimeError as r_error:
                if self.product in self.env.product_range:
                    raise r_error
                else:
                    return ''

    @property
    def trade_price(self):
        trade_price = abs(float_check(self.get_attr('trade_price')))
        # 处理港股交易价格
        if self.security_code.upper().endswith('HK'):
            if self.institution in ('兴业', '安信', '申万', '国君'):  # '中信',
                # if abs(trade_price) < 0.01:
                trade_price = self.calculated_trade_price
                # exchange = self.env.market_board.exchange_settle_rate('HKD', 'CNY', self.date)
                # trade_price = trade_price * exchange
                # else:
                #     if self.product in self.env.product_range:
                #         if self.currency != 'RMB':
                #             trade_price = self.calculated_trade_price
                #         else:
                #             raise NotImplementedError(self.__dict__)
                #     else:
                #         trade_price = safe_division(self.trade_amount, self.trade_volume)
                #         # trade_price = abs(self.cash_move) / self.trade_amount
            elif (self.product, self.institution) in (
                    ('稳健22号', '招商'), ('全球1号', '中信'),
            ):
            # elif self.product == '稳健22号' and self.institution == '招商':
                exchange = self.env.wind_board.exchange_settle_rate('HKD', 'CNY', 'HKS', self.date)
                trade_price = trade_price * exchange
                self.set_attr('trade_amount', trade_price * self.trade_volume)
            elif self.product not in self.env.product_range:
                trade_price = safe_division(abs(self.cash_move), self.trade_volume)
            else:
                raise NotImplementedError(self.__dict__)
        assert is_valid_float(trade_price), '{}\n{}'.format(trade_price, self.__dict__)
        return trade_price

    @property
    def calculated_trade_price(self):
        return safe_division(self.trade_amount, self.trade_volume)

    @property
    def trade_amount(self):
        trade_amount = abs(float_check(self.get_attr('trade_amount')))
        # if self.security_code.upper().endswith('HK') and not is_valid_float(trade_amount):
        #     if self.institution in ('中信', '兴业', '安信', ):
        #         trade_amount = self.trade_price * self.trade_volume
        #     else:
        #         raise NotImplementedError(self.__dict__)
        if not is_valid_float(trade_amount) and self.institution in (
                '中信建投', '中信', '中信两融', '招商两融', '华泰', '兴业', '中泰', '财通', '申万', '长江', '招商', '银河',
                '安信', '海通', '国君',
        ) and not self.security_code.upper().endswith('HK'):
            trade_amount = self.trade_price * self.trade_volume
        if self.institution in ('中信', ) and self.security_code.upper().endswith('HK'):
            exchange = self.env.wind_board.exchange_settle_rate('HKD', 'CNY', 'HKS', self.date)
            trade_amount = abs(float_check(self.get_attr('trade_price'))) * self.trade_volume * exchange
            print(self.__dict__)
            # trade_amount = trade_amount * self.env.wind_board.exchange_settle_rate('HKD', 'CNY', 'HKS', self.date)
        # 处理交易额与交易价格和交易数量不同的情况
        if not self.security_code.upper().endswith('HK'):
            if is_different_float(self.trade_price * self.trade_volume, trade_amount):
                if abs(self.trade_price * self.trade_volume - trade_amount) < 0.01 * trade_amount:
                    # trade_amount = self.trade_price * self.trade_volume
                    pass
                else:
                    if abs(self.trade_volume) < 0.01:       # 红利税等直接扣款内容
                        trade_amount = 0.0
                    else:
                        raise RuntimeError('交易金额 不等于 交易价格乘以交易数量 {}'.format(self.__dict__))
        # 验证港股的价格已经被正确转换成人民币，防止出现原始价格为港币的情况
        if self.security_code.upper().endswith('HK'):
            if abs(trade_amount) >= 0.01 and abs(self.cash_move) >= 0.01:
                gap = abs(abs(abs(self.cash_move) - trade_amount) / trade_amount)
                if gap > 0.05:
                    if self.product not in self.env.product_range:
                        pass
                    else:
                        exchange = self.env.wind_board.exchange_settle_rate('HKD', 'CNY', 'HKS', self.date)
                        trade_amount = trade_amount * exchange
                        self.set_attr('trade_price', safe_division(trade_amount, self.trade_volume))
                        print(exchange, self.__dict__)
                else:
                    pass
            # print(trade_amount, self.__dict__)
        # if abs(trade_amount) > 0 and 'HK' in self.security_code.upper():
        #     if abs(trade_amount) < 0.01 or abs(self.cash_move) < 0.01:
        #         pass
        #     else:
        #         gap = abs((abs(self.cash_move) - self.trade_amount) / self.trade_amount)
        #         if gap > 0.02 and self.product in self.env.product_range:
        #             raise RuntimeError('交易发生金额 不等于 交易价格乘以交易数量 {}'.format(self))
        #         else:
        #             pass
        if abs(trade_amount) >= 0.01 and abs(self.cash_move) >= 0.01:
            gap = abs(abs(self.cash_move) - trade_amount) / trade_amount
            if gap > 0.05:
                if self.product not in self.env.product_range:
                    pass
                else:
                    raise RuntimeError(self.__dict__)
            else:
                pass
        assert is_valid_float(trade_amount), str(self.__dict__)
        return trade_amount

    @property
    def currency(self):
        return 'RMB'

    def generate_journal_entry(self):
        from structures import EventType
        from sheets.entry.Account import EntryAccount
        from sheets.entry.Position import EntryPositionMove, EntryPosition
        from sheets.flowing.VATTransaction import VATTransaction

        new_journal_entry_list = list()
        tag = self.trade_class.strip()

        if self.security_name in tag:
            tag = tag.replace(self.security_name, '')

        if tag in ('ETF现金替代退款', 'ETF 申购退款'):
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='存出保证金', base_account=self.institution,)
            except ValueError:
                raise RuntimeError('不存在该账户 {}'.format(self))
            assert isinstance(acc, EntryAccount)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2=acc.sub_account, account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN,  amount=abs(self.cash_move)).force_match(),
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='股票投资收益', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
            ])
        elif tag in ('偿还融资利息', '卖券偿还融资利息', '直接偿还融资利息'):
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='应付利息', sub_account='短期借款利息', base_account=self.institution,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='应付利息', account_level_2='短期借款利息', account_level_3=self.institution,
                        account_level_4='借款', debit_credit=SIDE_DEBIT_CN,
                        amount=abs(acc.start_net_value)).force_match(),
                    self.__ggje__().update(
                        account_name='利息支出', account_level_2='借款利息支出', account_level_3=self.institution,
                        account_level_4='借款', debit_credit=SIDE_DEBIT_CN,
                        amount=abs(self.cash_move) - abs(acc.start_net_value)),
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='普通账户', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)).force_match(),
                ])
            except ValueError:
                raise RuntimeError('偿还未知利息 {} .'.format(str(self)))
        # elif tag in ('偿还融资负债本金', '卖券偿还融资负债', '直接偿还融资负债', ):
        #     try:
        #         acc = self.env.entry_gen.accounts.find_value(
        #             product=self.product, account='短期借款', sub_account=self.institution,
        #         )
        #         assert isinstance(acc, EntryAccount)
        #         if abs(acc.start_net_value) >= abs(self.cash_move):
        #             new_journal_entry_list.extend([
        #                 self.__ggje__().update(
        #                     account_name='短期借款', account_level_2=self.institution,
        #                     debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
        #                 self.__ggje__().update(
        #                     account_name='存出保证金', account_level_2=self.institution,
        #                     debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)).force_match(),
        #             ])
        #         else:
        #             raise NotImplementedError('{}\n{}'.format(self, acc))
        #     except ValueError:
        #         raise RuntimeError('偿还未知借款 {} .'.format(str(self)))
        #     raise NotImplementedError(self)
        elif tag in ('利息归本', '利息结转', '批量利息归本'):
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
                    account_name='存出保证金', account_level_2='普通账户', account_level_3=self.institution,
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

        elif tag == '利息支付':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='存出保证金', account_level_2=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    abstract=tag, account_name='应付利息', account_level_2=self.institution,
                    account_level_3=self.security_name, debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
            ])
            raise RuntimeError(self)

        elif '组合费' in tag or tag in ('港股通组合费收取', '港股通证券组合费', '港股通组合费', '组合费', ):
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='其他费用', account_level_2='港股通组合费', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='普通账户', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)).force_match(),
            ])

        elif tag in ('货币基金收益结转', '货币基金收益结转建信', '红股入帐', '红股入账'):
            if self.security_name in ('财富宝E', '建信添益'):
                # 货基不可以看成价格为零的买入，否则成本为零，即市值为零
                assert self.trade_volume > 0, str(self)
                trade_price = self.env.wind_board.float_field(
                    'close', self.security_code, self.date - datetime.timedelta(days=1),)
                trade_amount = self.trade_price * self.trade_volume

                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                    self.__ggje__().update(
                        account_name='投资收益', account_level_2='股票投资收益', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
                ])

                self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove(
                    product=self.product, date=self.date, institution=self.institution,
                    security_code=self.security_code, security_name=self.security_name,
                    security_type=SECURITY_TYPE_STOCK,
                    trade_direction=DIRECTION_BUY, trade_offset=OFFSET_OPEN,
                    trade_price=trade_price, trade_volume=self.trade_volume, trade_amount=trade_amount,
                    currency=self.currency,
                ))
            else:
                raise NotImplementedError(self)

        elif tag in ('股息入帐', '股息入账', '红利入账', '港股通红利发放', '港股红利发放资金交收'):
            # if self.date < datetime.date(2018, 5, 11):
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='应收股利', sub_account=self.institution,
                    base_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='存出保证金', account_level_2='普通账户', account_level_3=self.institution,
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
                        account_name='存出保证金', account_level_2='普通账户', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                    self.__ggje__().update(
                        account_name='证券清算款', account_level_2='股利收益', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
                ])

        elif tag in ('股息税', '股息个税征收', '股息红利税补缴', '股息红利差异扣税', '股息红利税补', '红利差异税扣税'):



            assert self.cash_move < 0, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='股利收益', account_level_3=self.institution,
                    account_level_4='所得税抵减', debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='普通账户', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
            ])

        elif tag in ('证券买入', '担保品买入', '港股通买入成交', '买入'):
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
                    account_name='存出保证金', account_level_2='普通账户', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)).force_match(),
            ])
            self.set_attr('offset', OFFSET_OPEN)
            self.set_attr('trade_direction', DIRECTION_BUY)
            self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))

        # elif tag == '质押回购拆出':
        #     new_journal_entry_list.extend([
        #         self.__ggje__().update(
        #             account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
        #             debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount),
        #         self.__ggje__().update(
        #             account_name='交易费用', account_level_2=self.institution, debit_credit=SIDE_DEBIT_CN,
        #             amount=abs(self.cash_move) - abs(self.trade_amount), ),
        #         self.__ggje__().update(
        #             account_name='存出保证金', account_level_2=self.institution,
        #             debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
        #     ])
        #     self.env.trigger_event(
        #         EventType.PositionUpdate,
        #         EntryPositionMove(
        #             product=self.product, date=self.date, institution=self.institution,
        #             security_code=self.security_code, security_name=self.security_name,
        #             security_type=SECURITY_TYPE_ASSET_BUY_BACK,
        #             trade_direction=DIRECTION_BUY, trade_offset=OFFSET_OPEN,
        #             trade_volume=self.trade_volume, trade_price=self.trade_price,
        #             trade_amount=self.trade_amount, currency=self.currency,
        #         )
        #     )
        #     self.offset, self.trade_direction = OFFSET_OPEN, DIRECTION_BUY
        #     self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))
        # elif tag == '拆出质押购回':
        #     try:
        #         pos = self.env.entry_gen.positions.find_value(
        #             product=self.product, institution=self.institution, security_code=self.security_code
        #         )
        #         assert isinstance(pos, EntryPosition)
        #     except KeyError:
        #         raise RuntimeError('Sell {} while no holding.'.format(str(self)))
        #
        #     value_add_amount = (self.trade_price - pos.tax_cost) * self.trade_volume
        #     if value_add_amount >= 0.01:
        #         self.env.trigger_event(
        #             event_type=EventType.VATGen,
        #             data=VATTransaction(
        #                 product=self.product, date=self.date, institution=self.institution, account_code=1102,
        #                 security_code=self.security_code, security_name=self.security_name,
        #                 tax_cost=pos.tax_cost, trade_volume=self.trade_volume, trade_price=self.trade_price,
        #                 value_add_amount=value_add_amount,
        #                 vat=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT),
        #                 building_tax=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_BT,
        #                 education_surcharge=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_ES,
        #                 local_education_surcharge=value_add_amount * TAX_RATE_VAT / (
        #                         1 + TAX_RATE_VAT) * TAX_RATE_LES
        #             ))
        #         raise RuntimeError(str(VATTransaction(
        #                 product=self.product, date=self.date, institution=self.institution, account_code=1102,
        #                 security_code=self.security_code, security_name=self.security_name,
        #                 tax_cost=pos.tax_cost, trade_volume=self.trade_volume, trade_price=self.trade_price,
        #                 value_add_amount=value_add_amount,
        #                 vat=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT),
        #                 building_tax=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_BT,
        #                 education_surcharge=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_ES,
        #                 local_education_surcharge=value_add_amount * TAX_RATE_VAT / (
        #                         1 + TAX_RATE_VAT) * TAX_RATE_LES
        #             )))
        #
        #     new_journal_entry_list.extend([
        #         self.__ggje__().update(
        #             account_name='存出保证金', account_level_2=self.institution,
        #             debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
        #         self.__ggje__().update(
        #             account_name='交易费用', account_level_2=self.institution, debit_credit=SIDE_DEBIT_CN,
        #             amount=abs(self.trade_amount) - abs(self.cash_move), ),
        #         self.__ggje__().update(
        #             account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
        #             debit_credit=SIDE_CREDIT_CN, amount=pos.weight_average_cost * self.trade_volume),
        #         self.__ggje__().update(
        #             account_name='投资收益', account_level_2='股票投资收益', account_level_3=self.institution,
        #             debit_credit=SIDE_CREDIT_CN,
        #
        #             amount=(self.trade_price - pos.weight_average_cost) * self.trade_volume, ),
        #     ])
        #     self.offset, self.trade_direction = OFFSET_CLOSE, DIRECTION_SELL
        #     self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))
        #wavezhou
        elif tag in ('配股入账'):
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN,
                    amount=self.trade_amount),

            ])
            self.set_attr('offset', OFFSET_OPEN)
            self.set_attr('trade_direction', DIRECTION_BUY)
            self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))





        elif tag in ('证券卖出', '大宗卖出', '担保品卖出', '港股通卖出成交', '港股通股票卖出', '卖出'):
            assert self.trade_price > 0.00, str(self)
            # assert self.trade_amount >= abs(self.cash_move) - 10.0, str(self)
            pos = self.env.entry_gen.positions.find_value(
                product=self.product, institution=self.institution, security_code=self.security_code
            )
            assert isinstance(pos, EntryPosition)

            if self.security_name in ['财富宝E', '建信添益'] or self.security_code in ('511850.SH',):
                value_add_amount = (self.trade_price - pos.tax_cost) * self.trade_volume
                if value_add_amount >= 0.01:
                    self.env.trigger_event(
                        event_type=EventType.VATGen,
                        data=VATTransaction(
                            product=self.product, date=self.date, institution=self.institution, account_code=1102,
                            security_code=self.security_code, security_name=self.security_name,
                            tax_cost=pos.tax_cost, trade_volume=self.trade_volume,
                            trade_price=self.calculated_trade_price,
                            value_add_amount=value_add_amount,
                            vat=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT),
                            # building_tax=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_BT,
                            # education_surcharge=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_ES,
                            # local_education_surcharge=value_add_amount * TAX_RATE_VAT / (
                            #         1 + TAX_RATE_VAT) * TAX_RATE_LES,
                        ))

            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='普通账户', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)).force_match(),
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, account_level_3=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount) - abs(self.cash_move), ),
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
                    account_level_4=self.security_name,
                    debit_credit=SIDE_CREDIT_CN,
                    amount=(self.calculated_trade_price - pos.weight_average_cost) * self.trade_volume, ),
            ])
            self.set_attr('offset', OFFSET_CLOSE)
            self.set_attr('trade_direction', DIRECTION_SELL)
            self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))

        elif tag in ('新股申购确认缴款', '配售缴款', ):
            assert self.cash_move < 0, self
            # if '申购' in self.security_name:
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='证券清算款', account_level_2='新股申购', account_level_3=self.institution,
                    account_level_4=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='普通账户', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
            ])
            # else:
            #     raise NotImplementedError(self)

        elif tag in ('新股入帐', '新股入账'):
            try:
                acc = self.env.entry_gen.accounts.find_value(
                    product=self.product, account_name='证券清算款',
                    note_account=self.security_name,
                )
                assert isinstance(acc, EntryAccount)
                assert not is_different_float(self.trade_amount, acc.realtime_net_value), '{}\n{}'.format(self, acc)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
                        account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN,
                        amount=self.trade_amount),
                    self.__ggje__().update(
                        account_name='证券清算款', account_level_2='新股申购', account_level_3=acc.base_account,
                        account_level_4=acc.note_account, debit_credit=SIDE_CREDIT_CN,
                        amount=self.trade_amount),
                ])

                self.set_attr('offset', OFFSET_OPEN)
                self.set_attr('trade_direction', DIRECTION_BUY)
                self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))

            except ValueError:
                print(self.env.entry_gen.accounts.find_value_where(
                    product=self.product, account_name='证券清算款',
                ))
                raise NotImplementedError(self)
            # try:
            #     pos = self.env.entry_gen.positions.find_value(
            #         product=self.product, institution=self.institution, security_code=self.security_code
            #     )
            #     assert isinstance(pos, EntryPosition)
            #     if int(pos.hold_volume) == int(self.trade_volume):
            #         return list()
            #     else:
            #         raise NotImplementedError(self)
            # except ValueError:
            #     # 手动调节配售标号新股编号
            #     if self.date == datetime.date(2018, 1, 2) and self.product in ('稳健6号', '稳健17号', ):
            #         return list()
            #     if self.date == datetime.date(2018, 1, 4):
            #         if self.security_code in ('603161.SH', ):
            #             return list()
            #         else:
            #             raise NotImplementedError(self)
            #     if self.date == datetime.date(2018, 1, 16) and self.security_code == '601828.SH':
            #         return list()
            #     if self.date == datetime.date(2018, 1, 30) and self.product in ('稳健7号', '久铭2号', ):
            #         return list()
            #     if self.date == datetime.date(2018, 6, 7) and self.security_code in ('601138.SH', ):
            #         return list()
            #     if self.date == datetime.date(2019, 4, 10) and self.product in ('稳健11号'):
            #         return list()
            #     if self.date == datetime.date(2019, 4, 15) and self.security_code == '603317.SH':
            #         return list()
            #     if self.date == datetime.date(2019, 5, 15) and self.security_code == '600989.SH':
            #         return list()
            #     assert self.trade_price > 0 and self.trade_amount > 0, str(self)
            #     if (self.date, self.security_code) in [(datetime.date(2018, 1, 10), '300733.SZ')]:
            #         new_journal_entry_list.extend([
            #             self.__ggje__().update(
            #                 account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
            #                 debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
            #             self.__ggje__().update(
            #                 account_name='证券清算款', account_level_2=self.institution,
            #                 debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            #         ])
            #     elif (self.date, self.security_code) in [
            #         (datetime.date(2018, 10, 18), '601162.SH'), (datetime.date(2018, 11, 15), '601319.SH'),
            #     ]:
            #         new_journal_entry_list.extend([
            #             self.__ggje__().update(
            #                 account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
            #                 debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
            #             self.__ggje__().update(
            #                 account_name='其他应付款', account_level_2=self.institution,
            #                 debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            #         ])
            #     else:
            #         new_journal_entry_list.extend([
            #             self.__ggje__().update(
            #                 account_name='其他应付款', account_level_2=self.institution,
            #                 debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
            #             self.__ggje__().update(
            #                 account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
            #                 debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            #         ])
            #     self.set_attr('offset', OFFSET_OPEN)
            #     self.set_attr('trade_direction', DIRECTION_BUY)
            #     self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))
        # elif tag in ('配售中签', '市值申购中签'):
        #     new_journal_entry_list.extend([
        #         self.__ggje__().update(
        #             account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
        #             debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
        #         self.__ggje__().update(
        #             account_name='证券清算款', account_level_2=self.institution,
        #             debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
        #     ])
        #     self.set_attr('offset', OFFSET_OPEN)
        #     self.set_attr('trade_direction', DIRECTION_BUY)
        #     self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))
        elif tag in ('市值申购中签', '配售中签'):
            pass
            # if self.institution in ('华泰', ):
            #     pass
            # else:
            #     new_journal_entry_list.extend([
            #         self.__ggje__().update(
            #             account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
            #             account_level_4=self.
            #             debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
            #         self.__ggje__().update(
            #             account_name='证券清算款', account_level_2=self.institution,
            #             debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            #     ])
            #     self.set_attr('offset', OFFSET_OPEN)
            #     self.set_attr('trade_direction', DIRECTION_BUY)
            #     self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))
        elif tag in ():
            # '托管转入', '担保物转出', '余额入账', '转托转入','撤指转出','指定交易','撤销指定'
            raise NotImplementedError('需要凭证层面修改科目余额表 {}'.format(self))
            # try:
            #     pos = self.env.entry_gen.positions.find_value(
            #         product=self.product, security_code=self.security_code
            #     )
            #     assert isinstance(pos, EntryPosition)
            # except KeyError:
            #     raise RuntimeError('Sell {} while no holding.'.format(str(self)))
            #
            # assert abs(self.trade_volume) > 0, str(self)
            #
            # new_journal_entry_list.extend([
            #     self.__ggje__().update(
            #         account_name='股票投资', account_level_2='成本', account_level_3=self.institution,
            #         debit_credit=SIDE_DEBIT_CN, amount=pos.weight_average_cost * self.trade_volume),
            #     self.__ggje__().update(
            #         account_name='股票投资', account_level_2='估值增值', account_level_3=self.institution,
            #         debit_credit=SIDE_DEBIT_CN,
            #         amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume),
            #     self.__ggje__().update(
            #         account_name='股票投资', account_level_2='成本', account_level_3=pos.institution,
            #         debit_credit=SIDE_CREDIT_CN, amount=pos.weight_average_cost * self.trade_volume),
            #     self.__ggje__().update(
            #         account_name='股票投资', account_level_2='估值增值', account_level_3=pos.institution,
            #         debit_credit=SIDE_CREDIT_CN,
            #         amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume),
            # ])

            # self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove(
            #     security_type=SECURITY_TYPE_STOCK,
            #     product=self.product, date=self.date, institution=self.institution,
            #     security_code=self.security_code, security_name=self.security_name,
            #     trade_direction=DIRECTION_BUY, trade_volume=self.trade_volume, trade_price=pos.weight_average_cost,
            #     trade_amount=
            # ))

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
                assert isinstance(pos, EntryPosition)
                pos.institution = '待转收'
            except ValueError:
                raise RuntimeError('未知持仓 {}'.format(self))
            # if (self.product, self.date.strftime('%Y%m%d'), self.security_name) in [
            #             #     ('稳健22号', '20190605', '完美世界'), ('久铭2号', '20190611', '中国化学'),
            #             #     ('久铭2号', '20190611', '完美世界'), ('稳健33号', '20190614', '松炀申购'),
            #             #     ('稳健7号', '20190701', '完美世界'), ('稳健7号', '20190702', '中国化学'),
            #             #     ('稳健7号', '20190711', '济川药业'), ('久铭2号', '20190711', '建设银行'),
            #             #     ('久铭2号', '20200305', '五粮液'), ('稳健7号', '20200305', 'XD贵州茅'),
            #             # ]:
            #             #     pass
            #             # else:
            #             #     raise NotImplementedError(self)

        elif tag in ('担保品划入', ):
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

        elif tag in (
            '配售配号', '申购配号',
            '银行转证券', '证券转银行', '银行转取', '银行转存', '新股申购失败', '|',
            '港股通买入交收', '证券冻结', '删除银行账号', '银行帐户开户', '港股通卖出交收', '撤销指定',
        ):
            pass

        else:
            raise NotImplementedError(self)
        return new_journal_entry_list

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.date, abstract=self.trade_class.strip(),
            account_level_4=self.security_code_name,
        )
