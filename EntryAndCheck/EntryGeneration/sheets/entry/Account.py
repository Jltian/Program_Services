# -*- encoding: UTF-8 -*-
import datetime

from sheets.Elements import AccountClass, BaseInfo
from utils.Constants import *

from jetend.DataCheck import *


class EntryAccount(AccountClass, BaseInfo):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'account_name': '科目名称', 'account_code': '科目代码',
        'sub_account': '二级科目', 'base_account': '三级科目', 'note_account': '四级科目',
        'start_net_value': '期初净额', 'debit_amount_move': '本期借方发生额',
        'credit_amount_move': '本期贷方发生额', 'net_value': '期末净额',
    }

    @property
    def sub_account(self):
        """二级科目"""
        return str_check(self.get_attr('sub_account'))

    @property
    def base_account(self):
        """三级科目"""
        return str_check(self.get_attr('base_account'))

    @property
    def note_account(self):
        """四级科目"""
        return str_check(self.get_attr('note_account'))

    @property
    def institution(self):
        raise RuntimeError('会计科目没有institution属性')

    @property
    def realtime_net_value(self):
        return self.start_net_value + self.debit_amount_move - self.credit_amount_move

    def init_to_next_date(self):
        # 日期往后挪移一天
        self.set_attr('date', self.date + datetime.timedelta(days=1))
        # 当日借贷发生额清空
        self.set_attr('debit_amount_move', 0.0)
        self.set_attr('credit_amount_move', 0.0)
        # 当日期末余额转入下日期初余额
        self.set_attr('start_net_value', self.net_value)

    @classmethod
    def init_from(cls, entry):
        from sheets.entry.Entry import JournalEntry
        assert isinstance(entry, JournalEntry)
        return cls(
            product=entry.product, date=entry.date, account_code=entry.account_code, account_name=entry.account_name,
            sub_account=entry.account_level_2, base_account=entry.account_level_3, note_account=entry.account_level_4,
            start_net_value=0.0, debit_amount_move=0.0, credit_amount_move=0.0, net_value=0.0,
        ).update_by(entry)

    def update_by(self, entry):
        # from sheets.entry.Entry import JournalEntry
        # assert isinstance(entry, JournalEntry)
        # 检查科目和凭证是否匹配
        assert self.product == entry.product, '{}\n{}'.format(self, entry)
        assert self.account_name == entry.account_name, '{}\n{}'.format(self, entry)
        assert self.date == entry.date, '{}\n{}'.format(self, entry)
        if is_valid_str(self.sub_account):
            assert is_valid_str(entry.account_level_2), str(entry)
            if self.sub_account == entry.account_level_2:
                pass
            elif self.sub_account in entry.account_level_2 or entry.account_level_2 in self.sub_account:
                pass
            else:
                raise RuntimeError('{}\n{}'.format(self, entry))
        if is_valid_str(self.base_account):
            assert is_valid_str(entry.account_level_3), '{}\n{}'.format(self, entry)
            if self.base_account == entry.account_level_3:
                pass
            else:
                if self.base_account in entry.account_level_3 or entry.account_level_3 in self.base_account:
                    pass
                else:
                    raise RuntimeError('{}\n{}'.format(self, entry))
        if is_valid_str(self.note_account):
            assert is_valid_str(entry.account_level_4), '{}\n{}'.format(self, entry)
            if self.note_account == entry.account_level_4:
                pass
            else:
                if self.note_account in entry.account_level_4 or entry.account_level_4 in self.note_account:
                    pass
                else:
                    raise RuntimeError('{}\n{}'.format(self, entry))
        assert is_valid_float(self.start_net_value), '科目没有经过初始化 {}'.format(self)
        # 更新科目
        if entry.debit_credit == SIDE_DEBIT_CN:
            self.set_attr('debit_amount_move', self.get_attr('debit_amount_move') + entry.amount)
        elif entry.debit_credit == SIDE_CREDIT_CN:
            self.set_attr('credit_amount_move', self.get_attr('credit_amount_move') + entry.amount)
        else:
            raise RuntimeError('Unknown DEBIT/CREDIT {}'.format(entry))
        self.set_attr('net_value', self.start_net_value + self.debit_amount_move - self.credit_amount_move)
        return self

    @property
    def hash_key(self):
        return '|'.join([
            self.product.strip(), self.account_name.strip(),
            self.sub_account.strip(), self.base_account.strip(),
        ])

    @property
    def debit_amount_move(self):
        return round(self.get_attr('debit_amount_move'), 4)

    @property
    def credit_amount_move(self):
        return round(self.get_attr('credit_amount_move'), 4)

    @property
    def net_value(self):
        return round(self.get_attr('net_value'), 2)
