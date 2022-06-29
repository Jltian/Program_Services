# -*- encoding: UTF-8 -*-
import datetime

from jetend.structures import List
from jetend.jmSheets import RawTrusteeshipValuation

from sheets.Elements import AccountClass, Contract, Flowing, Trading
from utils.Constants import *


class EntryPositionMove(Contract, Flowing, Trading):
    """交易行为"""

    def __init__(self, product: str = '', date: datetime.date = None, institution: str = '',
                 security_name: str = '', security_code: str = '', security_type: str = '',
                 trade_direction: str = DIRECTION_NONE, trade_volume: float = None,
                 trade_price: float = None, trade_amount: float = None,
                 trade_offset: str = OFFSET_NONE, currency: str = ''):
        Contract.__init__(self, security_code=security_code, security_name=security_name)
        Flowing.__init__(self, product=product, date=date, institution=institution)
        Trading.__init__(
            self, trade_direction=trade_direction, trade_price=trade_price, trade_volume=trade_volume,
            trade_amount=abs(trade_amount), offset=trade_offset, currency=currency,
        )
        self.security_type = str_check(security_type)

        assert self.trade_volume > 0.0, str(self)
        assert self.trade_price >= 0.0, str(self)
        assert is_valid_str(self.currency), str(self)
        assert self.trade_direction in (DIRECTION_BUY, DIRECTION_SELL), str(self)

        if is_different_float(self.trade_amount, self.trade_price * self.trade_volume, gap=10):
            # def warning(self, message, category=None, stacklevel=1, source=None):
            #     import traceback
            #     for tb_info in traceback.extract_stack():
            #         assert isinstance(tb_info, traceback.FrameSummary)
            #         warnings.warn('[warning]: {} {} {}'.format(tb_info.filename, tb_info.lineno, tb_info.line))
            #     warnings.warn(message='[warning]: {}'.format(message), category=category, stacklevel=stacklevel,
            #                   source=source)
            if self.security_name != '财富宝E':#货币基金结转，当持仓不是财富宝E的时候，都验证一下以下代码。20220525 wavezhou
                raise RuntimeWarning('交易金额和交易数量 * 交易价格不一致 {}'.format(self))
            # self.env.warning()

    def __repr__(self):
        string_dict = dict()
        for k in Contract.inner2outer_map.keys():
            string_dict[k] = getattr(self, k)
        for k in Flowing.inner2outer_map.keys():
            string_dict[k] = getattr(self, k)
        for k in Trading.inner2outer_map.keys():
            string_dict[k] = getattr(self, k)
        return 'EntryPositionMove: ' + str(string_dict)

    @classmethod
    def init_from(cls, obj):
        from sheets.Elements import BaseInfo, TradeInfo
        assert isinstance(obj, (Contract, Flowing, Trading, BaseInfo, TradeInfo)), str(obj)
        assert obj.security_type in SECURITY_TYPE_RANGE or obj.security_type == '证券清算款', '{} {}'.format(
            obj.security_type, str(obj))
        return cls(
            security_type=obj.security_type,
            product=obj.product, date=obj.date, institution=obj.institution,
            security_code=obj.security_code, security_name=obj.security_name,
            trade_direction=obj.trade_direction, currency=obj.currency, trade_offset=obj.offset,
            trade_volume=obj.trade_volume, trade_price=obj.trade_price,
            trade_amount=obj.trade_amount,
        )

    @property
    def hash_key(self):
        return '|'.join([self.product.strip(), self.institution.strip(),
                         self.security_name.strip(), self.security_code.strip()])


