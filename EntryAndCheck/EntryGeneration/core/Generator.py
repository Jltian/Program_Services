# -*- encoding: UTF-8 -*-
import os
import datetime

from jetend.structures import List
from jetend.jmSheets import RawTrusteeshipValuation

from structures import DataList, EventObject, EventType
from sheets.entry.Account import EntryAccount
from sheets.entry.Position import EntryPosition, EntryPositionMove
from sheets.flowing.BankFlow import BankFlowing
from sheets.flowing.BondFlow import BondFlowing
from sheets.flowing.DailyValueAddedFlow import DailyValueAddedFlowing
from sheets.flowing.DividendFlow import DividendFlowing
from sheets.flowing.FundFlow import FundConfirmFlow
from sheets.flowing.FutureFlow import FutureFlowing
from sheets.flowing.InterestsFlow import InterestsFlow, BondIntersetsFlow
from sheets.flowing.ManagementFee import ManagementFeePayableFlow, ManagementFeeReceivableFlow
from sheets.flowing.MarginFlow import MarginFlow
from sheets.flowing.OptionFlow import OptionFlowing
from sheets.flowing.StockFlow import StockFlowing
from sheets.flowing.SwapFlow import SwapFlow, ModifyFlowing
from sheets.flowing.TaFlow import TaConfirmFlow
from sheets.flowing.VATBondInterests import VATBondInterests
from sheets.flowing.VATPaid import VATPaid
from sheets.flowing.VATTransaction import VATTransaction
from sheets.flowing.VATWithholding import VATWithholding, VATSum
from sheets.Information import DividendInfo
from sheets.Information import InterestRate
from utils.Constants import *


