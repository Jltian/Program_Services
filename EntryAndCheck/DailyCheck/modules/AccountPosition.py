# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
from jetend.Interface import AttributeObject
from jetend.DataCheck import *


class AccountPosition(AttributeObject):
    """账户余额和产品持仓"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'account_name': '科目名称', 'institution': '机构',
        'security_code': '证券代码', 'security_name': '证券名称',
        'volume': '数量', 'market_price_origin': '原始市场价', 'currency_origin': '原始货币',
        'exchange_rate': '汇率', 'market_price': '市场价', 'market_value': '市值', 'currency': '货币',
    }
    __market_board__ = None
    __info_board__ = None
    TradeBuyRange = ('买', )
    TradeSellRange = ('卖', )

    # @property
    # def product(self):
    #     product = self.get_attr('product')
    #     if product in ('久铭全球丰收1号', ):
    #         return product.replace('久铭', '')
    #     else:
    #         return product

    @property
    def security_name(self):
        security_name = str_check(self.get_attr('security_name'))
        return security_name

    @security_name.setter
    def security_name(self, value):
        self.set_attr('security_name', str_check(value))

    @property
    def institution(self):
        institution = self.get_attr('institution')
        assert isinstance(institution, str), '{}'.format(self.__dict__)
        if self.account_name == '证券账户' and '普通' in institution:
            institution = institution.replace('普通', '')
            self.set_attr('institution', institution)
        if self.is_position() and '普通' in institution:
            institution = institution.replace('普通', '')
            self.set_attr('institution', institution)
        # if self.account_name == '信用账户' and '两融' not in institution:
        #     institution = '{}{}'.format(institution, '两融')
        return institution

    @institution.setter
    def institution(self, value: str):
        self.set_attr('institution', value)

    @property
    def date(self):
        return date_check(self.get_attr('date'))

    @date.setter
    def date(self, value):
        self.set_attr('date', date_check(value))
        self.set_attr('last_market_price_origin', self.get_attr('market_price_origin'))
        self.set_attr('last_market_price', self.get_attr('market_price'))
        self.set_attr('market_price_origin', float_check(None))
        self.set_attr('exchange_rate', float_check(None))

    def update_by(self, obj):
        from jetend.jmSheets import BankFlow, EstimatedNormalTradeFlow, EstimatedMarginTradeFlow
        assert self.product == obj.product, '持仓和流水不匹配 {}\n{}'.format(self, obj)
        # 持仓变化、账户资金变化
        if isinstance(obj, (EstimatedNormalTradeFlow, EstimatedMarginTradeFlow)):
            assert self.date == obj.date, '持仓和流水不匹配 {}\n{}'.format(self, obj)
            if self.is_account():
                if '买入' in obj.trade_class or obj.trade_class in self.TradeBuyRange:
                    self.volume -= abs(obj.cash_move)
                elif '卖出' in obj.trade_class or obj.trade_class in self.TradeSellRange:
                    self.volume += abs(obj.cash_move)
                else:
                    raise NotImplementedError('Unknown trade class {}\n{}.'.format(obj.trade_class, obj))
            else:
                assert self.security_code == obj.security_code, '{}\n{}'.format(self, obj)
                if '买入' in obj.trade_class or obj.trade_class in self.TradeBuyRange:
                    self.volume += abs(obj.trade_volume)
                elif '卖出' in obj.trade_class or obj.trade_class in self.TradeSellRange:
                    self.volume -= abs(obj.trade_volume)
                else:
                    raise NotImplementedError('Unknown trade class {}\n{}.'.format(obj.trade_class, obj))
        # 银行账户资金变化
        elif isinstance(obj, BankFlow):
            assert self.date == obj.date, '持仓和流水不匹配 {}\n{}'.format(self, obj)
            if self.institution == '-' or obj.institution == '-':
                pass
            else:
                assert self.institution == obj.institution, '持仓和流水不匹配 {}\n{}'.format(self, obj)
            self.volume += obj.trade_amount
        else:
            raise NotImplementedError(type(obj))
        return self

    @property
    def volume(self):
        volume = self.get_attr('volume')
        assert is_valid_float(volume), str(self.__dict_data__)
        return round(volume, 8)

    @volume.setter
    def volume(self, value):
        self.pop_attr('market_value')
        # self.set_attr('market_value', float_check(None))                # 数量变动导致市值变动
        self.set_attr('volume', float_check(value))

    @property
    def market_price_origin(self):
        market_price_origin = self.get_attr('market_price_origin')
        if is_valid_float(market_price_origin):
            return market_price_origin
        if self.account_name in (
                '累计应付管理费', '实收基金', '应收利息', '累计应收管理费返还', '资产净值', '银行存款', '证券账户', '期货账户',
                '期权账户', '信用账户', '结算备付金', '存出保证金', '单位净值', '应交税费', '应付利息', '其他应付款',
                '应收债券利息', '应收股利', '短期借款', '待确认申购款', '已付应付管理费', '已收应收管理费返还', '应付赎回款',
                '应付融资利息', '应付融资费用', '累计应付业绩报酬', '累计已付业绩报酬', '预收递延股利', '申购股票', '其他应收款',
                '应付申购款', '资产总计', '负债总计',
        ):
            return float_check(None)
        elif self.account_name in ('股票', '货基', ):
            try:
                market_price_origin = self.market_board.float_field('close', self.security_code, self.date, option='')
            except AssertionError as market_assertion_error:
                if self.market_board.ipo_date(self.security_code, self.date) >= self.date:
                    market_price_origin = self.get_attr('last_market_price')
                    assert is_valid_float(market_price_origin), self.__dict_data__
                    self.set_attr('market_price_origin', market_price_origin)
                    return market_price_origin
                else:
                    print(self.__dict__)
                    raise market_assertion_error
        elif self.account_name in ('期货', '期权', ):
            market_price_origin = self.market_board.float_field('settle', self.security_code, self.date, option='')
        elif self.account_name in ('公募基金', ):
            if 'OF' in self.security_code.upper():
                market_price_origin = self.market_board.float_field('nav', self.security_code, self.date, option='')
            else:
                raise NotImplementedError(self.__dict_data__)
        elif self.account_name in ('ETF基金', ):
            if 'SH' in self.security_code.upper():
                market_price_origin = self.market_board.float_field('close', self.security_code, self.date, option='')
            else:
                raise NotImplementedError(self.__dict_data__)
        elif self.account_name in ('自有产品', ):
            market_price_origin = self.info_board.find_product_net_value_by_name(
                self.security_name, self.date, ta_read=False)
        elif self.account_name in ('可转债', '债券', ):
            market_price_origin = self.market_board.float_field('cleanprice', self.security_code, self.date, option='')
        else:
            raise NotImplementedError(self.__dict_data__)
        assert is_valid_float(market_price_origin), self.__dict_data__
        self.set_attr('market_price_origin', market_price_origin)
        self.set_attr('market_price', float_check(None))
        return market_price_origin

    @property
    def market_price(self):
        market_price = self.get_attr('market_price')
        if is_valid_float(market_price):
            return round(market_price, 8)
        try:
            market_price = self.market_price_origin * self.exchange_rate
        except TypeError as type_error:
            if self.account_name in ('股票', ):
                if is_valid_float(self.get_attr('raw_market_value')) and is_valid_float(self.get_attr('volume')):
                    market_price = round(self.get_attr('raw_market_value') / self.get_attr('volume'), 8)
                    self.set_attr('market_price_origin', market_price)
                    return market_price
                else:
                    raise RuntimeError(self.__dict__)
            elif self.account_name in ('期货', '期权', ):
                return self.market_price_origin
            else:
                print(self.__dict__)
                raise type_error
        if not is_valid_float(market_price):
            return float_check(None)
        self.set_attr('market_price', market_price)
        self.set_attr('market_value', float_check(None))                # 市场价变动导致市值变动
        return round(market_price, 8)

    @property
    def exchange_rate(self):
        exchange_rate = self.get_attr('exchange_rate')
        if is_valid_float(exchange_rate):
            return exchange_rate
        if self.currency_origin == self.currency:
            return 1.0
        elif self.currency == 'RMB':
            if self.institution == '华泰互换':
                return exchange_rate
            if self.currency_origin == 'USD':
                if self.institution in ('中信SWAP', '美股收益互换'):
                    exchange_rate = self.info_board.find_exchange_rate(self.date, 'USDCNYSET.SWAP').value
                else:
                    raise NotImplementedError(self.__dict_data__)
            elif self.currency_origin == 'HKD':
                if self.institution in ('中信SWAP', '港股收益互换'):
                    exchange_rate = self.info_board.find_exchange_rate(self.date, 'HKDCNYSET.SWAP').value
                elif self.institution in (
                        '安信', '海通', '申万', '兴业', '中信', '招商', '国信', '华泰', '长江', '国君',
                ) or '普通' in self.institution:
                    exchange_rate = self.market_board.exchange_settle_rate('HKD', 'CNY', 'HKS', self.date)
                else:
                    raise NotImplementedError('{}\n{}'.format(self.institution, self.__dict_data__))
            else:
                raise NotImplementedError(self.__dict_data__)
        else:
            raise NotImplementedError(self.__dict_data__)
        self.set_attr('exchange_rate', exchange_rate)
        self.set_attr('market_price', float_check(None))                # 汇率变动导致市场价格变动
        assert is_valid_float(exchange_rate), '{}'.format(self.__dict_data__)
        return exchange_rate

    @property
    def market_value(self):
        """本币市值 -> float"""
        market_value = self.get_attr('market_value')
        if is_valid_float(market_value):
            return round(market_value, 4)
        if self.account_name in (
                '资产净值', '银行存款', '应收利息', '证券账户', '累计应付管理费', '期货账户', '期权账户', '累计应收管理费返还',
                '存出保证金', '结算备付金', '应交税费', '应付利息', '其他应付款', '实收基金', '单位净值', '应收债券利息', '应收股利',
                '短期借款', '待确认申购款', '已付应付管理费', '信用账户', '应付赎回款', '已收应收管理费返还', '应付融资利息',
                '应付融资费用', '累计应付业绩报酬', '累计已付业绩报酬', '预收递延股利', '其他应收款', '应付申购款',
                '资产总计', '负债总计',
        ):
            # 资产类科目
            if self.account_name in (
                    '资产净值', '银行存款', '应收利息', '证券账户', '期货账户', '期权账户', '累计应收管理费返还', '信用账户',
                    '存出保证金', '结算备付金', '实收基金', '单位净值', '应收债券利息', '应收股利', '待确认申购款',
                    '已付应付管理费', '累计已付业绩报酬', '其他应收款', '资产总计',
            ):
                market_value = self.volume * self.exchange_rate
            # 负债类科目
            elif self.account_name in (
                    '累计应付管理费', '应付利息', '其他应付款', '应交税费', '短期借款', '已收应收管理费返还', '应付赎回款',
                    '应付融资利息', '应付融资费用', '累计应付业绩报酬', '预收递延股利', '应付申购款', '负债总计',
            ):
                market_value = - self.volume * self.exchange_rate
            else:
                raise NotImplementedError(self.__dict_data__)
        elif self.account_name in ('股票', '公募基金', 'ETF基金', '可转债', '债券', '自有产品', '货基', ):
            market_value = self.volume * self.market_price
        elif self.account_name in ('期货', ):
            raise RuntimeError('遗漏权证保证金数额 {}'.format(self.__dict_data__))
        elif self.account_name in ('期权', ):
            market_value = self.market_price * self.market_board.float_field(
                'contractmultiplier', self.security_code, self.date, option=''
            ) * self.volume
        elif self.account_name in ('申购股票', ):
            market_value = float_check(self.raw_market_value)
        else:
            raise NotImplementedError(self.__dict_data__)
        self.set_attr('market_value', market_value)
        return round(market_value, 4)

    def is_account(self):
        """判断本条属于账户、余额类条目"""
        if self.account_name in (
                '资产净值', '银行存款', '应收利息', '证券账户', '累计应付管理费', '期货账户', '期权账户', '累计应收管理费返还',
                '信用账户', '存出保证金', '结算备付金', '应交税费', '应付利息', '其他应付款', '实收基金', '单位净值',
                '应收债券利息', '应收股利',
                '短期借款', '待确认申购款', '已付应付管理费', '已收应收管理费返还', '应付赎回款', '应付融资利息', '应付融资费用',
                '累计应付业绩报酬', '累计已付业绩报酬', '预收递延股利', '其他应收款', '应付申购款', '资产总计', '负债总计',
        ):
            return True
        elif self.account_name in (
                '股票', '公募基金', 'ETF基金', '可转债', '债券', '自有产品', '货基', '期货', '期权', '申购股票',
        ):
            return False
        else:
            raise NotImplementedError('{}\n{}'.format(self.account_name, self.__dict_data__))

    def is_position(self):
        """判断本条属于持仓类条目"""
        if self.is_account():
            return False
        else:
            return True

    @property
    def exchange_market(self):
        if self.is_account():
            raise RuntimeError('对象非持仓 {}'.format(self.__dict_data__))
        return self.security_code.upper().split('.')[-1]

    @property
    def market_board(self):
        from jetend.modules.jmMarketBoard import jmMarketBoard
        if AccountPosition.__market_board__ is None:
            from modules.Modules import Modules
            AccountPosition.__market_board__ = Modules.get_instance().market_board
        assert isinstance(self.__market_board__, jmMarketBoard)
        return self.__market_board__

    @property
    def info_board(self):
        from jetend.modules.jmInfoBoard import jmInfoBoard
        if AccountPosition.__info_board__ is None:
            from modules.Modules import Modules
            AccountPosition.__info_board__ = Modules.get_instance().info_board
        assert isinstance(self.__info_board__, jmInfoBoard)
        return self.__info_board__