class EntryPosition(AccountClass, Contract, Flowing):
    """
    会计产品持仓表
    """
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'account_code': '科目编号', 'account_name': '科目', 'security_name': '标的名称', 'security_code': '标的代码',
        'hold_volume': '持有数量', 'contract_multiplier': '合约乘数', 'weight_average_cost': '加权成本',
        'tax_cost': '计税成本', 'total_cost': '成本', 'close_price': '收盘价', 'market_value': '市值',
    }

    def __init__(
            self, product: str = '', date: datetime.date = None, institution: str = '',
            account_name: str = '', account_code: int = None,
            security_name: str = '', security_code: str = '',
            hold_volume: float = None, contract_multiplier: float = None,
            weight_average_cost: float = None, tax_cost: float = None,
            close_price: float = None, market_value: float = None, offset: str = None,
            total_cost: float = None,
            **kwargs,
    ):
        AccountClass.__init__(self, account_code=account_code, account_name=account_name)
        Contract.__init__(self, security_code=security_code, security_name=security_name)
        Flowing.__init__(self, product=product, date=date, institution=institution)
        self.hold_volume = round(float_check(hold_volume), 2)
        self.weight_average_cost = float_check(weight_average_cost)
        self.offset = str_check(offset)
        self.__contract_multiplier__ = float_check(contract_multiplier)
        self.__close_price__ = float_check(close_price)
        self.__market_value__ = float_check(market_value)
        self.__hash_key__ = str_check(kwargs.get('hash_key', None))
        if self.date == datetime.date(2017, 12, 31):
            self.tax_cost = max(float_check(weight_average_cost), self.close_price)
        else:
            self.tax_cost = float_check(tax_cost)
        self.total_cost = float_check(total_cost)

        self.last_date = None
        self.last_hold_volume = None
        self.last_close_price = None
        self.last_market_value = None
        self.last_weight_average_cost = None
        self.last_total_cost = None

        if abs(self.weight_average_cost * self.hold_volume - self.total_cost) > 0.01 * self.total_cost:
            raise RuntimeError(self)

    def init_to_next_date(self):
        self.last_weight_average_cost = self.weight_average_cost
        self.last_total_cost = self.total_cost
        self.last_hold_volume = self.hold_volume
        self.last_close_price = self.__close_price__
        self.last_contract_multiplier = self.__contract_multiplier__
        self.last_market_value = self.__market_value__
        self.last_date = self.date
        # 日期往后
        self.date += datetime.timedelta(days=1)
        self.__close_price__ = float_check(None)
        self.__market_value__ = float_check(None)

    @property
    def close_price(self):
        if not is_valid_float(self.__close_price__):
            self.__close_price__ = self.realtime_close_price
        return round(self.__close_price__, 8)

    @property
    def realtime_close_price(self):
        if abs(self.hold_volume) < 0.01:
            close_price = 0.0

        elif self.account_name == '证券清算款':
            if self.ipo_date <= self.date:
                raise RuntimeError('出现未转为正式持仓的申购持仓'.format(self))
            else:
                close_price = self.weight_average_cost

        elif self.account_name == '基金投资':
            if self.security_code in (
                    'ZhongHaiJM01', 'ST1188', 'S22497', 'PuRui01',
            ):
                raise NotImplementedError(self)
            elif self.institution == '久铭':
                if self.env.info_board.check_mandatory(self.security_name) is True or self.security_name == '稳健22号':
                    value_list = List.from_pd(RawTrusteeshipValuation, self.env.data_base.read_pd_query(
                        DataBaseName.management,
                        """
                        SELECT * FROM `原始托管估值表净值表` 
                        WHERE `日期` = (SELECT MAX(日期) FROM `原始托管估值表净值表` WHERE `日期` <= '{}')
                        ;""".format(self.date)
                    ))
                    try:
                        net_value = float(value_list.find_value(product=self.security_name).net_value)
                    except ValueError:
                        raise RuntimeError('日期 {} 缺少 {} 估值表信息.\n{}'.format(
                            value_list.collect_attr_set('date'), self.security_name, self.__dict_data__))
                else:
                    net_value = self.db.read_pd_query(
                        DataBaseName.management,
                        """SELECT 单位净值 FROM `会计凭证估值净值表` WHERE 日期 = '{}' AND 产品 = '{}';""".format(
                            self.date, self.security_name, )).loc[0, '单位净值']
                assert is_valid_float(net_value), '单位净值数据出错 {} {}'.format(self.security_name, self.date)
                return net_value
            else:
                raise NotImplementedError(self)

        elif self.account_name == '债券投资':
            close_price = self.env.wind_board.float_field('cleanprice', self.security_code, self.date, option='')

        elif self.account_name == '权证投资':
            close_price = self.env.wind_board.float_field(
                'settle', self.security_code, self.date, option='',
            ) * self.env.wind_board.float_field(
                'contractmultiplier', self.security_code, self.date, option=''
            )

        elif self.account_name == '买入返售金融资产':
            close_price = self.weight_average_cost
        elif self.account_name == '股票投资':
            try:
                close_price = self.env.wind_board.float_field('close', self.security_code, self.date, option='')
            except AssertionError:
                close_price = self.weight_average_cost
            if 'HK' in self.security_code.upper():
                close_price = close_price * self.env.wind_board.exchange_settle_rate('HKD', 'CNY', 'HKS', self.date)
        else:
            raise NotImplementedError(self.account_name)
        if not is_valid_float(close_price) and self.account_name == '股票投资':
            # 股票还未上市 用成本价作为市价
            ipo_date = self.market_board.ipo_date(self.account_name, self.security_code, self.date)
            if ipo_date is None:
                close_price = self.weight_average_cost
            elif ipo_date > self.date:
                close_price = self.weight_average_cost
            else:
                pass
        if not is_valid_float(close_price) and abs(self.hold_volume) < 0.1:
            close_price = math.nan
        if not is_valid_float(close_price) and abs(self.hold_volume) >= 0.1:
            print(self.product, self.date, self.institution, self.security_code, self.security_name,
                  self.hold_volume)
            raise RuntimeError
        assert is_valid_float(close_price)
        return close_price

    @property
    def ipo_date(self):
        return self.env.wind_board.ipo_date(self.security_code, self.date)

    @property
    def market_value(self):
        if not is_valid_float(self.__market_value__):
            # 处理自有基金的单位净值精度带来的市值差距问题
            self.__market_value__ = self.realtime_market_value
        if not is_valid_float(self.__market_value__) and self.account_name != '证券清算款':
            print(self.product, self.security_name, self.close_price)
            raise RuntimeError('no market value!')
        return round(self.__market_value__, 4)

    @property
    def realtime_market_value(self):
        # 处理自有基金的单位净值精度带来的市值差距问题
        if abs(self.hold_volume) < 0.01:
            return 0.0
        if self.account_name == '证券清算款':
            if self.ipo_date <= self.date:
                return self.hold_volume * self.close_price
            else:
                return self.__market_value__ if is_valid_float(self.__market_value__) else self.last_market_value
        elif self.account_name in ('股票投资', '基金投资', '债券投资', '权证投资', '应收利息'):
            if not is_valid_float(self.close_price):
                raise RuntimeError('{} {} {} {}'.format(
                    self.product, self.security_code, self.security_name, self.hold_volume))
            return self.hold_volume * self.close_price
        elif self.account_name == '买入返售金融资产':
            return self.hold_volume * self.weight_average_cost
        else:
            raise NotImplementedError(self.account_name)

    @property
    def realtime_value_added(self):
        return self.realtime_market_value - self.total_cost

    @property
    def hash_key(self):
        return '|'.join([
            self.product.strip(), self.institution.strip(),
            self.security_name.strip(), self.security_code.strip(),
        ])

    @classmethod
    def init_from_update(cls, trade: EntryPositionMove):
        try:
            account_number = {
                SECURITY_TYPE_STOCK: 1102,
                SECURITY_TYPE_BOND: 1103, SECURITY_TYPE_FUND: 1105, SECURITY_TYPE_OPTION: 1106,
                SECURITY_TYPE_FUTURE: 1106, SECURITY_TYPE_BOND_INTEREST: 1204,
                '证券清算款': 3003, SECURITY_TYPE_ASSET_BUY_BACK: 1202,
            }[trade.security_type]
        except KeyError:
            raise NotImplementedError('{} {}'.format(trade.security_type, str(trade)))
        new_cls = cls(
            product=trade.product, date=trade.date, institution=trade.institution, account_code=account_number,
            security_code=trade.security_code, security_name=trade.security_name,
            hold_volume=trade.trade_volume, weight_average_cost=trade.trade_price, tax_cost=trade.trade_price,
            total_cost=trade.trade_amount,
            contract_multiplier=1.0,
            # currency=trade.currency
        )
        new_cls.last_hold_volume = new_cls.hold_volume
        new_cls.last_total_cost = new_cls.total_cost
        new_cls.last_close_price = new_cls.weight_average_cost
        new_cls.last_market_value = new_cls.total_cost
        new_cls.last_date = new_cls.date
        return new_cls

    def update_from(self, data):
        assert isinstance(data, EntryPositionMove)
        assert data.date == self.date, '{}\n{}'.format(data, self)
        assert data.currency == 'RMB', str(data)
        if data.trade_direction == DIRECTION_BUY:
            # 融券卖空后买回
            if self.hold_volume < 0:
                assert '两融' in self.institution, str(self)
                self.total_cost = self.total_cost * (1.0 + data.trade_volume / self.hold_volume)
                self.hold_volume += data.trade_volume
                # 调整持仓小于0.1的计算误差
                if self.hold_volume < 0:
                    if abs(self.hold_volume) < 0.1:
                        self.hold_volume = 0.0
                    else:
                        raise ValueError('rest:{} {}'.format(self.hold_volume, str(data)))
                raise RuntimeError(self)
            # 正常买入
            else:
                self.hold_volume += data.trade_volume
                self.total_cost += data.trade_amount
                self.weight_average_cost = self.total_cost / self.hold_volume
                self.tax_cost = self.total_cost / self.hold_volume
        elif data.trade_direction == DIRECTION_SELL:
            # 融券卖空
            if self.hold_volume <= 0:
                assert '两融' in self.institution, str(self)
                self.hold_volume -= data.trade_volume
                self.total_cost -= data.trade_amount
                self.weight_average_cost = self.total_cost / self.hold_volume
                self.tax_cost = self.total_cost / self.hold_volume
                raise RuntimeError(self)
            # 正常卖出
            else:
                self.total_cost = self.total_cost * (1.0 - data.trade_volume / self.hold_volume)
                self.hold_volume -= data.trade_volume
                # 调整持仓小于0.1的计算误差
                if self.hold_volume < 0:
                    if abs(self.hold_volume) < 0.1:
                        self.hold_volume = 0.0
                    else:
                        raise ValueError('rest:\n{}\n{}\n{}'.format(self.hold_volume, self, str(data)))
        else:
            raise RuntimeError
        assert is_valid_float(self.weight_average_cost), '\n{}\n{}'.format(data, str(self.__data__))
        assert is_valid_float(self.tax_cost)
        assert is_valid_float(self.hold_volume)

    @property
    def lastday_total_cost(self):
        return self.last_total_cost

    @property
    def tax_cost(self):
        return round(self.__data__.get('tax_cost'), 8)

    @tax_cost.setter
    def tax_cost(self, value):
        self.__data__.__setitem__('tax_cost', value)

    @property
    def weight_average_cost(self):
        return round(self.__data__.get('weight_average_cost'), 8)

    @weight_average_cost.setter
    def weight_average_cost(self, value):
        self.__data__.__setitem__('weight_average_cost', value)

    @property
    def contract_multiplier(self):
        return float_check(self.__contract_multiplier__)
