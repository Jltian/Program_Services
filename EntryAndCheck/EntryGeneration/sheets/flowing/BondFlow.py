# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import AccountClass, Contract, Flowing, Trading
from utils.Constants import *


class BondFlowing(AccountClass, Contract, Flowing, Trading):
    """当日债券交易流水"""
    inner2outer_map = {
        'product': '产品', 'account_name': '科目', 'institution': '机构', 'date': '日期',
        'security_code': '证券代码', 'security_name': '证券名称', 'trade_class': '交易类别',
        'trade_price': '成交价格', 'trade_volume': '成交数量', 'trade_amount': '成交金额',
        'cash_move': '资金发生数', 'total_fee': '费用合计', 'currency': '币种'
    }

    def __init__(self, product: str = '', account_name: str = '', institution: str = '', date: datetime.date = None,
                 security_code: str = '', security_name: str = '', trade_class: str = '',
                 trade_price: float = None, trade_volume: float = None, trade_amount: float = None,
                 cash_move: float = None, total_fee: float = None, currency: str = ''):
        AccountClass.__init__(self, account_name=account_name if is_valid_str(account_name) else '债券投资')
        Contract.__init__(self, security_code=security_code, security_name=security_name)
        Flowing.__init__(self, product=product, institution=institution, date=date)
        Trading.__init__(self, trade_volume=trade_volume, cash_move=cash_move,
                         trade_price=trade_price, trade_amount=trade_amount, currency=currency)
        self.trade_class = str_check(trade_class)
        self.total_fee = float_check(total_fee)

        # 华泰证券交易量需放大10倍
        if self.institution == '华泰':
            self.trade_volume = 10 * self.trade_volume
            self.trade_amount = self.trade_price * self.trade_volume
            self.currency = 'RMB'

        # 处理交易金额缺失的问题
        if (not is_valid_float(self.trade_amount) or abs(self.trade_amount) < 0.01) \
                and self.institution in (
                '中信建投', '中信', '兴业', '中泰', '财通', '申万', '长江', '招商', '国君',
        ):
            self.trade_amount = self.trade_price * self.trade_volume

        if self.institution in ('中信美股', ):
            self.trade_volume = self.trade_amount / self.trade_price

        try:
            assert is_valid_float(self.trade_price), '价格信息缺失！{}'.format(self)
            assert is_valid_float(self.trade_volume), '数量信息缺失！{}'.format(self)
            assert is_valid_float(self.trade_amount), '交易额信息缺失！{}'.format(self)
            assert is_valid_float(self.cash_move), '金额变动信息缺失！{}'.format(self)
            assert is_valid_str(self.currency), '币种信息缺失！{}'.format(self)
        except AssertionError as ass_error:
            if self.product in self.env.product_range:
                raise ass_error
            else:
                pass

        if is_different_float(self.trade_price * self.trade_volume, self.trade_amount):
            gap = self.trade_price * self.trade_volume - self.trade_amount
            if abs(gap) < 10:
                self.trade_price = self.trade_amount / self.trade_volume
            else:
                if self.product not in self.env.product_range:
                    pass
                else:
                    raise RuntimeError('交易金额 不等于 交易价格乘以交易数量 {}'.format(self))

        if abs(self.trade_amount) >= 0.01 and abs(self.cash_move) >= 0.01:
            gap = abs(abs(self.cash_move) - self.trade_amount) / self.trade_amount
            if gap > 0.2:
                if gap > 8 and self.institution in ('申万', '东方', ):
                    self.trade_volume = 10 * self.trade_volume
                    self.trade_amount = 10 * self.trade_amount
                else:
                    if self.security_code in ('204007.SH', '9618.HK'):
                        pass
                    else:
                        raise RuntimeError(self)

    def generate_journal_entry(self):
        from structures import EventType
        from sheets.entry.Account import EntryAccount
        from sheets.entry.Position import EntryPosition, EntryPositionMove
        new_journal_entry_list = list()
        tag = self.trade_class.strip()

        if self.product not in self.env.product_range:
            return new_journal_entry_list

        if self.institution in ('中信美股', ):
            return new_journal_entry_list

        assert self.currency == 'RMB', str(self)

        if tag in ('债券买入', '证券买入'):
            assert self.trade_amount < abs(self.cash_move), str(self)
            # if self.security_code in ('132013.SH', ) :
            #     new_journal_entry_list.extend([
            #         self.__ggje__().update(
            #             account_name='债券投资', account_level_2='成本', account_level_3=self.institution,
            #             debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount - self.interest_receivable),
            #         self.__ggje__().update(
            #             account_name='应收利息', account_level_2=self.security_name,
            #             debit_credit=SIDE_DEBIT_CN, amount=self.interest_receivable * 0.8),
            #         self.__ggje__().update(
            #             account_name='公允价值变动损益', account_level_2=self.institution,
            #             account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN,
            #             amount=self.interest_receivable * 0.2, ),
            #         self.__ggje__().update(
            #             account_name='交易费用', account_level_2=self.institution, debit_credit=SIDE_DEBIT_CN,
            #             amount=abs(self.cash_move) - self.trade_amount),
            #         self.__ggje__().update(
            #             account_name='存出保证金', account_level_2=self.institution, debit_credit=SIDE_CREDIT_CN,
            #             amount=abs(self.cash_move)),
            #     ])
            #
            # else:
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='债券投资', account_level_2='成本', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount - self.interest_receivable),
                self.__ggje__().update(
                    account_name='应收利息', account_level_2=self.institution, account_level_3=self.security_name,
                    debit_credit=SIDE_DEBIT_CN, amount=self.interest_receivable),
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution, debit_credit=SIDE_DEBIT_CN,
                    amount=abs(self.cash_move) - self.trade_amount),
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2=self.institution, debit_credit=SIDE_CREDIT_CN,
                    amount=abs(self.cash_move)),
            ])

            self.env.trigger_event(
                event_type=EventType.PositionUpdate,
                data=EntryPositionMove(
                    security_type=SECURITY_TYPE_BOND,
                    product=self.product, date=self.date, institution=self.institution,
                    security_name=self.security_name, security_code=self.security_code,
                    trade_direction=DIRECTION_BUY,
                    trade_volume=self.trade_volume,
                    trade_price=(self.trade_amount - self.interest_receivable) / self.trade_volume,
                    trade_amount=self.trade_amount - self.interest_receivable,
                    trade_offset=OFFSET_OPEN, currency=self.currency))

            raise NotImplementedError(self)

        elif tag in ('债券卖出', '证券卖出'):
            assert self.trade_amount > abs(self.cash_move), str(self)
            # 应收利息 80% 100% 计提不同
            try:
                pos = self.env.entry_gen.positions.find_value(
                    product=self.product, account_name='债券投资',
                    institution=self.institution, security_code=self.security_code
                )
            except KeyError:
                raise RuntimeError('Sell {} while no holding.'.format(str(self)))
            assert isinstance(pos, EntryPosition)

            # if self.security_code == '132013.SH':
            #     new_journal_entry_list.extend([
            #         self.__ggje__().update(
            #             account_name='存出保证金', account_level_2=self.institution,
            #             debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
            #         self.__ggje__().update(
            #             account_name='交易费用', account_level_2=self.institution,
            #             debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount - abs(self.cash_move)),
            #         self.__ggje__().update(
            #             account_name='应收利息', account_level_2=self.security_name, debit_credit=SIDE_CREDIT_CN,
            #             amount=self.interest_receivable * (1 - 0.2)),
            #         self.__ggje__().update(
            #             account_name='债券投资', account_level_2='成本', account_level_3=self.institution,
            #             debit_credit=SIDE_CREDIT_CN, amount=pos.weight_average_cost * self.trade_volume),
            #         self.__ggje__().update(
            #             account_name='债券投资', account_level_2='估值增值', account_level_3=self.institution,
            #             debit_credit=SIDE_CREDIT_CN,
            #             amount=(pos.last_close_price - pos.weight_average_cost) * abs(self.trade_volume)),
            #         self.__ggje__().update(
            #             account_name='投资收益', account_level_2='债券投资收益', account_level_3=self.institution,
            #             debit_credit=SIDE_CREDIT_CN,
            #             amount=(self.trade_price - pos.last_close_price) * self.trade_volume \
            #                    - self.interest_receivable * 0.8),
            #         self.__ggje__().update(
            #             account_name='公允价值变动损益', account_level_2=self.institution,
            #             account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN,
            #             amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume),
            #         self.__ggje__().update(
            #             account_name='投资收益', account_level_2='债券投资收益', account_level_3=self.institution,
            #             debit_credit=SIDE_CREDIT_CN,
            #             amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume),
            #     ])
            #
            # else:
            # 假设价格内包含利息
            assert self.trade_amount > abs(self.cash_move)
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='交易费用', account_level_2=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=self.trade_amount - abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='债券投资', account_level_2='成本', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=pos.weight_average_cost * self.trade_volume),
                self.__ggje__().update(
                    account_name='债券投资', account_level_2='估值增值', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * abs(self.trade_volume)),
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='债券投资收益', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN,
                    amount=(self.trade_price - pos.last_close_price) * self.trade_volume - self.interest_receivable),
                self.__ggje__().update(
                    account_name='应收利息', account_level_2=self.institution, account_level_3=self.security_name,
                    debit_credit=SIDE_CREDIT_CN, amount=self.interest_receivable),
                self.__ggje__().update(
                    account_name='公允价值变动损益', account_level_2=self.institution,
                    account_level_3=self.security_name, debit_credit=SIDE_DEBIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume),
                self.__ggje__().update(
                    account_name='投资收益', account_level_2='债券投资收益', account_level_3=self.institution,
                    debit_credit=SIDE_CREDIT_CN,
                    amount=(pos.last_close_price - pos.weight_average_cost) * self.trade_volume),
            ])

            self.env.trigger_event(
                event_type=EventType.PositionUpdate,
                data=EntryPositionMove(
                    product=self.product, date=self.date, institution=self.institution,
                    security_name=self.security_name,
                    security_code=self.security_code, security_type=SECURITY_TYPE_BOND,
                    trade_direction=DIRECTION_SELL,
                    trade_volume=self.trade_volume,
                    trade_price=(self.trade_amount - self.interest_receivable) / self.trade_volume,
                    trade_amount=self.trade_amount - self.interest_receivable,
                    trade_offset=OFFSET_CLOSE, currency=self.currency)
            )

            raise NotImplementedError(self)

        elif tag == '证券清算款转债券投资':
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='债券投资', account_level_2='成本', account_level_3=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.trade_amount)),
                self.__ggje__().update(
                    account_name='证券清算款', account_level_2=self.institution,
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.trade_amount)),
            ])
            raise NotImplementedError(self)

        elif tag in ('债券兑息', ):
            acc = self.env.entry_gen.accounts.find_value(
                product=self.product, account_name='其他应收款', sub_account=self.institution,
                base_account=self.security_name,
            )
            assert isinstance(acc, EntryAccount)
            assert abs(self.cash_move) > acc.net_value > 0.0
            # new_journal_entry_list.extend([
            #     self.__ggje__().update(
            #         account_name='存出保证金', account_level_2=self.institution,
            #         debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
            #     self.__ggje__().update(
            #         account_name='应交税费', account_level_2=self.institution, account_level_3='股息红利税',
            #         debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move) - acc.net_value),
            #     self.__ggje__().update(
            #         account_name='其他应收款', account_level_2=self.institution, account_level_3=self.security_name,
            #         debit_credit=SIDE_CREDIT_CN, amount=acc.net_value),
            # ])
            new_journal_entry_list.extend([
                self.__ggje__().update(
                    account_name='存出保证金', account_level_2=self.institution,
                    debit_credit=SIDE_DEBIT_CN, amount=abs(self.cash_move)),
                self.__ggje__().update(
                    account_name='利息收入', account_level_2=self.institution, account_level_3='所得税对冲',
                    debit_credit=SIDE_CREDIT_CN, amount=abs(self.cash_move) - acc.net_value),
                self.__ggje__().update(
                    account_name='其他应收款', account_level_2=self.institution, account_level_3=self.security_name,
                    debit_credit=SIDE_CREDIT_CN, amount=acc.net_value),
            ])
            raise NotImplementedError(self)
        elif '组合费' in tag:
            pass
        elif tag in (
                '配售配号', '新股申购失败', '申购配号', '市值申购中签', '市值申购中签扣款',      # 配售配号仅仅是券商发出的通知
                '银行转证券', '证券转银行', '银行转取', '银行转存', '银行转存招行存管', '|',    # [重复]银行转证券在银行流水中生成分录
                '利息归本', '利息结转', '股息红利税补缴', '股息红利税补', '批量利息归本',    # [重复]在股票流水中处理
                '港股通组合费收取', '港股通证券组合费', '港股通组合费', '组合费', '转托管费',   # [重复]在股票流水中处理
                '融资借款', '配售中签', '撤销指定',   # [重复]在股票流水中处理
                '删除银行账号', '银行帐户开户', '股息个税征收',
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

    @property
    def interest_receivable(self):
        interest_receivable = self.__data__.get('interest_receivable', None)
        if not is_valid_float(interest_receivable):
            interest_receivable = self.env.wind_board.float_field(
                'self.accruedinterest', self.security_code, self.date) * self.trade_volume
            self.interest_receivable = interest_receivable
        assert is_valid_float(interest_receivable), str(self)
        return interest_receivable

    @interest_receivable.setter
    def interest_receivable(self, value):
        self.__data__.__setitem__('interest_receivable', value)
