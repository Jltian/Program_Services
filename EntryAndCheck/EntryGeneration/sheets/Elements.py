# -*- encoding: UTF-8 -*-
import datetime

from structures.DataObject import DataObject
from utils.Constants import *

from jetend.Interface import AttributeObject


class Contract(DataObject):
    """合约要素"""
    inner2outer_map = {
        'security_code': 'security_code', 'security_name': 'security_name'
    }

    def __init__(self, security_code: str = '', security_name: str = ''):
        DataObject.__init__(self)
        self.security_code = str_check(security_code)
        self.security_name = str_check(security_name)

    @property
    def security_code_name(self):
        security_code_name = self.__data__.get('security_code_name', None)
        if is_valid_str(self.security_code) and not is_valid_str(security_code_name):
            security_code_name = '{}|{}'.format(self.security_code, self.security_name)
        return security_code_name

    @security_code_name.setter
    def security_code_name(self, value):
        self.__data__.__setitem__('security_code_name', str_check(value))


class BaseInfo(AttributeObject):
    __env__ = None

    @property
    def product(self):
        product = str_check(self.get_attr('product'))
        assert is_valid_str(product), str(self.__dict__)
        return product

    @property
    def date(self):
        date = date_check(self.get_attr('date'))
        assert isinstance(date, datetime.date), str(self.__dict__)
        return date

    @property
    def institution(self):
        institution = str_check(self.get_attr('institution'))
        assert is_valid_str(institution), str(self.__dict__)
        return institution

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.date, account_level_5=getattr(self, 'security_code_name', '')
        )

    @property
    def env(self):
        from core.Environment import Environment
        if DataObject.__env__ is None:
            DataObject.__env__ = Environment.get_instance()
        assert isinstance(DataObject.__env__, Environment)
        return DataObject.__env__


class EntryGenerable:

    def generate_journal_entry(self):
        raise NotImplementedError(self)


class Flowing(DataObject):
    """流水要素"""
    security_type = None
    inner2outer_map = {
        'product': 'product', 'date': 'date', 'institution': 'institution',
    }

    def __init__(self, product: str = None, date: datetime.date = None, institution: str = '',):
        DataObject.__init__(self)
        self.product, self.date = product, date
        self.__data__.__setitem__('institution', str_check(institution))

    def __ggje__(self):
        """__generate_general_journal_entry__ 生成JournalEntry，为上个函数服务"""
        from sheets.entry.Entry import JournalEntry
        return JournalEntry(
            product=self.product, date=self.date, account_level_5=getattr(self, 'security_code_name', '')
        )

    @property
    def hash_key(self):
        raise NotImplementedError

    @property
    def product(self):
        product = self.__data__.get('product', None)
        if product is None:
            raise RuntimeError('产品信息遗失！：\n{}\n{}'.format(self.__class__.__name__, self.__data__))
        assert isinstance(product, str)
        return product

    @product.setter
    def product(self, value):
        self.__data__.__setitem__('product', str_check(value))

    @property
    def date(self):
        date = self.__data__.get('date', None)
        if date is None:
            raise RuntimeError('日期信息遗失！：\n{}\n{}'.format(self.__class__.__name__, self.__data__))
        assert isinstance(date, datetime.date), str(self.__data__)
        return date

    @date.setter
    def date(self, value):
        self.__data__.__setitem__('date', date_check(value))

    @property
    def institution(self):
        institution = self.__data__.get('institution', None)
        if not is_valid_str(institution):
            print(type(institution))
            raise RuntimeWarning('机构信息遗失！:\n{}\n{}'.format(self.__class__.__name__, self.__data__))
        return institution

    @institution.setter
    def institution(self, value):
        self.__data__.__setitem__('institution', str_check(value))


class SecurityInfo(AttributeObject):
    """合约要素"""

    @property
    def security_code(self):
        security_code = str_check(self.get_attr('security_code'))
        assert is_valid_str(security_code), str(self.__dict__)
        return security_code

    @property
    def security_name(self):
        security_name = str_check(self.get_attr('security_name'))
        assert is_valid_str(security_name), str(self.__dict__)
        return security_name

    @property
    def security_code_name(self):
        return '{}|{}'.format(self.security_code, self.security_name)


