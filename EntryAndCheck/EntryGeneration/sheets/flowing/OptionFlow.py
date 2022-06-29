# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import AccountClass, Contract, EntryGenerable, Flowing, Trading
from utils.Constants import *


class OptionFlowing(AccountClass, Contract, EntryGenerable, Flowing, Trading):
    """当日期权交易流水"""
    inner2outer_map = {
        'product': '产品', 'institution': '机构', 'date': '日期',
        'security_code': '合约代码', 'security_name': '合约名称',
        'trade_class': '交易类型', 'offset': '开平方向',
        'trade_price': '成交价格', 'trade_volume': '成交数量', 'trade_amount': '成交金额',
        'trade_fee': '手续费', 'cash_move': '资金发生数', 'currency': '币种'
    }
    security_type = SECURITY_TYPE_OPTION

    def __init__(self, product: str = '', institution: str = '', date: datetime.date = None,
                 trade_class: str = '', offset: str = '',
                 security_code: str = '', security_name: str = '',
                 trade_price: float = None, trade_volume: float = None, trade_amount: float = None,
                 trade_fee: float = None, cash_move: float = None, currency: str = ''):
        Contract.__init__(self, security_code=security_code, security_name=security_name)
        Flowing.__init__(self, product=product, institution=institution, date=date)
        Trading.__init__(self, trade_price=trade_price, trade_volume=trade_volume, trade_amount=trade_amount,
                         cash_move=cash_move, currency=currency)
        self.trade_class = str_check(trade_class)
        self.offset = str_check(offset)
        self.trade_fee = float_check(trade_fee)

    def check_loaded(self):

        if abs(self.trade_price * self.trade_volume) / abs(self.trade_amount) < 0.1 and self.institution in (
                '国君期权', '中信期权',
        ):
            self.trade_price = self.trade_price * self.env.wind_board.float_field(
                'contractmultiplier', self.security_code, self.date, option='')
        if abs(self.trade_price * self.trade_volume) / abs(self.trade_amount) < 0.1 and self.institution in (
                '兴业期权', '招商期权',
        ):
            self.trade_price = self.trade_amount / self.trade_volume

        if not is_valid_float(self.trade_fee) and is_valid_float(self.cash_move) and self.institution in (
                '国君期权', ):
            self.trade_fee = abs(self.trade_amount - abs(self.cash_move))

        try:
            assert is_valid_float(self.trade_price), '价格信息缺失！{}'.format(self)
            assert is_valid_float(self.trade_volume), '数量信息缺失！{}'.format(self)
            assert is_valid_float(self.trade_amount), '交易额信息缺失！{}'.format(self)
            assert is_valid_float(self.cash_move), '金额变动信息缺失！{}'.format(self)
            assert is_valid_float(self.trade_fee), '手续费信息缺失！{}'.format(self)
            assert is_valid_str(self.currency), '币种信息缺失！{}'.format(self)
        except AssertionError as ass_error:
            if self.product in self.env.product_range:
                raise ass_error
            else:
                pass

        if is_different_float(self.trade_price * self.trade_volume, self.trade_amount):
            gap = self.trade_price * self.trade_volume - self.trade_amount
            if abs(gap) < self.trade_amount * 0.01 \
                    or abs(self.trade_amount / self.trade_volume - self.trade_price) / self.trade_price < 0.01:
                self.trade_price = self.trade_amount / self.trade_volume
            else:
                raise RuntimeError('交易金额 不等于 交易价格乘以交易数量 gap: {}, {}'.format(gap, self))

        if is_different_float(abs(abs(self.cash_move) - self.trade_amount), abs(self.trade_fee)):
            gap = abs(abs(self.cash_move) - self.trade_amount) - abs(self.trade_fee)
            if gap > 0.5:
                raise RuntimeError('交易金额 不等于 资金变动刨除手续费 gap: {}, {}'.format(gap, self))

    @property
    @depreciated_method('security_code')
    def option_code(self):
        return self.security_code

    @property
    @depreciated_method('security_name')
    def option_name(self):
        return self.security_name

    def generate_journal_entry(self):
        from structures import EventType
        from sheets.entry.Account import EntryAccount
        from sheets.entry.Position import EntryPosition, EntryPositionMove
        from sheets.flowing.VATTransaction import VATTransaction
        new_journal_entry_list = list()
        tag = self.trade_class.strip()
        # processing '买入认沽开仓', '卖出认沽开仓', '利息归本'
        self.check_loaded()

        if tag in ('买入认沽开仓', '买入开仓', '买入'):
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='权证投资', account_level_2='成本', account_level_3=self.institution,
                    account_level_4=self.security_code,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, account_level_3=self.security_code,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move) - abs(self.trade_amount)),
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='期权账户', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move)),
            ])

            self.offset, self.trade_direction = OFFSET_OPEN, DIRECTION_BUY
            self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))

        elif tag in ('卖出平仓', '卖出'):
            try:
                pos = self.env.entry_gen.positions.find_value(
                    product=self.product, institution=self.institution, security_code=self.security_code)
                assert isinstance(pos, EntryPosition)
            except ValueError:
                print(self.env.entry_gen.positions.find_value_where(product=self.product))
                raise RuntimeError('Sell {} while no holding.'.format(str(self)))

            value_add_amount = (self.trade_price - pos.tax_cost) * self.trade_volume
            self.env.trigger_event(
                event_type=EventType.VATGen,
                data=VATTransaction(
                    product=self.product, account_code=1106, institution=self.institution,
                    date=self.date, security_code=self.security_code, security_name=self.security_name,
                    tax_cost=pos.tax_cost, trade_volume=self.trade_volume, trade_price=self.trade_price,
                    value_add_amount=value_add_amount, vat=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT),
                    # building_tax=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_BT,
                    # education_surcharge=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_ES,
                    # local_education_surcharge=value_add_amount * TAX_RATE_VAT / (1 + TAX_RATE_VAT) * TAX_RATE_LES
                ))

            last_close_price = pos.last_close_price if is_valid_float(pos.last_close_price) else pos.weight_average_cost

            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2='期权账户', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, account_level_3=self.security_code,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_fee),
                self.__ggje__().update(
                    account_name='权证投资', account_level_2='成本', account_level_3=self.institution,
                    account_level_4=self.security_code,
                    debit_credit=SIDE_CREDIT_CN, amount=pos.weight_average_cost * self.trade_volume),
                self.__ggje__().update(
                    account_name='权证投资', account_level_2='估值增值', account_level_3=self.institution,
                    account_level_4=self.security_code, debit_credit=SIDE_CREDIT_CN,
                    amount=(last_close_price - pos.weight_average_cost) * self.trade_volume),
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='衍生投资收益', account_level_3=self.institution,
                    account_level_4=self.security_code, debit_credit=SIDE_CREDIT_CN,
                    amount=(self.trade_price - last_close_price) * self.trade_volume),
                self.__ggje__().update(
                    account_name='公允价值变动损益', account_level_2=self.institution, account_level_3=self.security_code,
                    debit_credit=SIDE_DEBIT_CN,
                    amount=(last_close_price - pos.weight_average_cost) * self.trade_volume),
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='衍生投资收益', account_level_3=self.institution,
                    account_level_4=self.security_code, debit_credit=SIDE_CREDIT_CN,
                    amount=(last_close_price - pos.weight_average_cost) * self.trade_volume),
            ])

            self.offset, self.trade_direction = OFFSET_CLOSE, DIRECTION_SELL
            self.env.trigger_event(EventType.PositionUpdate, EntryPositionMove.init_from(self))

        elif tag == '利息归本':
            try:
                di = self.env.entry_gen.accounts.find_value(
                    product=self.product, account='应收利息', base_account=self.institution,)
                assert isinstance(di, EntryAccount)
                interests = di.start_net_value
            except ValueError:
                interests = 0.0

            new_journal_entry_list.extend([
                self.__ggje__().update(
                    abstract=tag, account_name='存出保证金', account_level_2='期权账户', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    abstract=tag, account_name='利息收入', account_level_2='存款利息收入',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move) - abs(interests)),
                self.__ggje__().update(
                    abstract=tag, account_name='应收利息', account_level_2='存出保证金利息',
                    account_level_3=self.institution, account_level_4='保证金',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(interests)),
            ])
        else:
            raise NotImplementedError(self)
        return new_journal_entry_list

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.date, abstract=self.trade_class.strip(),
            # account_level_4=self.security_code_name,
        )