class EntryGenerator(object):
    def __init__(self, date: datetime.date):
        from core.Environment import Environment
        from sheets.entry.Entry import JournalEntry
        self.env = Environment.get_instance()
        self.info_board = self.env.info_board

        self.current_date = date
        self.last_date = date - datetime.timedelta(days=1)

        # ---- [set before using, update with flowing] ---- #
        self.positions = DataList(EntryPosition)  # 持仓信息储存
        self.accounts = DataList(EntryAccount)  # 存借款余额

        # ---- [data to running] ---- #
        self.bank_flow_list = DataList(BankFlowing)  # 银行流水
        self.stock_flow_list = DataList(StockFlowing)  # 股票流水
        self.bond_flow_list = DataList(BondFlowing)
        self.future_flow_list = DataList(FutureFlowing)  # 期货流水
        self.option_flow_list = DataList(OptionFlowing)

        # ---- [data to store] ---- #
        self.journal_entry_list = DataList(JournalEntry)  # 分录凭证记录列表

        self.vat_interests_list = DataList(VATBondInterests)  # 利息增值税记录列表
        self.vat_paid_list = DataList(VATPaid)  # 已付增值税记录列表
        self.vat_transaction_list = DataList(VATTransaction)  # 价差收入增值税记录列表
        self.vat_withholding_list = DataList(VATWithholding)  # 预提增值税记录列表
        self.today_vat_sum_list = DataList(VATSum)  # 当日增值税汇总情况
        self.lastday_vat_sum_list = DataList(VATSum)

        # ---- [set before using] ---- #
        self.__logger__ = None

        self.register_operations()  # 注册预定处理方案
        self.__load_support__()

    @property
    def log(self):
        from jetend import get_logger
        if self.__logger__ is None:
            self.__logger__ = get_logger(self.__class__.__name__, os.path.join(
                self.env.root_path(), 'temp', '{} {}'.format(self.__class__.__name__, self.current_date)))
        return self.__logger__

    def register_operations(self):
        self.env.event_engine.register(EventType.VATGen, self.__vat_generate_collection_process__)
        self.env.event_engine.register(EventType.PositionUpdate, self.__position_update_process__)
        self.env.event_engine.register(EventType.AccountUpdate, self.__account_update_process__)

    def __load_support__(self):
        self.positions = DataList(EntryPosition)
        for pos in DataList.from_pd(EntryPosition, self.env.data_base.read_pd_query(
                DataBaseName.management,
                """SELECT * FROM `会计产品持仓表` WHERE `日期` = '{}';""".format(self.last_date)
        )):
            assert isinstance(pos, EntryPosition)
            if abs(pos.hold_volume) < 0.01:
                continue
            else:
                pos.init_to_next_date()
                self.positions.append(pos)

        self.accounts = DataList(EntryAccount)
        for acc in DataList.from_pd(EntryAccount, self.env.data_base.read_pd_query(
                DataBaseName.management,
                """SELECT * FROM `会计科目余额表` WHERE `日期` = '{}';""".format(self.last_date)
        )):
            assert isinstance(acc, EntryAccount)
            acc.init_to_next_date()
            if abs(acc.start_net_value) < 0.01:
                continue
            self.accounts.append(acc)

        self.bank_flow_list = DataList.from_pd(BankFlowing, self.env.data_base.read_pd_query(
            DataBaseName.journal,
            """SELECT * FROM `{}` WHERE `日期` = '{}';""".format('银行标准流水', self.current_date)
        ))
        bank_flow_other_list = DataList(BankFlowing)
        for obj in self.bank_flow_list:
            assert isinstance(obj, BankFlowing)
            if is_valid_str(obj.comment):
                if obj.tag_program == '跳过':
                    continue
                if obj.comment == '内部' and obj.trade_class == '申购':
                    assert is_valid_str(obj.opposite) and not is_valid_str(obj.subject), str(obj)
                    assert obj.trade_amount > 0, str(obj)
                    if obj.opposite not in self.env.product_range:
                        continue
                    institution = self.accounts.find_value(product=obj.opposite, account_name='银行存款').sub_account
                    bank_flow_other_list.append(BankFlowing(
                        product=obj.opposite, date=obj.date, institution=institution,
                        trade_class='基金投资', opposite='久铭', subject=obj.product,
                        trade_amount=-abs(obj.trade_amount),
                    ))
                elif obj.comment == '内部' and obj.trade_class == '赎回':
                    assert is_valid_str(obj.opposite) and not is_valid_str(obj.subject), str(obj)
                    assert obj.trade_amount < 0, str(obj)
                    if obj.opposite not in self.env.product_range:
                        continue
                    institution = self.accounts.find_value(product=obj.opposite, account_name='银行存款').sub_account
                    bank_flow_other_list.append(BankFlowing(
                        product=obj.opposite, date=obj.date, institution=institution,
                        trade_class='基金投资', opposite='久铭', subject=obj.product,
                        trade_amount=abs(obj.trade_amount),
                    ))
                elif obj.comment == '内部' and obj.trade_class == '托管户互转':
                    continue
                elif obj.comment == '内部' and obj.trade_class == '份额转换':
                    if obj.opposite not in self.env.product_range:
                        continue
                    institution = self.accounts.find_value(product=obj.opposite, account_name='银行存款').sub_account
                    bank_flow_other_list.append(BankFlowing(
                        product=obj.opposite, date=obj.date, institution=institution,
                        trade_class='份额转换', opposite=obj.product, trade_amount=-obj.trade_amount,
                    ))
                elif obj.comment == '内部' and obj.trade_class == '份额转换差额':
                    if obj.opposite not in self.env.product_range:
                        continue
                    institution = self.accounts.find_value(product=obj.opposite, account_name='银行存款').sub_account
                    bank_flow_other_list.append(BankFlowing(
                        product=obj.opposite, date=obj.date, institution=institution,
                        trade_class='份额转换差额', opposite=obj.product, trade_amount=-obj.trade_amount,
                    ))
                else:
                    if obj.product not in self.env.product_range and obj.opposite not in self.env.product_range:
                        continue
                    else:
                        raise NotImplementedError(obj)
        self.bank_flow_list.extend(bank_flow_other_list)

        self.stock_flow_list = DataList.from_pd(StockFlowing, self.env.data_base.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `原始普通流水记录` WHERE `日期` = '{}'
            AND `证券代码` NOT IN (SELECT `合约识别代码` FROM `证券代码名称规整表` WHERE `类型` = '债券投资')
            ;""".format(self.current_date)
        ))

        self.bond_flow_list = DataList.from_pd(BondFlowing, self.env.data_base.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `原始普通流水记录` 
            WHERE `日期` = '{}' AND `证券代码` NOT IN (
                SELECT `合约识别代码` FROM `证券代码名称规整表` WHERE `类型` = '股票投资' or `类型` = '证券清算款')
            ;""".format(self.current_date)
        ))

        self.future_flow_list = DataList.from_pd(FutureFlowing, self.env.data_base.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `{}` WHERE `日期` = '{}';""".format('原始期货流水记录', self.current_date)
        ))

        self.option_flow_list = DataList.from_pd(OptionFlowing, self.env.data_base.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `{}` WHERE `日期` = '{}';""".format('原始期权流水记录', self.current_date)
        ))

        self.lastday_vat_sum_list = DataList.from_pd(VATSum, self.env.data_base.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `{}` WHERE `日期` = '{}';""".format('增值税备查簿_预估余额', self.last_date)
        ))

    def __derive_table_data_on_date__(self, obj_type: type, table_name: str, date: datetime.date, product: str):
        return DataList.from_pd(obj_type, self.env.data_base.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `{}` WHERE `日期` = '{}' AND `产品` = '{}';""".format(table_name, date, product)
        ))

    def run_product(self, product: str):
        print(self)
        self.log.info_running('运行分录凭证 {} 当前日期 {} 前一日期 {}'.format(product, self.current_date, self.last_date))

        self.log.info_running('管理费返还', '生成分录凭证')
        # WARNING: 取决于产品持仓明细表，持仓和市值有误这部分就有误，产品持仓明细只有
        if self.current_date.year % 4 == 0:
            DAYS_ONE_YEAR = 366
        else:
            DAYS_ONE_YEAR = 365
        mf_rec_list = DataList(ManagementFeeReceivableFlow)
        for pos in self.positions.find_value_where(product=product):
            assert isinstance(pos, EntryPosition)
            if pos.institution != '久铭':
                continue
            mf_rec_list.append(ManagementFeeReceivableFlow(
                investor=pos.product, date=self.current_date, invested=pos.security_name,
                fee_return=round(pos.last_market_value * self.info_board.find_product_management_return_rate(
                    pos.product, pos.security_name, self.current_date) / DAYS_ONE_YEAR, 2), ))
        self.generate_journal_entry(mf_rec_list)

        self.log.info_running('申赎确认', '生成分录凭证, 更新持仓表，前一日申赎确认单')
        if product == '稳健18号':
            print("ssgsdg")
        data_list = DataList.from_pd(TaConfirmFlow, self.env.data_base.read_pd_query(
            DataBaseName.transfer_agent_new,
            """
            SELECT b.`name` as 投资人, b.`type` as 业务类型, b.`date` as 日期, a.`产品简称` as 产品, 
                b.`amount` as 资金数目, b.`netvalue` as 单位净值, b.`share` as 基金份额, b.`confirmation_date` as 确认日
            FROM `最新产品要素表` a, `申赎流水表` b
            WHERE b.`product_name` = a.`产品全称` AND `confirmation_date` = '{}' AND a.`产品简称` = '{}'
            ;""".format(self.current_date, product)
        ))
        self.generate_journal_entry(data_list)

        data_list = DataList.from_pd(FundConfirmFlow, self.env.data_base.read_pd_query(
            DataBaseName.transfer_agent_new,
            """
            SELECT a.`产品简称` as name, b.`type`, b.`date`, c.`产品简称` as product_name, c.`产品代码` as security_code,
                b.`amount`, b.`netvalue`, b.`share`, b.`confirmation_date`, '久铭' as institution, 'RMB' as currency
            FROM `最新产品要素表` a, `申赎流水表` b, `最新产品要素表` c 
            WHERE b.`name` = a.`产品全称` and b.`product_name` = c.`产品全称`
                AND b.`confirmation_date` = '{}' AND a.`产品简称` = '{}'
            ;""".format(self.current_date, product),
        ))
        self.generate_journal_entry(data_list)

        self.log.info_running('管理费计提', '生成分录凭证')
        if self.current_date.year % 4 == 0:
            DAYS_ONE_YEAR = 366
        else:
            DAYS_ONE_YEAR = 365
        from jetend.jmSheets import RawEntryValuation

        data_list = DataList(RawEntryValuation).from_pd(RawEntryValuation, self.info_board.db.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM 会计凭证估值净值表 
            WHERE 日期 = '{}' AND 产品 = '{}'
            ;""".format(self.last_date, product)
        ))
        if len(data_list) == 1:
            data_obj = data_list[0]
        elif len(data_list) == 0:
            if product == '稳健18号':
                pass
            else:
                raise RuntimeError('前日产品资产净值数据 management.产品余额持仓表 缺失 {} {}'.format(self.last_date, product))
        else:
            raise RuntimeError(data_list)
        mf_rate = self.info_board.find_product_management_fee_rate(product, self.current_date)
        daily_management_fee = round(data_obj.net_asset * mf_rate / DAYS_ONE_YEAR, 2)
        self.generate_journal_entry_by_obj(ManagementFeePayableFlow(
            product=product, date=self.current_date, fee_type='应付管理费计提', daily_fee=daily_management_fee,
        ))

        # self.log.info_running('管理费返还', '生成分录凭证')
        # # WARNING: 取决于产品持仓明细表，持仓和市值有误这部分就有误，产品持仓明细只有
        # mf_rec_list = DataList(ManagementFeeReceivableFlow)
        # for pos in self.positions.find_value_where(product=product):
        #     assert isinstance(pos, EntryPosition)
        #     if pos.institution != '久铭':
        #         continue
        #     mf_rec_list.append(ManagementFeeReceivableFlow(
        #         investor=pos.product, date=self.current_date, invested=pos.security_name,
        #         fee_return=round(pos.last_market_value * self.info_board.find_product_management_return_rate(
        #             pos.product, pos.security_name, self.current_date) / 365, 2), ))
        # self.generate_journal_entry(mf_rec_list)

        self.log.info_running('基金流水处理', '基金流水')
        data_list = DataList(FundConfirmFlow)
        sql = """
        SELECT `投资人` as name, `交易类型` as type, `日期` as date, `产品名称` as product_name, 
            `产品代码` as security_code, `机构名称` as institution, `发生金额` as amount, `净值` as netvalue,
            `份额` as share, `币种` as currency, `确认日期` as confirmation_date
        FROM `{}` WHERE `确认日期` = '{}'
        ;""".format('基金交易流水', self.current_date)
        for obj in DataList.from_pd(FundConfirmFlow, self.env.data_base.read_pd_query(DataBaseName.journal, sql)):
            assert isinstance(obj, FundConfirmFlow)
            if obj.institution == '久铭':
                continue
            if obj.product not in self.env.product_range:
                continue
            data_list.append(obj)
        self.generate_journal_entry(data_list)

        self.log.info_running('股利信息', '生成分录凭证，更新持仓列表')
        dividend_info_list = DataList.from_pd(DividendInfo, self.env.data_base.read_pd_query(
            DataBaseName.valuation,
            """SELECT * FROM `股利信息表` WHERE `除权日` = '{}';""".format(self.current_date)
        ))
        self.log.debug(dividend_info_list)
        data_list = DataList(DividendFlowing)
        for obj in dividend_info_list:
            assert isinstance(obj, DividendInfo)
            if obj.dividend_mode == '债券付息':
                for pos in self.positions.find_value_where(product=product, security_code=obj.security_code.upper()):
                    assert isinstance(pos, EntryPosition)
                    data_list.append(DividendFlowing(
                        product=product, date=pos.date, institution=pos.institution,
                        security_code=pos.security_code, security_name=pos.security_name,
                        trade_class='除权除息', dividend_mode=obj.dividend_mode, currency=obj.currency,
                        cash_amount=obj.cash_dividend * pos.hold_volume,
                    ))
            elif obj.dividend_mode in ('现金派息',):
                if obj.ex_date == obj.dividend_date:
                    security_name = self.info_board.find_security_name_by_code(obj.security_code.upper())
                    for acc in self.accounts.find_value_where(
                            product=product, account_name='证券清算款', sub_account='股利收益', note_account=security_name
                    ):
                        assert isinstance(acc, EntryAccount)
                        data_list.append(DividendFlowing(
                            product=product, date=acc.date, institution=acc.base_account,
                            security_code=obj.security_code.upper(), security_name=security_name,
                            trade_class='内部结转股利收益', currency=obj.currency,
                            cash_amount=acc.realtime_net_value,
                        ))
                else:
                    for pos in self.positions.find_value_where(
                            product=product, security_code=obj.security_code.upper()):
                        assert isinstance(pos, EntryPosition)
                        if pos.security_code.split('.')[-1] in ('SH', 'SZ',):
                            data_list.append(DividendFlowing(
                                product=pos.product, date=pos.date, institution=pos.institution,
                                security_code=pos.security_code, security_name=pos.security_name,
                                trade_class='除权除息', dividend_mode=obj.dividend_mode, currency=obj.currency,
                                cash_amount=obj.cash_dividend * pos.hold_volume,
                            ))
                        elif pos.security_code.split('.')[-1] in ('HK',):
                            data_list.append(DividendFlowing(
                                product=pos.product, date=pos.date, institution=pos.institution,
                                security_code=pos.security_code, security_name=pos.security_name,
                                trade_class='除权除息', dividend_mode=obj.dividend_mode, currency=obj.currency,
                                cash_amount=obj.cash_dividend * pos.hold_volume * 0.8,
                            ))
                        else:
                            raise NotImplementedError('{}\n{}'.format(pos, obj))
            else:
                raise NotImplementedError(obj)
        self.generate_journal_entry(data_list)

        # 4
        self.log.info_running('债券利息', '生成分录凭证，利息增值税')
        # # WARNING: 取决于产品持仓明细表，持仓有误这部分就有误
        data_list = DataList(BondIntersetsFlow)
        for pos in self.positions.find_value_where(product=product, account_name='债券投资'):
            assert isinstance(pos, EntryPosition)
            new_bi = BondIntersetsFlow.init_from(pos)
            data_list.append(new_bi)
            raise NotImplementedError(pos)
        self.generate_journal_entry(data_list)
        self.trigger_event_list(event_type=EventType.VATGen, data_list=data_list)

        self.log.info_running('银行流水处理', '生成分录凭证、已付增值税、更新持仓列表、更新存借款余额表')
        data_list = self.bank_flow_list.find_value_where(product=product)
        self.generate_journal_entry(data_list)

        # 7
        self.log.info_running('股票流水处理', '生成分录凭证、价差增值税、更新持仓表、更新存借款余额')
        data_list = self.stock_flow_list.find_value_where(product=product)
        self.generate_journal_entry(data_list)

        # 8
        self.log.info_running('两融流水处理', '生成分录凭证、价差增值税、更新持仓表、更新存借款余额')
        data_list = self.__derive_table_data_on_date__(MarginFlow, '原始两融流水记录', self.current_date, product)
        self.generate_journal_entry(data_list)

        # 9
        self.log.info_running('期权流水处理', '生成分录凭证、价差增值税、更新持仓表、更新存借款余额')
        data_list = self.option_flow_list.find_value_where(product=product)
        # self.generate_journal_entry(data_list)
        # if len(data_list) > 0:
        #     raise NotImplementedError(data_list)
        option_trade_class_set = data_list.collect_distinct_attr('trade_class')
        for tag in option_trade_class_set:
            if '卖' not in tag:
                self.generate_journal_entry(data_list.find_value_where(trade_class=tag))
        for tag in option_trade_class_set:
            if '卖' in tag:
                self.generate_journal_entry(data_list.find_value_where(trade_class=tag))

        # 10
        self.log.info_running('期货流水处理', '生成分录凭证、价差增值税、更新持仓表')
        data_list = self.future_flow_list.find_value_where(product=product)
        self.generate_journal_entry(data_list)

        # 11
        self.log.info_running('债券流水处理', '生成分录凭证、更新持仓表')
        data_list = self.bond_flow_list.find_value_where(product=product)
        self.generate_journal_entry(data_list)

        self.log.info_running('股票流水处理', '检查证券清算款是否上市交易')
        for pos in self.positions.find_value_where(product=product):
            assert isinstance(pos, EntryPosition)
            if pos.account_name == '证券清算款':
                raise NotImplementedError(self)

        self.log.info_running('调整分录', '')
        data_list = self.__derive_table_data_on_date__(ModifyFlowing, '录入调整流水', self.current_date, product)
        self.generate_journal_entry(data_list)

        self.log.info_running('存借款利息计提', '生成分录凭证')
        # WARNING: 取决于科目余额表
        if self.current_date <= datetime.date(2019, 7, 1):
            data_list = self.__interest_flow_generation_process__(
                DataList.from_pd(InterestRate, self.env.data_base.read_pd_query(
                    DataBaseName.management,
                    """
                    select a.* from `利率表` as a, (
                        select `科目`, `机构`, MAX(`起效日期`) as 最新起效日期 FROM `利率表` 
                        WHERE `起效日期` < '{}' GROUP BY `科目`, `机构`) as b 
                    WHERE a.`机构` = b.`机构` AND a.`科目` = b.`科目` AND a.`起效日期` = b.`最新起效日期`
                    ;""".format(self.current_date)
                )))
        else:
            data_list = self.__interest_flow_recevable_generation_process__(product=product)
        self.generate_journal_entry(data_list)

        self.log.info_running('华泰收益互换', '估值调整')
        from jetend.jmSheets import RawSwapHtscAccount
        data_list = DataList(SwapFlow)
        source_data_list = DataList.from_pd(RawSwapHtscAccount, self.info_board.db.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM 原始华泰收益互换账户资金记录 WHERE 产品 = '{}' AND 交易市场 = '合计' AND 日期 = (
                SELECT MAX(日期) FROM 原始华泰收益互换账户资金记录 WHERE 产品 = '{}' AND 日期 <= '{}'
            );""".format(product, product, self.current_date)
        ))
        if len(source_data_list) > 0:
            swap_today_obj = source_data_list[0]
            if swap_today_obj.date == self.current_date:
                try:
                    last_swap_today_obj = DataList.from_pd(RawSwapHtscAccount, self.info_board.db.read_pd_query(
                        DataBaseName.management,
                        """SELECT * FROM 原始华泰收益互换账户资金记录 WHERE 产品 = '{}' AND 交易市场 = '合计' AND 日期 = (
                            SELECT MAX(日期) FROM 原始华泰收益互换账户资金记录 WHERE 产品 = '{}' AND 日期 < '{}'
                        );""".format(product, product, self.current_date)
                    ))[0]
                    last_swap_today_obj_date = last_swap_today_obj.date
                    last_swap_today_obj_net_asset = last_swap_today_obj.net_asset
                except IndexError:
                    last_swap_today_obj_date = self.current_date - datetime.timedelta(days=2)
                    last_swap_today_obj_net_asset = 0.0
                assert last_swap_today_obj_date < swap_today_obj.date, '{}\n{}'.format(
                    last_swap_today_obj_date, swap_today_obj)
                self.log.debug('{}\n{}'.format(last_swap_today_obj_date, swap_today_obj))
                value_change = swap_today_obj.net_asset - last_swap_today_obj_net_asset
            else:
                value_change = 0.0

            if len(self.bank_flow_list.find_value_where(product=product, opposite='华泰互换')) > 0:
                for obj in self.bank_flow_list.find_value_where(product=product, opposite='华泰互换'):
                    value_change += obj.trade_amount
                for obj in self.bank_flow_list.find_value_where(product=product, opposite='华泰收益互换'):
                    value_change += obj.trade_amount
            data_list.append(SwapFlow(
                product=product, date=self.current_date, institution='华泰互换',
                trade_class='收益互换估值增值', amount=value_change,
            ))
        self.generate_journal_entry(data_list)

        self.log.info_running('中信收益互换', '估值调整')
        from jetend.jmSheets import RawSwapCiticAccount
        data_list = DataList(SwapFlow)
        sub_acc_list = self.accounts.find_value_where(product=product, account_name='收益互换', )
        self.log.debug(sub_acc_list)
        for institution in sub_acc_list.collect_distinct_attr('base_account'):
            if institution in ('华泰互换',):
                continue
            swap_today_obj = DataList.from_pd(RawSwapCiticAccount, self.info_board.db.read_pd_query(
                DataBaseName.management,
                """SELECT * FROM 原始中信收益互换账户资金记录 WHERE 产品 = '{}' AND 机构 = '{}' AND 日期 = (
                    SELECT MAX(日期) FROM 原始中信收益互换账户资金记录 WHERE 产品 = '{}' AND 机构 = '{}' AND 日期 <= '{}'
                );""".format(product, institution, product, institution, self.current_date)
            ))[0]
            if swap_today_obj.date == self.current_date:
                last_swap_today_obj = DataList.from_pd(RawSwapCiticAccount, self.info_board.db.read_pd_query(
                    DataBaseName.management,
                    """SELECT * FROM 原始中信收益互换账户资金记录 WHERE 产品 = '{}' AND 机构 = '{}' AND 日期 = (
                        SELECT MAX(日期) FROM 原始中信收益互换账户资金记录 WHERE 产品 = '{}' AND 机构 = '{}' AND 日期 < '{}'
                    );""".format(product, institution, product, institution, self.current_date)
                ))[0]
                assert last_swap_today_obj.date < swap_today_obj.date, '{}\n{}'.format(
                    last_swap_today_obj, swap_today_obj)
                value_change = swap_today_obj.capital_sum - last_swap_today_obj.capital_sum
            else:
                continue

            if len(self.bank_flow_list.find_value_where(product=product, opposite=institution)) > 0:
                for obj in self.bank_flow_list.find_value_where(product=product, opposite=institution):
                    value_change += obj.trade_amount
            data_list.append(SwapFlow(
                product=product, date=self.current_date, institution=institution,
                trade_class='收益互换估值增值', amount=value_change,
            ))
        self.log.debug(data_list)
        self.generate_journal_entry(data_list)

        self.log.info_running('估值增值检查', '产品持仓')
        data_list = DataList(DailyValueAddedFlowing)
        for pos in self.positions.find_value_where(product=product):
            assert isinstance(pos, EntryPosition)
            self.log.debug(pos)
            pos.__market_value__ = math.nan
            try:
                if pos.institution in ('中信美股', '中信港股'):
                    raise NotImplementedError(self)
                if 1100 <= pos.account_code < 1200:
                    try:
                        data_list.append(DailyValueAddedFlowing.init_from(pos))
                    except KeyError as k_r:
                        print(pos)
                        raise k_r
            except AttributeError as attr_error:
                print(pos.product, pos.date, pos.institution, pos.security_code, pos.security_name)
                raise attr_error
        self.generate_journal_entry(data_list)

        self.log.info_running('增值税处理 - 预提', '生成分录凭证，更新备查簿')
        for dva in data_list:
            self.log.debug(dva)
            assert isinstance(dva, DailyValueAddedFlowing)
            if dva.account_code in (1103, 1105,):  # 债券和基金
                continue
            elif dva.account_code == 1102 and dva.security_name not in ['财富宝E', '建信添益']:  # 部分股票
                continue
            else:
                # 二级市场基金和衍生品 计税
                self.vat_withholding_list.append(VATWithholding.init_from(dva))

        # 计算今日预提增值税
        data_list = self.vat_withholding_list.find_value_where(product=product)
        new_vat_obj = VATSum(
            product=product, date=self.current_date, vat_type='预提',
            vat=data_list.sum_attr('vat'), building_tax=data_list.sum_attr('building_tax'),
            education_surcharge=data_list.sum_attr('education_surcharge'),
            local_education_surcharge=data_list.sum_attr('local_education_surcharge'), )
        self.today_vat_sum_list.append(new_vat_obj)

        # 计算进入凭证的预提增值税
        entry_vat_sum_list = DataList(VATSum)

        try:
            last_vat_obj = self.lastday_vat_sum_list.find_value(product=product, vat_type='价差')
        except ValueError:
            raise RuntimeError('前日 {} {} 无价差增值税数据'.format(self.last_date, product))
        if self.current_date.month == 1 and self.current_date.day == 1:
            if last_vat_obj.total_tax < 0.0:  # 备查簿数字为负，清零
                raise NotImplementedError(last_vat_obj)
            else:
                pass
        else:
            pass

        vat_obj = VATSum.from_dict(last_vat_obj.to_dict())
        today_vat_tran_list = self.vat_transaction_list.find_value_where(product=product)
        vat_obj.set_attr('date', self.current_date)
        for obj in today_vat_tran_list:
            vat_obj.update_by(obj)
        self.today_vat_sum_list.append(vat_obj)

        if last_vat_obj.total_tax > 0 or vat_obj.total_tax > 0:
            entry_vat_sum_list.append(VATSum(
                product=vat_obj.product, date=self.current_date, vat_type='价差',
                vat=max(0, vat_obj.vat) - max(0, last_vat_obj.vat),
                building_tax=max(0, vat_obj.building_tax) - max(0, last_vat_obj.building_tax),
                education_surcharge=max(0, vat_obj.education_surcharge) - max(0, last_vat_obj.education_surcharge),
                local_education_surcharge=max(0, vat_obj.local_education_surcharge) - max(
                    0, last_vat_obj.local_education_surcharge),
            ))

        today_vat_jiacha_sum = vat_obj

        try:
            vat_obj = self.today_vat_sum_list.find_value(product=product, vat_type='预提', )
        except ValueError:
            vat_obj = VATSum(product=product, date=self.current_date, vat_type='预提', vat=0)
        assert isinstance(vat_obj, VATSum)
        last_vat_obj = self.lastday_vat_sum_list.find_value(product=product, vat_type='预提')
        assert isinstance(last_vat_obj, VATSum)

        # 调整价差增值税带来的影响 价差增值税为负 预提为正
        if today_vat_jiacha_sum.total_tax < 0 < vat_obj.total_tax:
            new_vat_obj = VATSum(
                product=product, date=self.current_date, vat_type='预提',
                vat=vat_obj.vat + today_vat_jiacha_sum.vat,
                building_tax=vat_obj.building_tax + today_vat_jiacha_sum.building_tax,
                education_surcharge=vat_obj.education_surcharge + today_vat_jiacha_sum.education_surcharge,
                local_education_surcharge=vat_obj.local_education_surcharge
                                          + today_vat_jiacha_sum.local_education_surcharge,
            )
        if last_vat_obj.total_tax > 0 or vat_obj.total_tax > 0:
            entry_vat_sum_list.append(VATSum(
                product=new_vat_obj.product, date=self.current_date, vat_type='预提',
                vat=max(0, new_vat_obj.vat) - max(0, last_vat_obj.vat),
                building_tax=max(0, new_vat_obj.building_tax) - max(0, last_vat_obj.building_tax),
                education_surcharge=max(0, new_vat_obj.education_surcharge) - max(0, last_vat_obj.education_surcharge),
                local_education_surcharge=max(0, new_vat_obj.local_education_surcharge) - max(
                    0, last_vat_obj.local_education_surcharge),
            ))
        # self.generate_journal_entry(entry_vat_sum_list)  #wavezhou

        # 16
        self.log.info_running('增值税处理 - 价差、利息、已付', '生成分录凭证，更新备查簿')
        #self.generate_journal_entry(self.vat_interests_list) #wavezhou

        self.log.info_running('等待事件引擎结束事务处理')
        self.env.event_engine.wait()
        self.log.info_running('事件引擎结束事务处理')

        self.log.info_running('简单统计')
        acc_list = self.accounts.find_value_where(product=product)
        if product == '稳健18号':
            temp_list = self.accounts.find_value_where(product='稳健18号')
            print(temp_list)
        entry_list_gap = acc_list.sum_attr('debit_amount_move') - acc_list.sum_attr('credit_amount_move')
        if abs(entry_list_gap) > 1:
            raise RuntimeError('！！！！！凭证借贷不平 {}'.format(entry_list_gap))
        total_asset, total_liability = None, None
        sub_acc_list = DataList(EntryAccount)
        if vat_obj.product == '久铭2号':
            print('暂停')
        sub_acc_list.extend(acc_list.find_value_where(account_name='银行存款'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='股票投资'))
        stock_temp_list = list()
        stock_temp_list.extend(acc_list.find_value_where(account_name='股票投资'))
        stock_account = 0
        for temp_obj in stock_temp_list:
            if isinstance(temp_obj, EntryAccount):
                stock_account += temp_obj.realtime_net_value
        sub_acc_list.extend(acc_list.find_value_where(account_name='收益互换'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='存出保证金'))
        security_money_list = list()
        security_money_list.extend(acc_list.find_value_where(account_name='存出保证金'))
        money_account = 0
        for temp_obj in security_money_list:
            if isinstance(temp_obj, EntryAccount):
                money_account += temp_obj.realtime_net_value
        sub_acc_list.extend(acc_list.find_value_where(account_name='结算备付金'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='基金投资'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='权证投资'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='其他应收款'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='应收股利'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='应收利息'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='证券清算款'))
        total_asset = sub_acc_list.sum_attr('net_value')
        sub_acc_list = DataList(EntryAccount)
        sub_acc_list.extend(acc_list.find_value_where(account_name='短期借款'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='其他应付款'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='应付赎回款'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='应交税费'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='应付管理人报酬'))
        sub_acc_list.extend(acc_list.find_value_where(account_name='应付利息'))
        total_liability = sub_acc_list.sum_attr('net_value')
        net_asset_value = total_asset + total_liability
        obj = acc_list.find_value(account_name='实收基金')
        from jetend.jmSheets import RawEntryValuation
        if vat_obj.product == '稳健18号':
            print('dsgsgs')
        if product == '稳健18号':
            print('sgsgsd')
        new_value_obj = RawEntryValuation(
            product=product, date=self.current_date, net_asset=round(net_asset_value, 2),
            fund_shares=abs(obj.net_value), net_value=round(net_asset_value / abs(obj.net_value), 3),
            total_asset=round(total_asset, 2), total_liability=round(total_liability, 2),
        )
        self.env.data_base.execute(
            DataBaseName.management,
            """DELETE FROM 会计凭证估值净值表 WHERE 日期 = '{}' AND 产品 = '{}';""".format(self.current_date, product)
        )
        self.env.data_base.execute(DataBaseName.management, new_value_obj.form_insert_sql('会计凭证估值净值表'))

    def save_to_db(self):
        # self.log.info('\n\n\t当日星期 {}'.format(self.current_date.isoweekday()))
        self.log.time_sleep(2)

        # self.to_csv('增值税备查簿_预估余额', self.today_vat_sum_list)
        # self.to_csv('增值税备查簿_已付', self.vat_paid_list)
        #
        # self.to_csv('增值税备查簿_应付_价差收入', self.vat_transaction_list)
        #
        # self.to_csv('增值税备查簿_应付_利息收入', self.vat_interests_list)
        #
        # self.to_csv('增值税备查簿_预提', self.vat_withholding_list)
        #
        # self.to_csv('会计分录凭证表', self.journal_entry_list)
        #
        # self.to_csv('会计产品持仓表', self.positions)
        #
        # self.to_csv('会计科目余额表', self.accounts)

        self.clear_duplicated_in_db('增值税备查簿_预估余额')
        self.insert_to_db('增值税备查簿_预估余额', self.today_vat_sum_list)

        self.clear_duplicated_in_db('增值税备查簿_已付')
        self.insert_to_db('增值税备查簿_已付', self.vat_paid_list)

        self.clear_duplicated_in_db('增值税备查簿_应付_价差收入')
        self.insert_to_db('增值税备查簿_应付_价差收入', self.vat_transaction_list)

        self.clear_duplicated_in_db('增值税备查簿_应付_利息收入')
        self.insert_to_db('增值税备查簿_应付_利息收入', self.vat_interests_list)

        self.clear_duplicated_in_db('增值税备查簿_预提')
        self.insert_to_db('增值税备查簿_预提', self.vat_withholding_list)

        self.clear_duplicated_in_db('会计分录凭证表')
        self.insert_to_db('会计分录凭证表', self.journal_entry_list)

        self.clear_duplicated_in_db('会计产品持仓表')
        self.insert_to_db('会计产品持仓表', self.positions)

        self.clear_duplicated_in_db('会计科目余额表')
        self.insert_to_db('会计科目余额表', self.accounts)

        self.log.info('\n\n\n')
        self.log.info('\t\t当前运行日：{}  星期 {}'.format(self.current_date, self.current_date.isoweekday()))
        self.log.warning_if(
            len(List.from_pd(RawTrusteeshipValuation, self.env.data_base.read_pd_query(
                DataBaseName.management,
                """
                SELECT * FROM `原始托管估值表净值表` WHERE `日期` = '{}'
                ;""".format(self.current_date)))) == 0, '\t当日无托管估值表单位净值数据！！！'
        )
        self.log.info('\t\t下一个运行日：{}'.format(self.current_date + datetime.timedelta(days=1)))

    def __account_update_process__(self, event: EventObject):
        """科目余额更新"""
        from sheets.entry.Entry import JournalEntry
        entry = event.data
        assert isinstance(entry, JournalEntry)
        self.log.debug('updating EntryAccount by {}'.format(entry))
        acc_list = self.accounts.find_value_where(
            product=entry.product, date=entry.date, account_name=entry.account_name,
        )
        try:
            acc = acc_list.find_value(
                sub_account=entry.account_level_2, base_account=entry.account_level_3,
                note_account=entry.account_level_4,
            )
            acc.update_by(entry)
            self.log.debug('{}'.format(acc))
        except ValueError:
            if entry.is_force_match is True and abs(entry.amount) > 0.01:
                raise NotImplementedError('{}'.format(entry))
            else:
                acc = EntryAccount(
                    product=entry.product, date=entry.date,
                    account_name=entry.account_name, sub_account=entry.account_level_2,
                    base_account=entry.account_level_3, note_account=entry.account_level_4,
                    start_net_value=0.0, net_value=0.0, debit_amount_move=0.0, credit_amount_move=0.0,
                )
                acc.update_by(entry)
                self.log.debug('{}'.format(acc))
                self.accounts.append(acc)

    def __position_update_process__(self, event: EventObject):
        """持仓信息更新"""
        data = event.data
        assert isinstance(data, EntryPositionMove)
        if data.product not in self.env.product_range:
            return
        self.update_position(data)

    def update_position(self, pos_move: EntryPositionMove):
        self.log.debug('update position by {}'.format(pos_move))
        pos_list = self.positions.find_value_where(
            product=pos_move.product, institution=pos_move.institution, security_code=pos_move.security_code
        )
        if len(pos_list) == 1:
            for pos in pos_list:
                assert isinstance(pos, EntryPosition)
                pos.update_from(pos_move)
        elif len(pos_list) == 0:
            self.positions.append(EntryPosition.init_from_update(pos_move))
        else:
            raise RuntimeError(str(pos_list))

    def generate_journal_entry_by_obj(self, data):
        from sheets.entry.Entry import JournalEntry
        if data.product not in self.env.product_range:
            return
        # 生成分录凭证
        j_list = DataList(JournalEntry)
        self.log.debug('generating jounal entry for {}'.format(data))
        if data.product == '稳健5号':
            print('zanting')
        j_list.extend(data.generate_journal_entry())
        if abs(j_list.find_value_where(debit_credit=SIDE_DEBIT_CN).sum_attr('amount')
               - j_list.find_value_where(debit_credit=SIDE_CREDIT_CN).sum_attr('amount')) >= 0.01:
            raise RuntimeError(j_list)

        self.journal_entry_list.extend(j_list)

        self.env.event_engine.wait()

        # 检查分录凭证
        for j_e in j_list:
            assert isinstance(j_e, JournalEntry)
            self.__account_update_process__(EventObject(EventType.AccountUpdate, j_e))

    def generate_journal_entry(self, data_list):
        for data in data_list:
            self.generate_journal_entry_by_obj(data)

    def __interest_flow_generation_process__(self, ir_list: DataList):
        """存借款利息提记"""
        if_list = DataList(InterestsFlow)
        for acc in self.accounts:
            assert isinstance(acc, EntryAccount)
            if acc.account_name in ('银行存款', '短期借款', '存出保证金'):
                if '期货' in acc.base_account:  # 警告！期货存出保证金无利息
                    continue
                try:
                    if acc.account_name == '银行存款':
                        i_rate = ir_list.find_value(account=acc.account_name, institution=acc.sub_account)
                    elif acc.account_name == '存出保证金':
                        i_rate = ir_list.find_value(account=acc.account_name, institution=acc.base_account)
                    elif acc.account_name == '短期借款':
                        i_rate = ir_list.find_value(account=acc.account_name, institution=acc.base_account)
                    else:
                        raise NotImplementedError(acc)
                except ValueError as e:
                    if acc.net_value < 0.01:
                        continue
                    else:
                        self.log.critical(str(acc))
                        raise e
                assert isinstance(i_rate, InterestRate)
                if i_rate.institution in ('中信美股', '中信港股'):  # TODO: 这个利率是计算借款利率的 借款利率用外汇结算
                    continue

                if_list.append(InterestsFlow.init_from(acc, i_rate))
            else:
                pass
        return if_list

    def __interest_flow_recevable_generation_process__(self, product: str):
        from jetend.jmSheets import AccountInterestRate
        if_list = DataList(InterestsFlow)
        for acc in self.accounts.find_value_where(product=product):
            if product == '久铭3号':
                print("暂停一下")
            assert isinstance(acc, EntryAccount)
            if acc.account_name in ('银行存款', '存出保证金'):
                self.log.debug(acc)
                if '期货' in acc.base_account:
                    continue
                if abs(acc.net_value) < 0.01:
                    continue
                if - 1.0 < acc.net_value < 0:
                    continue
                if acc.net_value < - 1.0:
                    # continue
                    raise RuntimeError(acc)
                if acc.account_name == '银行存款':
                    i_rate = self.info_board.find_product_account_interest_rate(
                        product, '银行存款', acc.sub_account, self.current_date)
                    institution = acc.sub_account
                elif acc.account_name == '存出保证金':
                    institution = acc.base_account
                    if acc.sub_account == '普通账户':
                        account_type = '证券账户'
                    elif acc.sub_account == '信用账户':
                        account_type = '信用账户'
                    elif acc.sub_account == '期权账户':
                        account_type = '期权账户'
                    else:
                        raise NotImplementedError(acc)
                    i_rate = self.info_board.find_product_account_interest_rate(
                        acc.product, account_type, acc.base_account, self.current_date)
                else:
                    raise NotImplementedError(acc)
                assert isinstance(i_rate, AccountInterestRate)
                daily_interest = acc.net_value * i_rate.interest_rate
                if abs(daily_interest) < 0.01:
                    continue
                daily_interest = daily_interest / i_rate.yearly_accrued_days
                assert is_valid_float(daily_interest), '{}\n{}'.format(acc, i_rate)
                if_list.append(InterestsFlow(
                    product=acc.product, date=self.current_date, account_name=acc.account_name,
                    institution=institution, daily_interest=round(daily_interest, 2),
                ))
            elif acc.account_name in ('短期借款', '其他应付款'):
                institution = acc.base_account
                if acc.account_name == '短期借款':
                    account_type = '融资账户'
                elif acc.account_name == '其他应付款':
                    if acc.sub_account == '融资费用':
                        account_type = '融资账户'
                    else:
                        continue
                else:
                    raise NotImplementedError(acc)
                i_rate = self.info_board.find_product_account_interest_rate(
                    acc.product, account_type, acc.base_account, self.current_date)
                if institution in ('长江两融', '招商两融'):
                    if acc.date.isoweekday() in (6, 7,):
                        multiplier = 0
                    elif acc.date.isoweekday() in (5,):
                        multiplier = 3
                    else:
                        multiplier = 1
                else:
                    raise NotImplementedError(acc)
                daily_interest = multiplier * acc.net_value * i_rate.interest_rate
                if abs(daily_interest) < 0.01:
                    continue
                daily_interest = daily_interest / i_rate.yearly_accrued_days
                assert is_valid_float(daily_interest), '{}\n{}'.format(acc, i_rate)
                if_list.append(InterestsFlow(
                    product=acc.product, date=self.current_date, account_name='短期借款',
                    institution=institution, daily_interest=round(daily_interest, 2),
                ))
            else:
                pass
        return if_list

    def __vat_generate_collection_process__(self, event: EventObject):
        """在其他流水生成增值税对象或者收集成列表"""
        data = event.data
        if isinstance(data, VATPaid):
            self.vat_paid_list.append(data)
        elif isinstance(data, VATTransaction):
            self.vat_transaction_list.append(data)
        elif isinstance(data, BondIntersetsFlow):
            new_vat_interest = VATBondInterests.init_from(data)
            self.vat_interests_list.append(new_vat_interest)
        else:
            raise NotImplementedError(type(data))

    def trigger_event_list(self, event_type, data_list):
        from collections.abc import Iterable
        assert isinstance(data_list, Iterable)
        for data in data_list:
            e_object = EventObject(event_type=event_type, data=data)
            self.env.event_engine.put(e_object)

    def clear_duplicated_in_db(self, table_name: str):
        self.env.data_base.execute(DataBaseName.management, """
        DELETE FROM {} WHERE 日期 = '{}';""".format(table_name, self.current_date))

    def insert_to_db(self, table_name: str, data_list: DataList):
        from jetend.structures import List
        self.log.info_running('储存当日', table_name)
        store_list = List()
        for obj in data_list:
            if obj.product not in self.env.product_range:
                continue
            store_list.append(obj)
        store_list.to_pd().to_sql(table_name, self.env.local_cache.engine, if_exists='replace')
        if len(store_list) > 0:
            for obj in store_list:
                self.env.data_base.execute(DataBaseName.management, getattr(
                    obj, 'form_insert_sql').__call__(table_name))


if __name__ == '__main__':
    from core.Environment import Environment

    env_inst = Environment()

    entry_gen = EntryGenerator(datetime.date(2019, 9, 18))
    env_inst.deploy_entry_generator(entry_gen)

    try:
        for p_str in env_inst.product_range:
            entry_gen.run_product(p_str)
        entry_gen.save_to_db()
    finally:
        env_inst.exit()