class TradeInfo(AttributeObject):
    """交易信息要素"""

    @property
    def trade_direction(self):
        trade_direction = str_check(self.get_attr('trade_direction'))
        assert is_valid_str(trade_direction), str(self.__dict__)
        return trade_direction

    @property
    def offset(self):
        offset = str_check(self.get_attr('offset'))
        assert is_valid_str(offset), str(self.__dict__)
        return offset

    @property
    def trade_price(self):
        trade_price = abs(float_check(self.get_attr('trade_price')))
        assert is_valid_float(trade_price), str(self.__dict__)
        return trade_price

    @property
    def trade_volume(self):
        trade_volume = abs(float_check(self.get_attr('trade_volume')))
        assert is_valid_float(trade_volume), str(self.__dict__)
        return trade_volume

    @property
    def trade_amount(self):
        trade_amount = abs(float_check(self.get_attr('trade_amount')))
        assert is_valid_float(trade_amount), str(self.__dict__)
        return trade_amount

    @property
    def cash_move(self):
        cash_move = float_check(self.get_attr('cash_move'))
        assert is_valid_float(cash_move), str(self.__dict__)
        return cash_move

    @property
    def currency(self):
        currency = str_check(self.get_attr('currency'))
        assert is_valid_str(currency), str(self.__dict__)
        return currency


class Trading(DataObject):
    """交易要素"""
    inner2outer_map = {
        'trade_direction': 'trade_direction', 'offset': 'offset', 'trade_volume': 'trade_volume',
        'cash_move': 'cash_move', 'trade_price': 'trade_price', 'trade_amount': 'trade_amount',
        'currency': 'currency',
    }

    def __init__(self, trade_direction: str = '', offset: str = '',
                 trade_volume: float = None, cash_move: float = None,
                 trade_price: float = None, trade_amount: float = None,
                 currency: str = '', ):
        DataObject.__init__(self)
        self.trade_direction = str_check(trade_direction)
        self.offset = str_check(offset)
        self.trade_price = float_check(trade_price)
        self.trade_volume = float_check(trade_volume)
        self.trade_amount = float_check(trade_amount)
        self.cash_move = float_check(cash_move)
        self.currency = str_check(currency)

    @property
    def trade_price(self):
        return abs(self.__data__.get('trade_price'))

    @trade_price.setter
    def trade_price(self, value):
        self.__data__.__setitem__('trade_price', float_check(value))

    @property
    def trade_volume(self):
        return abs(self.__data__.get('trade_volume'))

    @trade_volume.setter
    def trade_volume(self, value):
        self.__data__.__setitem__('trade_volume', float_check(value))

    @property
    def trade_amount(self):
        return abs(self.__data__.get('trade_amount'))

    @trade_amount.setter
    def trade_amount(self, value):
        self.__data__.__setitem__('trade_amount', float_check(value))


class AccountClass(AttributeObject):

    @property
    def account_code(self):
        """会计编号 -> int"""
        account_code = int_check(self.get_attr('account_code'))
        if isinstance(account_code, int):
            return account_code
        else:
            try:
                return ACCOUNT_NAME_CODE_MAP[self.account_name]
            except KeyError as error_key:
                print(self)
                raise error_key

    @account_code.setter
    def account_code(self, value):
        self.__setattr__('account_code', int_check(value))

    @property
    @depreciated_method('account_code')
    def account_number(self):
        return self.account_code

    @property
    def account_name(self):
        account_name = str_check(self.get_attr('account_name'))
        if not is_valid_str(account_name):
            account_code = self.account_code
            assert isinstance(account_code, int), str(self.__dict__)
            for key, value in ACCOUNT_NAME_CODE_MAP.items():
                if value == account_code:
                    account_name = key
        else:
            pass
        assert is_valid_str(account_name), '{} {}'.format(self.__class__.__name__, self.__dict__)
        return account_name

    @account_name.setter
    def account_name(self, value):
        self.set_attr('account_name', str_check(value))

    @property
    @depreciated_method('account_name')
    def account(self):
        return self.account_name


class ValueAddedTaxInfo(AttributeObject):

    @property
    def vat(self):
        vat = float_check(self.get_attr('vat'))
        assert is_valid_float(vat), str(self.__dict__)
        return round(vat, 4)

    @property
    def building_tax(self):
        building_tax = float_check(self.get_attr('building_tax'))
        if is_valid_float(building_tax):
            return round(building_tax, 4)
        else:
            return round(self.vat * TAX_RATE_BT, 4)

    @property
    def education_surcharge(self):
        education_surcharge = float_check(self.get_attr('education_surcharge'))
        if is_valid_float(education_surcharge):
            return round(education_surcharge, 4)
        else:
            return round(self.vat * TAX_RATE_ES, 4)

    @property
    def local_education_surcharge(self):
        local_education_surcharge = float_check(self.get_attr('local_education_surcharge'))
        if is_valid_float(local_education_surcharge):
            return round(local_education_surcharge, 4)
        else:
            return round(self.vat * TAX_RATE_LES, 4)

    @property
    def total_tax(self):
        total_tax = float_check(self.get_attr('total_tax'))
        if is_valid_float(total_tax):
            return total_tax
        else:
            return self.vat + self.building_tax + self.education_surcharge + self.local_education_surcharge
