# -*- encoding: UTF-8 -*-
import datetime

from jetend.structures import List
from jetend.DataCheck import *

from sheets.Elements import AccountClass, BaseInfo
from sheets.entry.Entry import JournalEntry
from utils.Constants import *


class EntryAccount(AccountClass, BaseInfo):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'account_name': '科目名称', 'account_code': '科目代码',
        'sub_account': '二级科目', 'base_account': '三级科目', 'note_account': '四级科目',
        'start_net_value': '期初净额', 'debit_amount_move': '本期借方发生额',
        'credit_amount_move': '本期贷方发生额', 'net_value': '期末净额',
    }

    def init_to_next_date(self):
        # 日期往后挪移一天
        self.set_attr('date', self.date + datetime.timedelta(days=1))
        # 当日借贷发生额清空
        self.set_attr('debit_amount_move', 0.0)
        self.set_attr('credit_amount_move', 0.0)
        # 当日期末余额转入下日期初余额
        self.set_attr('start_net_value', self.net_value)

    def update_by(self, entry):
        from sheets.entry.Entry import JournalEntry
        assert isinstance(entry, JournalEntry)
        # 检查科目和凭证是否匹配
        assert self.product == entry.product, '{}\n{}'.format(self, entry)
        assert self.account_name == entry.account_name, '{}\n{}'.format(self, entry)
        assert self.date == entry.date, '{}\n{}'.format(self, entry)
        # if is_valid_str(self.sub_account):
        #     assert is_valid_str(entry.account_level_2), str(entry)
        #     if self.sub_account == entry.account_level_2:
        #         pass
        #     elif self.sub_account in entry.account_level_2 or entry.account_level_2 in self.sub_account:
        #         pass
        #     else:
        #         raise RuntimeError('{}\n{}'.format(self, entry))
        # if is_valid_str(self.base_account):
        #     assert is_valid_str(entry.account_level_3), '{}\n{}'.format(self, entry)
        #     if self.base_account == entry.account_level_3:
        #         pass
        #     else:
        #         if self.base_account in entry.account_level_3 or entry.account_level_3 in self.base_account:
        #             pass
        #         else:
        #             raise RuntimeError('{}\n{}'.format(self, entry))
        # if is_valid_str(self.note_account):
        #     assert is_valid_str(entry.account_level_4), '{}\n{}'.format(self, entry)
        #     if self.note_account == entry.account_level_4:
        #         pass
        #     else:
        #         if self.note_account in entry.account_level_4 or entry.account_level_4 in self.note_account:
        #             pass
        #         else:
        #             raise RuntimeError('{}\n{}'.format(self, entry))
        # assert is_valid_float(self.start_net_value), '科目没有经过初始化 {}'.format(self)
        # 更新科目
        if entry.debit_credit == SIDE_DEBIT_CN:
            self.set_attr('debit_amount_move', self.get_attr('debit_amount_move') + entry.amount)
        elif entry.debit_credit == SIDE_CREDIT_CN:
            self.set_attr('credit_amount_move', self.get_attr('credit_amount_move') + entry.amount)
        else:
            raise RuntimeError('Unknown DEBIT/CREDIT {}'.format(entry))
        self.set_attr('net_value', self.start_net_value + self.debit_amount_move - self.credit_amount_move)
        return self


