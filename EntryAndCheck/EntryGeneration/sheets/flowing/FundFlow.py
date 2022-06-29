# -*- encoding: UTF-8 -*-
import re

from sheets.Elements import BaseInfo, SecurityInfo
from utils.Constants import *


class FundConfirmFlow(BaseInfo, SecurityInfo):
    """基金投资交易确认表"""
    inner2outer_map = {
        'product': 'name', 'trade_class': 'type', 'date': 'date', 'institution': 'institution',
        'security_name': 'product_name', 'security_code': 'security_code',
        'amount': 'amount', 'price': 'netvalue', 'volume': 'share',
        'confirm_date': 'confirmation_date', 'currency': 'currency',
    }

    @property
    def security_code(self):
        security_code = str_check(self.get_attr('security_code'))
        if is_valid_str(security_code) and len(re.sub(r'\d', '', security_code)) == 0:
            if len(security_code) == 6:
                security_code = '{}.OF'.format(security_code)
            else:
                raise NotImplementedError(self.__dict__)
        else:
            pass
        return security_code

    @property
    def volume(self):
        volume = float_check(self.get_attr('volume'))
        assert is_valid_float(volume), str(self.__dict__)
        return volume

    @property
    def price(self):
        price = float_check(self.get_attr('price'))
        # if not is_valid_float(price):
        #     if self.security_code.endswith('OF'):
        #         price = self.env.wind_board.float_field(
        #             'nav', self.security_code, self.date - datetime.timedelta(days=1),
        #         )
        #     else:
        #         raise NotImplementedError(self.__dict__)
        # else:
        #     pass
        assert is_valid_float(price), str(self.__dict__)
        return price

    @property
    def trade_price(self):
        return self.price

    @property
    def trade_volume(self):
        return self.volume

    @property
    def trade_amount(self):
        return self.amount

    @property
    def amount(self):
        amount = float_check(self.get_attr('amount'))
        if not is_valid_float(amount):
            amount = self.price * self.volume
        else:
            pass
        assert is_valid_float(amount), str(self.__dict__)
        assert not is_different_float(self.price * self.volume, amount), str(self.__dict__)
        return amount

    def generate_journal_entry(self):
        from structures import EventType
        from sheets.entry.Position import EntryPosition, EntryPositionMove
        new_journal_entry_list = list()
        tag = self.trade_class.strip()
        # processing ['申购', '赎回', '基金现金分红']

        if tag == '申购':
            abstract = '基金买入'
            assert self.amount > 0, str(self.__dict__)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=abstract, account_name='基金投资', account_level_2='成本', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount)),
                self.__ggje__().update(
                    abstract=abstract, account_name='其他应收款', account_level_2='未确认基金投资款',
                    account_level_3=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=abs(self.amount)),
            ])

            self.env.trigger_event(
                event_type=EventType.PositionUpdate,
                data=EntryPositionMove(
                    product=self.product, date=self.running_date, institution=self.institution,
                    security_type=SECURITY_TYPE_FUND,
                    security_name=self.security_name, security_code=self.security_code,
                    trade_direction=DIRECTION_BUY, trade_volume=self.volume, trade_price=self.price,
                    trade_amount=self.volume * self.price, trade_offset=OFFSET_OPEN,
                    currency='RMB',
                ))

        elif tag == '转让接收':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='基金投资', account_level_2='成本', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount)),
                self.__ggje__().update(
                    account_name='其他应付款', account_level_2='应付转让款',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount)),
            ])

            self.env.trigger_event(
                event_type=EventType.PositionUpdate,
                data=EntryPositionMove(
                    product=self.interest_related, date=self.running_date, institution=self.institution,
                    security_type=SECURITY_TYPE_FUND,
                    security_name=self.security_name, security_code=self.security_code,
                    trade_direction=DIRECTION_BUY, trade_volume=self.volume, trade_price=self.price,
                    trade_amount=self.volume * self.price, trade_offset=OFFSET_OPEN,
                    currency='RMB',
                ))
            raise NotImplementedError(self)

        elif tag == '赎回':
            assert self.amount < 0, str(self.__dict__)
            abstract = '基金卖出'
            try:
                if is_valid_str(self.security_code):
                    pos = self.env.entry_gen.positions.find_value(
                        product=self.product, institution=self.institution, security_code=self.security_code)
                else:
                    pos = self.env.entry_gen.positions.find_value(
                        product=self.product, institution=self.institution, security_name=self.security_name)
                assert isinstance(pos, EntryPosition)
            except KeyError:
                raise RuntimeError('Sell {} while no holding.'.format(str(self)))

            trade_amount, trade_volume = abs(self.amount), abs(self.volume)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=abstract, account_name='其他应收款', account_level_2='基金赎回款',
                    account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN, amount=trade_amount),
                self.__ggje__().update(
                    abstract=abstract, account_name='基金投资', account_level_2='成本', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=pos.weight_average_cost * trade_volume),
                self.__ggje__().update(
                    abstract=abstract, account_name='基金投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * trade_volume),
                self.__ggje__().update(
                    abstract=abstract, account_name='投资收益', account_level_2='基金投资收益',
                    account_level_3=self.institution, account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=(self.trade_price - pos.last_close_price) * trade_volume),
                # TODO: 对冲公允价值变动损益
                self.__ggje__().update(
                    abstract=abstract, account_name='公允价值变动损益', account_level_2=self.institution,
                    account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * trade_volume),
                self.__ggje__().update(
                    abstract=abstract, account_name='投资收益', account_level_2='基金投资收益',
                    account_level_3=self.institution, account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * trade_volume),
            ])

            self.env.trigger_event(
                event_type=EventType.PositionUpdate,
                data=EntryPositionMove(
                    security_type=SECURITY_TYPE_FUND,
                    product=self.product, date=self.running_date, institution=self.institution,
                    security_code=self.security_code, security_name=self.security_name,
                    trade_direction=DIRECTION_SELL, trade_volume=self.trade_volume, trade_price=self.trade_price,
                    trade_amount=self.trade_amount, trade_offset=OFFSET_CLOSE,
                    currency='RMB',
                ))

        elif tag == '转让出让':
            try:
                pos = self.env.entry_gen.positions.find_value(
                    product=self.product, institution=self.institution, security_name=self.security_name)
                assert isinstance(pos, EntryPosition)
            except KeyError:
                raise RuntimeError('Sell {} while no holding.'.format(str(self)))

            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='其他应收款', account_level_2='待收转让款',
                    account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                self.__ggje__().update(
                    account_name='基金投资', account_level_2='成本', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=pos.weight_average_cost * self.trade_volume),
                self.__ggje__().update(
                    account_name='基金投资', account_level_2='估值增值',
                    account_level_3=self.institution, debit_credit=SIDE_CREDIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume),
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='基金投资收益',
                    account_level_3=self.institution, debit_credit=SIDE_CREDIT_CN,
                    amount=(self.price - pos.last_close_price) * self.trade_volume),
                self.__ggje__().update(
                    account_name='公允价值变动损益', account_level_2=self.institution,
                    account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume),
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='基金投资收益',
                    account_level_3=self.institution, debit_credit=SIDE_CREDIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume),
            ])

            self.env.trigger_event(
                event_type=EventType.PositionUpdate,
                data=EntryPositionMove(
                    security_type=SECURITY_TYPE_OPTION,
                    product=self.product, date=self.running_date, institution=self.institution,
                    security_code=self.security_code, security_name=self.security_name,
                    trade_direction=DIRECTION_SELL, trade_volume=self.trade_volume, trade_price=self.trade_price,
                    trade_amount=self.trade_amount, trade_offset=OFFSET_CLOSE,
                    currency='RMB',
                ))
            raise NotImplementedError(self)

        elif tag in ('基金现金分红', '分红'):
            new_journal_entry_list.extend([
                self.__ggje__().update(abstract=tag, account_name='其他应收款', account_level_2='分红',
                                       account_level_3=self.security_name,
                                       debit_credit=SIDE_DEBIT_CN, amount=abs(self.amount)),
                self.__ggje__().update(abstract=tag, account_name='投资收益', account_level_2='基金投资收益',
                                       account_level_3=self.institution,
                                       debit_credit=SIDE_CREDIT_CN, amount=abs(self.amount)),
            ])
            raise NotImplementedError(self)

        elif tag in ('计提业绩报酬', ):
            try:
                if is_valid_str(self.security_code):
                    pos = self.env.entry_gen.positions.find_value(
                        product=self.product, institution=self.institution, security_code=self.security_code)
                else:
                    pos = self.env.entry_gen.positions.find_value(
                        product=self.product, institution=self.institution, security_name=self.security_name)
                assert isinstance(pos, EntryPosition)
            except KeyError:
                raise RuntimeError('Sell {} while no holding.'.format(str(self)))

            abstract = tag
            trade_amount, trade_volume = abs(self.amount), abs(self.volume)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=abstract, account_name='其他应收款', account_level_2='业绩报酬',
                    account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN, amount=trade_amount),
                self.__ggje__().update(
                    abstract=abstract, account_name='基金投资', account_level_2='成本', account_level_3=self.institution,
                    account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=pos.weight_average_cost * trade_volume),
                self.__ggje__().update(
                    abstract=abstract, account_name='基金投资', account_level_2='估值增值',
                    account_level_3=self.institution, account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * trade_volume),
                self.__ggje__().update(
                    abstract=abstract, account_name='投资收益', account_level_2='基金投资收益',
                    account_level_3=self.institution, account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=(self.trade_price - pos.last_close_price) * trade_volume),
                # TODO: 对冲公允价值变动损益
                self.__ggje__().update(
                    abstract=abstract, account_name='公允价值变动损益', account_level_2=self.institution,
                    account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * trade_volume),
                self.__ggje__().update(
                    abstract=abstract, account_name='投资收益', account_level_2='基金投资收益',
                    account_level_3=self.institution, account_level_4=self.security_name, debit_credit=SIDE_CREDIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * trade_volume),
            ])

            self.env.trigger_event(
                event_type=EventType.PositionUpdate,
                data=EntryPositionMove(
                    security_type=SECURITY_TYPE_FUND,
                    product=self.product, date=self.running_date, institution=self.institution,
                    security_code=self.security_code, security_name=self.security_name,
                    trade_direction=DIRECTION_SELL, trade_volume=self.trade_volume, trade_price=self.trade_price,
                    trade_amount=self.trade_amount, trade_offset=OFFSET_CLOSE,
                    currency='RMB',
                ))

        else:
            raise NotImplementedError(self)
        return new_journal_entry_list

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.running_date,
            abstract=self.trade_class.strip(), account_level_4=self.security_code_name,
        )

    @property
    def running_date(self):
        return self.confirm_date
