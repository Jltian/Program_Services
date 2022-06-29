# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime

from jetend.Interface import AttributeObject
from jetend.DataCheck import *


class TradeFlow(AttributeObject):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'time': '时间', 'institution': '证券账户',
        'security_code': '证券代码', 'security_name': '证券名称', 'security_type': '证券类型',
        'trade_class': '交易操作', 'trade_price': '交易价格', 'trade_volume': '交易数量',
        'trade_amount': '成交金额', 'hashable_key': '交易编号',
        'trade_fee': '交易费用', 'cash_move': '资金变动',
    }
    __info_board__ = None
    TradeBuyRange = []
    TradeSellRange = []

    def check_loaded(self):
        self.security_code = self.security_code.strip().replace(' ', '.')               # 港股通代码点变成空格
        assert is_valid_str(self.security_code), str(self.__dict_data__)
        if '.' not in self.security_code:
            if is_valid_str(self.trade_market):
                if self.trade_market in ('深圳A股', ):
                    self.security_code = '.'.join([self.security_code, 'SZ'])
                elif self.trade_market in ('上海A股', ):
                    self.security_code = '.'.join([self.security_code, 'SH'])
                else:
                    raise NotImplementedError('{}\n{}'.format(self.trade_market, self.__dict_data__))
            else:
                self.security_code = self.info_board.find_security_full_code_by_code(self.security_code)
        if not is_valid_str(self.security_name):
            self.security_name = self.info_board.find_security_name_by_code(self.security_code)
        if not is_valid_str(self.security_type):
            self.security_type = self.info_board.find_security_type_by_code(self.security_code)
        assert is_valid_str(self.product), str(self.__dict_data__)
        assert isinstance(self.date, datetime.date), str(self.__dict_data__)
        assert is_valid_str(self.institution), str(self.__dict_data__)
        assert is_valid_str(self.security_code), str(self.__dict_data__)
        assert '.' in self.security_code, str(self.__dict_data__)
        assert is_valid_str(self.security_type), str(self.__dict_data__)
        assert is_valid_float(self.trade_price), str(self.__dict_data__)
        assert is_valid_float(self.trade_volume), str(self.__dict_data__)
        assert is_valid_float(self.trade_amount), str(self.__dict_data__)
        assert is_valid_str(self.trade_class), str(self.__dict_data__)
        return self

    def calculate_trade_fee(self):
        """计算交易产生的费用"""
        fee_rate = self.info_board.find_security_trade_fee(
            product=self.product, institution=self.institution, security_type=self.security_type,
            date=self.date,
        )
        self.trade_fee = fee_rate.fee_rate * abs(self.trade_amount)
        return self.trade_fee

    def calculate_cash_move(self):
        if '买入' in self.trade_class or self.trade_class in self.TradeBuyRange:
            self.cash_move = - abs(self.trade_amount) - self.trade_fee
        elif '卖出' in self.trade_class or self.trade_class in self.TradeSellRange:
            self.cash_move = abs(self.trade_amount) - self.trade_fee
        else:
            raise RuntimeError('未知交易类型 {} {}'.format(self.trade_class, self.__dict_data__))
        return self.cash_move

    @property
    def security_code(self):
        return self.get_attr('security_code').upper()

    @security_code.setter
    def security_code(self, value: str):
        self.set_attr('security_code', value.upper())

    @property
    def info_board(self):
        from jetend.modules.jmInfoBoard import jmInfoBoard
        if TradeFlow.__info_board__ is None:
            from modules.Modules import Modules
            TradeFlow.__info_board__ = Modules.get_instance().info_board
        assert isinstance(TradeFlow.__info_board__, jmInfoBoard)
        return TradeFlow.__info_board__
