# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import os

from modules.Modules import Modules
from runDailyValuation import ManagementProducts

from jetend.Constants import DataBaseName
from jetend.structures import List
from jetend.DataCheck import *
from jetend.jmSheets import *


class Monitor(object):

    def __init__(self, env: Modules):
        self.env = env
        self.db = env.sql_db
        self.info_board = env.info_board
        self.market_board = env.market_board

        self.current_date = None
        self.entry_accounts, self.entry_positions = None, None
        self.valuation_acc_pos = None
        self.__log__ = None

    @property
    def log(self):
        from jetend.structures import LogWrapper
        if self.__log__ is None:
            from jetend import get_logger
            assert isinstance(self.current_date, datetime.date)
            self.__log__ = get_logger(
                module_name=self.__class__.__name__,
                log_file=os.path.join(self.env.reach_relative_root_path(
                    'temp', 'log', '{}_{}.log'.format(self.current_date.strftime('%Y%m%d'), self.__class__.__name__)
                )))
        assert isinstance(self.__log__, LogWrapper), str(self.__log__)
        return self.__log__

    def compare_by_date(self, date: datetime.date):
        self.current_date = date

        self.entry_accounts = List.from_pd(EntryAccount, self.db.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `会计科目余额表` WHERE `日期` = '{}';""".format(self.current_date)
        ))
        self.entry_positions = List.from_pd(EntryPosition, self.db.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `会计产品持仓表` WHERE `日期` = '{}';""".format(self.current_date)
        ))
        assert len(self.entry_accounts) > 0, '当日无会计科目余额信息 {}'.format(self.current_date)
        # assert len(self.entry_positions) > 0, '当日无会计产品持仓信息 {}'.format(self.current_date)

        self.valuation_acc_pos = List.from_pd(AccountPosition, self.db.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `产品余额持仓表` WHERE `日期` = '{}';""".format(self.current_date)
        ))

        for product in ManagementProducts:
            self.log.info_running('comparing product', product)
            self.__account_level_compare__(
                entry_acc=self.entry_accounts.find_value_where(product=product),
                entry_pos=self.entry_positions.find_value_where(product=product),
                acc_pos=self.valuation_acc_pos.find_value_where(product=product),
            )

    def __account_level_compare__(self, entry_acc: List, entry_pos: List, acc_pos: List):

        # -------- 比较银行存款的机构信息是否相同，以防突然之间换存管银行 --------
        entry_obj = entry_acc.find_value(account_name='银行存款')
        value_obj = acc_pos.find_value(account_name='银行存款')
        self.log.warning_if(
            entry_obj.sub_account != value_obj.institution,
            '银行机构不同 {}\n{}'.format(entry_obj, value_obj),
        )
        self.log.warning_if(
            is_different_float(entry_obj.net_value, value_obj.volume, gap=0.5),
            '银行存款数目不同 {}\n{}'.format(entry_obj, value_obj)
        )

        # -------- 比较证券账户存出保证金数字 --------
        sub_entry_acc = entry_acc.find_value_where(account_name='存出保证金')
        # sub_entry_acc.extend(entry_acc.find_value_where(account_name='结算备付金'))
        institution_set = sub_entry_acc.collect_attr_set('base_account')
        sub_acc_pos = acc_pos.find_value_where(account_name='证券账户')
        sub_acc_pos.extend(acc_pos.find_value_where(account_name='信用账户'))
        sub_acc_pos.extend(acc_pos.find_value_where(account_name='期权账户'))
        institution_set.update(sub_acc_pos.collect_attr_set('institution'))
        for institution in institution_set:
            if '收益互换' in institution:
                continue
            entry_acc_obj = sub_entry_acc.find_value_where(base_account=institution)
            entry_acc_obj.extend(sub_entry_acc.find_value_where(base_account='估值增值'))
            # entry_acc_obj = sub_entry_acc.find_value_where()
            value_pos_obj = sub_acc_pos.find_value_where(institution=institution)
            gap = abs(entry_acc_obj.sum_attr('net_value') - value_pos_obj.sum_attr('volume'))
            self.log.warning_if(
                gap >= 0.5, '证券账户可用资金数目不同 {} \n凭证：{}\n余额：{}'.format(gap, entry_acc_obj, value_pos_obj)
            )

        sub_entry_acc = entry_acc.find_value_where(account_name='结算备付金')
        sub_entry_acc.extend(entry_acc.find_value_where(account_name='权证投资'))
        institution_set = sub_entry_acc.collect_attr_set('base_account')
        sub_acc_pos = acc_pos.find_value_where(account_name='期货账户')
        institution_set.update(sub_acc_pos.collect_attr_set('institution'))
        for institution in institution_set:
            entry_acc_obj = sub_entry_acc.find_value_where(base_account=institution)
            entry_acc_obj.extend(sub_entry_acc.find_value_where(base_account='估值增值'))
            value_pos_obj = sub_acc_pos.find_value_where(institution=institution)
            gap = abs(entry_acc_obj.sum_attr('net_value') - value_pos_obj.sum_attr('volume'))
            self.log.warning_if(
                gap >= 0.5, '证券账户可用资金数目不同 {} \n凭证：{}\n余额：{}'.format(gap, entry_acc_obj, value_pos_obj)
            )

        # -------- 比较两融账户负债 --------
        sub_entry_acc = entry_acc.find_value_where(account_name='应付利息', sub_account='短期借款利息')
        sub_acc_pos = acc_pos.find_value_where(account_name='应付融资利息')
        institution_set = sub_entry_acc.collect_attr_set('base_account')
        institution_set.update(sub_acc_pos.collect_attr_set('institution'))
        for institution in institution_set:
            entry_obj = sub_entry_acc.find_value(base_account=institution)
            value_obj = sub_acc_pos.find_value_where(institution=institution)
            self.log.warning_if(
                is_different_float(entry_obj.net_value, value_obj.sum_attr('market_value'), gap=0.5),
                '两融应付利息不同 {}\n{}'.format(entry_obj, value_obj)
            )

        # -------- 比较股票投资会计凭证每个产品的成本和估值是否对的上 --------
        sub_entry_pos = entry_pos.find_value_where(account_name='股票投资')
        sub_entry_acc = entry_acc.find_value_where(account_name='股票投资')
        security_set = sub_entry_acc.collect_attr_set('note_account')
        security_set.update(sub_entry_pos.collect_attr_set('security_name'))
        for security_name in security_set:
            institution_set = sub_entry_acc.find_value_where(
                note_account=security_name).collect_attr_set('base_account')
            institution_set.update(sub_entry_pos.find_value_where(
                security_name=security_name).collect_attr_set('institution'))
            for institution in institution_set:
                if institution in ('待转收', ):
                    continue
                try:
                    entry_pos_obj = sub_entry_pos.find_value(institution=institution, security_name=security_name)
                except ValueError:
                    entry_pos_obj = None
                entry_acc_obj = sub_entry_acc.find_value_where(
                    sub_account='成本', base_account=institution, note_account=security_name)
                if entry_pos_obj is None:
                    self.log.warning_if(  # 比较成本
                        abs(entry_acc_obj.sum_attr('net_value')) >= 0.01,
                        '股票成本数目不同 {}\n{}'.format(entry_pos_obj, entry_acc_obj),
                    )
                else:
                    self.log.warning_if(        # 比较成本
                        is_different_float(entry_pos_obj.total_cost, entry_acc_obj.sum_attr('net_value'), gap=0.5),
                        '股票成本数目不同 {}\n{}'.format(entry_pos_obj, entry_acc_obj),
                    )
                entry_acc_obj = sub_entry_acc.find_value_where(
                    sub_account='估值增值', base_account=institution, note_account=security_name)
                if entry_pos_obj is None:
                    self.log.warning_if(  # 比较成本
                        abs(entry_acc_obj.sum_attr('net_value')) >= 0.01,
                        '股票估值增值数目不同 {}\n{}'.format(entry_pos_obj, entry_acc_obj),
                    )
                else:
                    self.log.warning_if(        # 比较估值增值
                        is_different_float(
                            entry_pos_obj.market_value - entry_pos_obj.total_cost,
                            entry_acc_obj.sum_attr('net_value'), gap=0.5,
                        ),
                        '股票估值增值数目不同 {}\n{}'.format(entry_pos_obj, entry_acc_obj), )
        sub_acc_pos = acc_pos.find_value_where(account_name='股票')
        sub_acc_pos.extend(acc_pos.find_value_where(account_name='货基'))
        security_set = sub_entry_pos.collect_attr_set('security_code')
        security_set.update(sub_acc_pos.collect_attr_set('security_code'))
        for security_code in security_set:
            institution_set = sub_entry_pos.find_value_where(
                security_code=security_code).collect_attr_set('institution')
            institution_set.update(sub_acc_pos.find_value_where(
                security_code=security_code).collect_attr_set('institution'))
            for institution in institution_set:
                if '收益互换' in institution or institution in ('华泰互换', ):
                    continue
                try:
                    entry_pos_obj = sub_entry_pos.find_value(institution=institution, security_code=security_code)
                except ValueError:
                    entry_pos_obj = AccountPosition(hold_volume=0.0, market_value=0.0)
                value_pos_obj = sub_acc_pos.find_value_where(institution=institution, security_code=security_code)

                self.log.error_if(
                    is_different_float(entry_pos_obj.hold_volume, value_pos_obj.sum_attr('volume'), gap=0.5),
                    '股票持仓数量数目不同 {}\n{}'.format(entry_pos_obj, value_pos_obj),
                )
                self.log.warning_if(
                    is_different_float(entry_pos_obj.market_value, value_pos_obj.sum_attr('market_value'), gap=0.5),
                    '股票市值数目不同 {}\n{}'.format(entry_pos_obj, value_pos_obj),
                )

        # -------- 比较债券投资的成本和估值是否对的上 --------
        sub_entry_pos = entry_pos.find_value_where(account_name='债券投资')
        if len(sub_entry_pos) > 0:
            raise NotImplementedError(sub_entry_pos)

        # -------- 比较基金投资产品的成本和估值是否对的上 --------
        sub_entry_pos = entry_pos.find_value_where(account_name='基金投资')
        sub_entry_acc = entry_acc.find_value_where(account_name='基金投资')
        security_set = sub_entry_acc.collect_attr_set('note_account')
        security_set.update(sub_entry_pos.collect_attr_set('security_name'))
        for security_name in security_set:
            institution_set = sub_entry_acc.find_value_where(
                note_account=security_name).collect_attr_set('base_account')
            institution_set.update(sub_entry_pos.find_value_where(
                security_name=security_name).collect_attr_set('institution'))
            for institution in institution_set:
                entry_pos_obj = sub_entry_pos.find_value_where(institution=institution, security_name=security_name)
                entry_acc_obj = sub_entry_acc.find_value_where(
                    sub_account='成本', base_account=institution, note_account=security_name)
                self.log.warning_if(  # 比较成本
                    is_different_float(
                        entry_pos_obj.sum_attr('total_cost'), entry_acc_obj.sum_attr('net_value'),
                        gap=0.5), '基金成本数目不同 {}\n{}'.format(entry_pos_obj, entry_acc_obj),
                )
                entry_acc_obj = sub_entry_acc.find_value_where(
                    sub_account='估值增值', base_account=institution, note_account=security_name)
                self.log.warning_if(  # 比较估值增值
                    is_different_float(
                        entry_pos_obj.sum_attr('market_value') - entry_pos_obj.sum_attr('total_cost'),
                        entry_acc_obj.sum_attr('net_value'), gap=0.5
                    ),
                    '基金估值增值数目不同 {}\n{}'.format(entry_pos_obj, entry_acc_obj),
                )
        sub_acc_pos = acc_pos.find_value_where(account_name='公募基金')
        sub_acc_pos.extend(acc_pos.find_value_where(account_name='自有产品'))
        security_set = sub_entry_pos.collect_attr_set('security_code')
        security_set.update(sub_acc_pos.collect_attr_set('security_code'))
        for security_code in security_set:
            institution_set = sub_entry_pos.find_value_where(
                security_code=security_code).collect_attr_set('institution')
            institution_set.update(sub_acc_pos.find_value_where(
                security_code=security_code).collect_attr_set('institution'))
            for institution in institution_set:
                entry_pos_obj = sub_entry_pos.find_value_where(institution=institution, security_code=security_code)
                value_pos_obj = sub_acc_pos.find_value_where(institution=institution, security_code=security_code)
                self.log.error_if(is_different_float(
                    entry_pos_obj.sum_attr('hold_volume'), value_pos_obj.sum_attr('volume'), gap=0.5
                ), '基金持仓数量数目不同 {}\n{}'.format(entry_pos_obj, value_pos_obj), )
                self.log.warning_if(is_different_float(
                    entry_pos_obj.sum_attr('market_value'), value_pos_obj.sum_attr('market_value'), gap=0.5
                ), '基金市值数目不同 {}\n{}'.format(entry_pos_obj, value_pos_obj), )

        # -------- 比较收益互换 --------
        sub_entry_pos = entry_acc.find_value_where(account_name='收益互换', base_account='中信美股')
        sub_acc_pos = acc_pos.find_value_where(institution='美股收益互换')
        self.log.warning_if(
            is_different_float(sub_entry_pos.sum_attr('net_value'), sub_acc_pos.sum_attr('market_value'), gap=10),
            '美股收益互换净资产出错 {}\n{}\n{}'.format(
                sub_entry_pos.sum_attr('net_value') - sub_acc_pos.sum_attr('market_value'), sub_entry_pos, sub_acc_pos),
        )

        sub_entry_pos = entry_acc.find_value_where(account_name='收益互换', base_account='中信港股')
        sub_acc_pos = acc_pos.find_value_where(institution='港股收益互换')
        self.log.warning_if(
            is_different_float(sub_entry_pos.sum_attr('net_value'), sub_acc_pos.sum_attr('market_value'), gap=10),
            '港股收益互换净资产出错 {}\n{}\n{}'.format(
                sub_entry_pos.sum_attr('net_value') - sub_acc_pos.sum_attr('market_value'), sub_entry_pos, sub_acc_pos),
        )

        # -------- 比较应收股利 --------
        sub_entry_acc = entry_acc.find_value_where(account_name='应收股利')
        sub_acc_pos = List()
        for obj in acc_pos.find_value_where(account_name='应收股利'):
            if '收益互换' in obj.institution:
                pass
            else:
                sub_acc_pos.append(obj)
        self.log.warning_if(
            is_different_float(sub_entry_acc.sum_attr('net_value'), sub_acc_pos.sum_attr('market_value'), gap=0.5),
            '应收股利出现差异 {}\n{}'.format(sub_entry_acc, sub_acc_pos)
        )

        # -------- 比较短期借款 --------
        sub_entry_acc = entry_acc.find_value_where(account_name='短期借款')
        sub_acc_pos = acc_pos.find_value_where(account_name='短期借款')
        self.log.warning_if(
            is_different_float(sub_entry_acc.sum_attr('net_value'), sub_acc_pos.sum_attr('market_value'), gap=0.5),
            '短期借款数目不同 {}\n{}'.format(sub_entry_acc, sub_acc_pos),
        )

        # -------- 比较应付赎回款 --------
        sub_entry_acc = entry_acc.find_value_where(account_name='应付赎回款')
        sub_acc_pos = acc_pos.find_value_where(account_name='应付赎回款')
        institution_set = sub_entry_acc.collect_attr_set('sub_account')
        institution_set.update(sub_acc_pos.collect_attr_set('institution'))
        for institution in institution_set:
            if institution == '待转换':
                continue
            entry_obj = sub_entry_acc.find_value_where(sub_account=institution)
            value_obj = sub_acc_pos.find_value_where(institution=institution)
            self.log.warning_if(
                is_different_float(entry_obj.sum_attr('net_value'), value_obj.sum_attr('market_value'), gap=0.5),
                '应付赎回款数目不同 {}\n{}'.format(sub_entry_acc, sub_acc_pos),
            )

        # -------- 比较应付管理人报酬 - 固定管理费 --------
        try:
            entry_obj = entry_acc.find_value(account_name='应付管理人报酬', sub_account='固定管理费')
        except ValueError:
            entry_obj = None
        sub_acc_pos = acc_pos.find_value_where(account_name='累计应付管理费')
        sub_acc_pos.extend(acc_pos.find_value_where(account_name='已付应付管理费'))
        if entry_obj is None:
            self.log.warning_if(
                abs(sub_acc_pos.sum_attr('market_value')) > 0.01,
                '应付管理人报酬数目不同 {}\n{}\n{}'.format(sub_acc_pos.sum_attr('market_value'), entry_obj, sub_acc_pos), )
        else:
            self.log.warning_if(
                is_different_float(entry_obj.net_value, sub_acc_pos.sum_attr('market_value'), gap=0.5),
                '应付管理人报酬数目不同 {}\n{}\n{}'.format(
                    entry_obj.net_value - sub_acc_pos.sum_attr('market_value'), entry_obj, sub_acc_pos), )

        # -------- 比较应付管理人报酬 - 业绩报酬 --------
        try:
            entry_obj = entry_acc.find_value(account_name='应付管理人报酬', sub_account='业绩报酬')
        except ValueError:
            entry_obj = None
        sub_acc_pos = acc_pos.find_value_where(account_name='累计应付业绩报酬', )
        sub_acc_pos.extend(acc_pos.find_value_where(account_name='累计已付业绩报酬'))
        if entry_obj is None:
            self.log.warning_if(
                abs(sub_acc_pos.sum_attr('market_value')) > 0.01,
                '业绩报酬数目不同 {}\n{}'.format(entry_obj, sub_acc_pos),
            )
        else:
            self.log.warning_if(
                is_different_float(entry_obj.net_value, sub_acc_pos.sum_attr('market_value'), gap=0.5),
                '业绩报酬数目不同 {}\n{}'.format(entry_obj, sub_acc_pos),
            )

        # -------- 比较客户申购款到账但未确认的负债 --------
        sub_entry_acc = entry_acc.find_value_where(account_name='其他应付款', sub_account='未确认申购款')
        sub_acc_pos = acc_pos.find_value_where(account_name='应付申购款')
        self.log.warning_if(
            is_different_float(sub_entry_acc.sum_attr('net_value'), sub_acc_pos.sum_attr('market_value'), gap=0.5),
            '应付申购款负债不同 {}\n{}'.format(sub_entry_acc, sub_acc_pos),
        )

        # -------- 比较其他应付款 --------
        sub_entry_acc = List()
        for entry_acc_obj in entry_acc.find_value_where(account_name='其他应付款'):
            if entry_acc_obj.sub_account not in ('未确认申购款', ):
                sub_entry_acc.append(entry_acc_obj)
        sub_acc_pos = acc_pos.find_value_where(account_name='其他应付款')
        self.log.warning_if(
            is_different_float(sub_entry_acc.sum_attr('net_value'), sub_acc_pos.sum_attr('market_value'), gap=0.5),
            '其他应付款不同 {}\n{}'.format(sub_entry_acc, sub_acc_pos),
        )

        # -------- 比较实收基金 --------
        entry_obj = entry_acc.find_value(account_name='实收基金')
        value_obj = acc_pos.find_value(account_name='实收基金')
        self.log.error_if(
            is_different_float(abs(entry_obj.net_value), value_obj.volume, gap=0.2),
            '实收基金数目不同 {}\n{}'.format(entry_obj, value_obj)
        )


if __name__ == '__main__':
    from jetend.structures import MySQL, Sqlite

    env_inst = Modules()

    from WindPy import w
    w.start()
    env_inst.deploy_module('wind_engine', w, )

    env_inst.deploy_module('sql_db', MySQL(server='192.168.1.31', port=3306, username='root', passwd='jm3389', ))
    env_inst.deploy_module('cache_db', Sqlite(env_inst.reach_relative_root_path('cache.db')))

    monitor = Monitor(env_inst)

    monitor.compare_by_date(datetime.date(2019, 7, 1))

    env_inst.exit()