class EntryAccountList(List):
    def __init__(self, *args, **kwargs):
        List.__init__(self, *args, **kwargs)

    def update_by_entry(self, entry: JournalEntry):
        """根据会计凭证更新科目余额"""
        acc_list = self.find_value_where(
            product=entry.product, date=entry.date, account_name=entry.account_name,
        )
        try:
            acc = acc_list.find_value(
                sub_account=entry.account_level_2, base_account=entry.account_level_3,
                note_account=entry.account_level_4,
            )
            acc.update_by(entry)
            print('{}'.format(acc))
        except ValueError:
            if entry.is_force_match is True:
                raise NotImplementedError('{}'.format(entry))
            else:
                acc = EntryAccount(
                    product=entry.product, date=entry.date,
                    account_name=entry.account_name, sub_account=entry.account_level_2,
                    base_account=entry.account_level_3, note_account=entry.account_level_4,
                    start_net_value=0.0, net_value=0.0, debit_amount_move=0.0, credit_amount_move=0.0,
                )
                acc.update_by(entry)
                print('{}'.format(acc))
                self.append(acc)

    def update_by_entry_old_version(self, entry: JournalEntry):
        """根据会计凭证更新科目余额 20190531 前使用"""

        product_acc_list = self.find_value_where(
            product=entry.product, date=entry.date, account_name=entry.account_name,
        )

        if entry.account_name in (              # 凭证为一级科目
                '应付管理人报酬', '实收基金',
        ):
            assert not is_valid_str(entry.account_level_2) and not is_valid_str(entry.account_level_3), str(entry)
            try:
                product_acc_list.find_value(sub_account='', base_account='').update_by(entry)
            except ValueError:
                self.append(EntryAccount(
                    product=entry.product, date=entry.date,
                    account_name=entry.account_name, sub_account='', base_account='',
                    start_net_value=0.0, net_value=0.0, debit_amount_move=0.0, credit_amount_move=0.0,
                ).update_by(entry))

        elif entry.account_name in (            # 凭证为二级科目
                '存出保证金', '结算备付金', '银行存款', '其他应付款', '管理人报酬', '预估税金及附加', '税金及附加',
                '其他费用', '交易费用', '损益平准金', '应付赎回款', '短期借款',
        ):
            assert is_valid_str(entry.account_level_2) and not is_valid_str(entry.account_level_3), str(entry)

            this_acc = None
            for acc in product_acc_list:
                assert isinstance(acc, EntryAccount)
                assert is_valid_str(acc.sub_account) and not is_valid_str(acc.base_account), str(acc)
                if acc.sub_account == entry.account_level_2:
                    this_acc = acc
                    break
                elif acc.sub_account in entry.account_level_2 or entry.account_level_2 in acc.sub_account:
                    this_acc = acc
                    break
                else:
                    pass
            if isinstance(this_acc, EntryAccount):
                this_acc.update_by(entry)
            else:
                sub_acc = EntryAccount(
                    product=entry.product, date=entry.date, account_name=entry.account_name,
                    sub_account=entry.account_level_2, base_account='',
                    start_net_value=0.0, net_value=0.0, debit_amount_move=0.0, credit_amount_move=0.0,
                )
                sub_acc.update_by(entry)
                self.append(sub_acc)

        # 凭证为三级科目
        elif entry.account_name in (
                '股票投资', '债券投资', '基金投资', '权证投资', '应收利息', '其他应收款', '应付利息', '公允价值变动损益',
                '利息收入', '利息支出', '预提费用', '应交税费', '投资收益', '应收股利',
        ):
            assert is_valid_str(entry.account_level_2) and is_valid_str(entry.account_level_3), str(entry)
            target_acc_list = product_acc_list.find_value_where(sub_account=entry.account_level_2)
            this_acc = None
            for acc in target_acc_list:
                assert isinstance(acc, EntryAccount)
                if not is_valid_str(acc.base_account):
                    raise RuntimeError(str(acc))
                if acc.base_account == entry.account_level_3:
                    this_acc = acc
                    break
                elif acc.base_account in entry.account_level_3 or entry.account_level_3 in acc.base_account:
                    this_acc = acc
                    break
                else:
                    pass
            if isinstance(this_acc, EntryAccount):
                this_acc.update_by(entry)
            else:
                new_acc = EntryAccount(
                    product=entry.product, date=entry.date,
                    account_name=entry.account_name, sub_account=entry.account_level_2,
                    base_account=entry.account_level_3,
                    debit_amount_move=0.0, credit_amount_move=0.0, start_net_value=0.0, net_value=0.0,
                ).update_by(entry)
                self.append(new_acc)
        else:
            raise RuntimeError('未知凭证科目 {}\n{}'.format(entry.account_name, entry))
