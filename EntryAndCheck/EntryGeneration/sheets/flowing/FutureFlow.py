# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import AccountClass, BaseInfo, SecurityInfo, TradeInfo
from utils.Constants import *


class FutureFlowing(AccountClass, BaseInfo, SecurityInfo, TradeInfo):
    """当日期货交易流水"""
    inner2outer_map = {
        'hash_key': '流水编号', 'product': '产品', 'date': '日期', 'institution': '机构',  'date': '日期',
        'security_code': '期货合约', 'security_name': '期货品种', 'trade_class': '交易行为', 'offset': '开平方向',
        'trade_price': '成交价格', 'trade_volume': '成交数量', 'trade_amount': '成交金额',
        'trade_fee': '手续费', 'realize_pl': '平仓盈亏', 'cash_move': '金额变动', 'currency': '币种',
    }
    security_type = SECURITY_TYPE_FUTURE

    # def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
    #              trade_class: str = '', security_name: str = '', security_code: str = '',
    #              trade_price: float = None, trade_volume: float = None, trade_amount: float = None,
    #              trade_fee: float = None, cash_move: float = None, offset: str = '', currency: str = '',
    #              **kwargs):
    #     AccountClass.__init__(self, account_code=1106, account_name=kwargs.get('account_name', '权证投资'))
    #     Contract.__init__(self, security_code=security_code, security_name=security_name)
    #     Flowing.__init__(self, product=product, institution=institution, date=date)
    #     Trading.__init__(self, trade_amount=trade_amount, trade_price=trade_price, trade_volume=trade_volume,
    #                      offset=offset, cash_move=cash_move, currency=currency)
    #     self.trade_class = str_check(trade_class)
    #     self.trade_fee = float_check(trade_fee)
    #
    #     if not is_valid_float(self.cash_move) and self.institution in (
    #         '国君期货',
    #     ):
    #         if '买' in self.trade_class:
    #             self.cash_move = self.trade_amount + self.trade_fee
    #         elif '卖' in self.trade_class:
    #             self.cash_move = self.trade_amount - self.trade_fee
    #         else:
    #             raise NotImplementedError(self)
    #
    #     try:
    #         assert is_valid_float(self.trade_price), '价格信息缺失！{}'.format(self)
    #         assert is_valid_float(self.trade_volume), '数量信息缺失！{}'.format(self)
    #         assert is_valid_float(self.trade_amount), '交易额信息缺失！{}'.format(self)
    #         assert is_valid_float(self.cash_move), '金额变动信息缺失！{}'.format(self)
    #         assert is_valid_str(self.currency), '币种信息缺失！{}'.format(self)
    #     except AssertionError as ass_error:
    #         if self.product in self.env.product_range:
    #             raise ass_error
    #         else:
    #             pass
    #
    #     if is_different_float(self.trade_price * self.trade_volume, self.trade_amount):
    #         if abs(self.trade_price * self.trade_volume - self.trade_amount) < 10:
    #             self.trade_amount = self.trade_price * self.trade_volume
    #         else:
    #             if abs(self.trade_amount / self.trade_volume - self.trade_price) < 0.01:
    #                 self.trade_price = self.trade_amount / self.trade_volume
    #             elif self.institution in ('国君期货', ):
    #                 self.trade_price = self.trade_amount / self.trade_volume
    #             elif self.product not in self.env.product_name_range:
    #                 pass
    #             else:
    #                 raise RuntimeError('交易金额 不等于 交易价格乘以交易数量 {}'.format(self))

    @property
    def offset(self):
        offset_str = str_check(self.get_attr('offset'))
        if len(offset_str) == 0:
            raise RuntimeError(self.__dict__)
        elif offset_str in (OFFSET_OPEN, ):
            return OFFSET_OPEN
        elif offset_str in (OFFSET_CLOSE, ):
            return OFFSET_CLOSE
        elif offset_str in (OFFSET_NONE, '-', ):
            return OFFSET_NONE
        else:
            raise NotImplementedError(self.__dict__)

    def generate_journal_entry(self):
        from structures import EventType
        from sheets.entry.Position import EntryPosition, EntryPositionMove
        from sheets.flowing.VATTransaction import VATTransaction

        new_journal_entry_list = list()
        tag = self.trade_class.strip()

        if tag in ('买', ):
            assert abs(self.trade_fee) > 0.0, str(self)
            assert self.offset == OFFSET_OPEN, str(self)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, account_level_3=self.security_code,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_fee)),
                self.__ggje__().update(
                    account_name='结算备付金', account_level_2='期货账户', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_fee)),
            ])

            self.set_attr('trade_direction', DIRECTION_BUY)
            self.set_attr('trade_price', self.env.wind_board.float_field(
                'contractmultiplier', self.security_code, self.date, option=''
            ) * self.trade_price)
            self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))

        elif tag == '出入金':
            # 入金为正， 出金为负
            if self.cash_move >= 0.0:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='结算备付金', account_level_2='期货账户', account_level_3=self.institution,
                        debit_credit=SIDE_DEBIT_CN, amount=self.cash_move),
                    self.__ggje__().update(
                        account_name='交易费用', account_level_2=self.institution, account_level_3='出入金',
                        debit_credit=SIDE_CREDIT_CN, amount=self.cash_move),
                ])
            else:
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        account_name='结算备付金', account_level_2='期货账户', account_level_3=self.institution,
                        debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
                    self.__ggje__().update(
                        account_name='交易费用', account_level_2=self.institution, account_level_3='出入金',
                        debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                ])
        elif tag == '卖':
            assert self.offset == OFFSET_CLOSE, str(self)
            pos = self.env.entry_gen.positions.find_value(
                product=self.product, institution=self.institution, security_code=self.security_code
            )
            assert isinstance(pos, EntryPosition)
            if abs(self.realize_pl) > 1.0:
                value_changed = self.trade_volume * (pos.last_close_price - pos.weight_average_cost)
                new_journal_entry_list.extend([
                    self.__ggje__().update(
                        abstract='期货估值增值', account_name='权证投资', account_level_2='估值增值',
                        account_level_3=self.institution, account_level_4=self.security_code,
                        debit_credit=SIDE_CREDIT_CN, amount=value_changed),
                    self.__ggje__().update(
                        abstract='期货估值增值', account_name='公允价值变动损益', account_level_2=self.institution,
                        account_level_3=self.security_code, debit_credit=SIDE_DEBIT_CN, amount=value_changed),
                ])
                realize_pl = self.realize_pl + value_changed
                if realize_pl >= 0.0:
                    new_journal_entry_list.extend([
                        self.__ggje__().update(
                            account_name='结算备付金', account_level_2='期货账户', account_level_3=self.institution,
                            debit_credit=SIDE_DEBIT_CN, amount=realize_pl),
                        self.__ggje__().update(
                            account_name='投资收益', account_level_2='衍生投资收益', account_level_3=self.institution,
                            account_level_4=self.security_code, debit_credit=SIDE_CREDIT_CN,
                            amount=realize_pl),
                    ])
                else:
                    new_journal_entry_list.extend([
                        self.__ggje__().update(
                            account_name='投资收益', account_level_2='衍生投资收益', account_level_3=self.institution,
                            account_level_4=self.security_code, debit_credit=SIDE_DEBIT_CN,
                            amount=abs(realize_pl)),
                        self.__ggje__().update(
                            account_name='结算备付金', account_level_2='期货账户', account_level_3=self.institution,
                            debit_credit=SIDE_CREDIT_CN, amount=abs(realize_pl)),
                    ])

                self.env.trigger_event(
                    event_type=EventType.VATGen,
                    data=VATTransaction(
                        product=self.product, date=self.date, institution=self.institution,
                        account_code=1106, account_name='权证投资',
                        security_code=self.security_code, security_name=self.security_name,
                        tax_cost=-1.0, trade_volume=-1.0, trade_price=-1.0,
                        value_add_amount=self.realize_pl, vat=self.realize_pl * TAX_RATE_VAT / (1 + TAX_RATE_VAT),
                    ))
                self.set_attr('trade_direction', DIRECTION_SELL)
                self.set_attr('trade_price', self.env.wind_board.float_field(
                    'contractmultiplier', self.security_code, self.date, option=''
                ) * self.trade_price)
                self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))
            else:
                raise NotImplementedError(self)
                # try:
                #     pos = self.env.entry_gen.positions.find_value(
                #         product=self.product, institution=self.institution, security_code=self.security_code)
                #     assert isinstance(pos, EntryPosition)
                # except KeyError:
                #     raise RuntimeError('Sell {} while no holding.'.format(str(self)))
                #
                # value_added_amount = (self.trade_price - pos.weight_average_cost) * self.trade_volume
                #
                # self.env.trigger_event(
                #     event_type=EventType.VATGen,
                #     data=VATTransaction(
                #         product=self.product, date=self.date, account_code=1106, institution=self.institution,
                #         security_code=self.security_code, security_name=self.security_name,
                #         tax_cost=pos.tax_cost, trade_volume=self.trade_volume, trade_price=self.trade_price,
                #         value_add_amount=value_added_amount, vat=value_added_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT),
                #     ))
                #
                # new_journal_entry_list.extend([
                #     self.__ggje__().update(
                #         account_name='结算备付金', account_level_2=self.institution, debit_credit=SIDE_DEBIT_CN,
                #         amount=(self.trade_price - pos.last_close_price) * self.trade_volume \
                #                + pos.last_close_price * self.trade_volume * self.future_leverage_ratio() \
                #                - self.trade_fee, ),
                #     self.__ggje__().update(
                #         account_name='交易费用', account_level_2=self.institution, debit_credit=SIDE_DEBIT_CN,
                #         amount=self.trade_fee),
                #     self.__ggje__().update(
                #         account_name='存出保证金', account_level_2=self.institution, debit_credit=SIDE_CREDIT_CN,
                #         amount=pos.last_close_price * self.trade_volume * self.future_leverage_ratio(), ),
                #     self.__ggje__().update(
                #         account_name='投资收益', account_level_2='衍生投资收益', account_level_3=self.institution,
                #         debit_credit=SIDE_CREDIT_CN,
                #         amount=(self.trade_price - pos.last_close_price) * self.trade_volume),
                # ])
                #
                # self.env.trigger_event(
                #     event_type=EventType.PositionUpdate,
                #     data=EntryPositionMove(
                #         security_type=SECURITY_TYPE_FUTURE,
                #         product=self.product, date=self.date, institution=self.institution,
                #         security_name=self.security_name, security_code=self.security_code,
                #         trade_direction=DIRECTION_SELL, trade_offset=OFFSET_CLOSE,
                #         trade_volume=self.trade_volume, trade_price=self.trade_price, trade_amount=self.trade_amount,
                #         currency=self.currency,
                #         ))
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

    @property
    @depreciated_method('security_code')
    def future_code(self):
        return self.security_code

    @property
    @depreciated_method('security_name')
    def future_name(self):
        return self.security_name
