# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import os
import datetime

from jetend.Constants import DataBaseName
from jetend.structures import List
from jetend.DataCheck import *
from jetend.jmSheets import *

from modules.AccountPosition import AccountPosition
from modules.Modules import Modules
from modules.Information import TaFlow


# # ManagementProducts = (
# #     # 非托管部分
# #     '久铭2号', '久铭3号', '全球1号', '收益1号', '双盈1号', '稳利2号',
# #     '稳健2号', '稳健3号', '稳健5号', '稳健6号', '稳健7号', '稳健8号', '稳健9号', '稳健10号', '稳健11号', '稳健12号',
# #     '稳健15号', '稳健16号', '稳健17号', '稳健18号', '稳健19号', '稳健21号', '稳健31号', '稳健32号', '稳健33号',
# #     # 托管部分
# #     '久铭1号', '久铭5号', '久铭7号', '久铭8号', '久铭9号', '久铭10号',
# #     # '稳健1号',
# #     '稳健22号', '稳健23号', '久盈2号', '收益2号',
# # )
# try:
#     ManagementProducts
# except NameError:
#     from runDailyValuation import ManagementProducts


class DailyValuation(object):

    def __init__(self, path_dict: dict, env: Modules):
        self.env = env
        self.db = env.sql_db
        self.path_dict = path_dict

        self.info_board = env.info_board
        self.market_board = env.market_board

        self.last_acc_pos = List()
        self.acc_pos = List()
        self.data_dict = dict()
        self.current_date, self.last_date = None, None
        self.simulation = False
        self.__log__ = None

    @property
    def log(self):
        from jetend.structures import LogWrapper
        if self.__log__ is None:
            from jetend import get_logger
            assert isinstance(self.current_date, datetime.date)
            self.__log__ = get_logger(
                module_name=self.__class__.__name__,
                log_file=os.path.join(self.env.root_path, 'temp', '{}_{}.log'.format(
                    self.current_date.strftime('%Y%m%d'), self.__class__.__name__
                )))
        assert isinstance(self.__log__, LogWrapper), str(self.__log__)
        return self.__log__

    def set_simulation_calculation(self):
        self.simulation = True
        return self

    def set_actual_calculation(self):
        self.simulation = False
        return self

    def set_current_working_date(self, current_date: datetime.date, ):
        self.current_date = current_date
        self.last_date = self.current_date - datetime.timedelta(days=1)

    def update_acc_pos_to_current_date(self, last_acc_pos: List, zero_drop: bool = True):
        assert isinstance(self.current_date, datetime.date), self.current_date
        for obj in last_acc_pos:
            assert isinstance(obj, AccountPosition)
            new_obj = AccountPosition().update(obj)
            new_obj.date = self.current_date
            if abs(new_obj.volume) >= 0.01:
                self.acc_pos.append(new_obj)
            else:
                if zero_drop is False:
                    self.acc_pos.append(new_obj)

    def __derive_data_preparation__(self):
        """获取需要处理的数据"""
        assert isinstance(self.current_date, datetime.date), '运行之前设置当前工作日期'

        if self.simulation is False:
            raise NotImplementedError
        else:
            # 导入上一天持仓和余额数据
            last_acc_pos = List.from_pd(AccountPosition, self.db.read_pd_query(
                DataBaseName.management, """SELECT * FROM 产品余额持仓表 WHERE 日期 = '{}';""".format(self.last_date)
            ))
            for product in ManagementProducts:
                if self.info_board.check_mandatory(product) is False and product != '稳健22号':
                    self.last_acc_pos.extend(last_acc_pos.find_value_where(product=product))
            last_acc_pos = List.from_pd(AccountPosition, self.db.read_pd_query(
                DataBaseName.management, """SELECT * FROM 产品模拟余额持仓表 WHERE 日期 = '{}';""".format(self.last_date)
            ))
            for product in ManagementProducts:
                if self.info_board.check_mandatory(product) is True or product == '稳健22号':
                    self.last_acc_pos.extend(last_acc_pos.find_value_where(product=product))
            assert len(self.last_acc_pos) > 0, '前一日 {} 运行数据缺失'.format(self.last_date)

        self.log.info_running('读取在途申赎流水')
        data_list = List()
        for obj in List.from_pd(TaFlow, self.db.read_pd_query(  # 在途申赎流水
                DataBaseName.transfer_agent_new,
                """SELECT * FROM 在途申赎流水表 WHERE date >= '{}';""".format(self.current_date.strftime('%Y%m%d')))):
            assert isinstance(obj, TaFlow)
            data_list.append(obj)
            self.log.debug(obj.__dict_data__)
        for obj in List.from_pd(TaFlow, self.db.read_pd_query(  # 历史在途申赎流水
                DataBaseName.transfer_agent_new,
                """SELECT * FROM 申赎流水录入表 WHERE date >= '{}';""".format(self.current_date.strftime('%Y%m%d')))):
            assert isinstance(obj, TaFlow)
            if is_valid_float(obj.check_status):
                data_list.append(obj)
                self.log.debug(obj.__dict_data__)
        self.data_dict['在途申赎流水'] = data_list

        self.log.info_running('读取申赎确认流水')
        self.data_dict['申赎确认流水'] = List.from_pd(TaFlow, self.db.read_pd_query(DataBaseName.transfer_agent_new, """
        SELECT * FROM 申赎流水表 WHERE confirmation_date = '{day}'
        ;""".format(day=self.current_date, )))

        self.log.info_running('读取申赎确认流水')
        data_list = List.from_pd(BankFlow, self.db.read_pd_query(DataBaseName.journal, """
        SELECT * FROM 银行标准流水 WHERE 日期 = '{}'
        ;""".format(self.current_date)))
        from core.func import separate_inner_bank_flow
        data_list.extend(separate_inner_bank_flow(data_list, ManagementProducts))
        sub_data_list = List()
        for obj in data_list:       # 只使用管理产品范围内银行流水
            if obj.product in ManagementProducts:
                sub_data_list.append(obj)
            else:
                continue
        # self.log.debug(sub_data_list)
        self.data_dict['银行标准流水'] = sub_data_list

    def __derive_fixed_holdings__(self):
        """当天相对固定的信息处理"""

        # --------------------------------
        self.log.info_running('根据在途申赎流水 - 生成应收应付款')
        from core.func import handle_account_payable_receivable_by_ta_flow
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='自有产品'))
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='其他应付款'))
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='应付申购款'))
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='待确认申购款'))
        acc_pos_list = self.acc_pos.find_value_where(account_name='自有产品')
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='其他应付款'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='待确认申购款'))
        self.acc_pos.extend(handle_account_payable_receivable_by_ta_flow(
            acc_pos=acc_pos_list, ta_flow=self.data_dict['在途申赎流水'], date=self.current_date))

        # --------------------------------
        self.log.info_running('根据确认申赎流水 - 修改实收基金，自有产品持仓')
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='累计应付业绩报酬'))
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='其他应收款'))
        acc_pos_list = self.acc_pos.find_value_where(account_name='其他应付款')
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='自有产品'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='其他应收款'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='应付申购款'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='待确认申购款'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='累计应付业绩报酬'))
        from core.func import handle_fund_share_by_ta_confirm_flow
        output_list = handle_fund_share_by_ta_confirm_flow(  # 加入实收基金、银行存款
            last_acc_pos=self.last_acc_pos.find_value_where(account_name='实收基金'),
            acc_pos=acc_pos_list, ta_confirm_flow=self.data_dict['申赎确认流水'], date=self.current_date,
        )
        # 处理自有产品首次建仓产品代码问题
        for obj in output_list:
            if obj.account_name == '自有产品':
                obj.security_code = self.info_board.find_product_code_by_name(obj.security_name)
            else:
                pass
        self.acc_pos.extend(output_list)

        # --------------------------------
        self.log.info_running('根据银行流水数据 - 更新银行存款，更新应收应付款')
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='银行存款'), zero_drop=False)
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='应付赎回款'))
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='已付应付管理费'))
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='已收应收管理费返还'))
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='累计已付业绩报酬'))
        # 更新银行存款
        acc_pos_list = self.acc_pos.find_value_where(account_name='银行存款')
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='应付赎回款'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='其他应付款'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='其他应收款'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='应付申购款'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='待确认申购款'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='已付应付管理费'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='已收应收管理费返还'))
        acc_pos_list.extend(self.acc_pos.find_value_where(account_name='累计已付业绩报酬'))
        from core.func import update_bank_account_by_bank_flow
        self.acc_pos.extend(update_bank_account_by_bank_flow(
            last_acc_pos=self.last_acc_pos.find_value_where(account_name='应收利息'),
            acc_pos=acc_pos_list, bank_flow_list=self.data_dict['银行标准流水'], date=self.current_date,
        ))

        # --------------------------------
        # TODO: 基金交易数据
        self.log.info_running('读取基金交易数据 - 更新基金持仓')

    def __derive_traded_holdings__(self):
        """获取当天交易流水并计算和预测持仓数目和账户余额"""

        self.log.info_running('读取银行流水数据 - 更新证券账户资金')
        from core.func import handle_security_account_by_bank_flow
        last_acc_pos = List()
        last_acc_pos.extend(self.last_acc_pos.find_value_where(account_name='证券账户'))
        last_acc_pos.extend(self.last_acc_pos.find_value_where(account_name='期货账户'))
        last_acc_pos.extend(self.last_acc_pos.find_value_where(account_name='期权账户'))
        last_acc_pos.extend(self.last_acc_pos.find_value_where(account_name='信用账户'))
        self.acc_pos.extend(handle_security_account_by_bank_flow(
            last_acc_list=last_acc_pos, bank_flow_list=self.data_dict['银行标准流水'], date=self.current_date,
        ))

        # --------------------------------
        self.log.info_running('读取交易流水 - 变动持仓数目、证券账户余额')
        from core.func import handle_security_account_position_by_trade_flow
        acc_list = List()
        acc_list.extend(self.acc_pos.find_value_where(account_name='证券账户'))
        acc_list.extend(self.acc_pos.find_value_where(account_name='期货账户'))
        acc_list.extend(self.acc_pos.find_value_where(account_name='期权账户'))
        acc_list.extend(self.acc_pos.find_value_where(account_name='信用账户'))
        last_pos_list = List()
        last_pos_list.extend(self.last_acc_pos.find_value_where(account_name='股票'))
        last_pos_list.extend(self.last_acc_pos.find_value_where(account_name='货基'))
        last_pos_list.extend(self.last_acc_pos.find_value_where(account_name='期货'))
        last_pos_list.extend(self.last_acc_pos.find_value_where(account_name='公募基金'))
        last_pos_list.extend(self.last_acc_pos.find_value_where(account_name='ETF基金'))
        last_pos_list.extend(self.last_acc_pos.find_value_where(account_name='可转债'))
        last_pos_list.extend(self.last_acc_pos.find_value_where(account_name='债券'))
        self.acc_pos.extend(handle_security_account_position_by_trade_flow(     # 加入持仓对象
            info_board=self.info_board, acc_list=acc_list, last_pos_list=last_pos_list,
            date=self.current_date, product_range=ManagementProducts,
        ))

        # --------------------------------
        self.log.info_running('处理收益互换数据')
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(
            account_name='应付利息', institution='美股收益互换'))
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(
            account_name='应付利息', institution='港股收益互换'))

    def __derive_journal_holdings__(self):

        self.log.info_running('读取券商对账单数据', '账户资金')
        last_acc_pos = List()
        last_acc_pos.extend(self.last_acc_pos.find_value_where(account_name='证券账户'))
        last_acc_pos.extend(self.last_acc_pos.find_value_where(account_name='信用账户'))
        last_acc_pos.extend(self.last_acc_pos.find_value_where(account_name='期货账户'))
        last_acc_pos.extend(self.last_acc_pos.find_value_where(account_name='期权账户'))
        from core.func import handle_security_account
        self.acc_pos.extend(handle_security_account(
            self.info_board, last_acc_pos, self.current_date, ManagementProducts))

        self.log.info_running('读取券商对账单数据', '账户持仓')
        from core.func import handle_security_position
        self.acc_pos.extend(handle_security_position(
            self.info_board, last_acc_pos, self.current_date, ManagementProducts))

        # --------------------------------
        self.log.info_running('读取收益互换对账单数据')
        last_acc_list = self.last_acc_pos.find_value_where(institution='美股收益互换')
        last_acc_list.extend(self.last_acc_pos.find_value_where(institution='港股收益互换'))
        from core.func import handle_citic_swap_account_position
        self.acc_pos.extend(handle_citic_swap_account_position(self.info_board, last_acc_list, self.current_date))

    def derive_holdings(self):
        """当天收盘后获取持仓明细"""

        self.__derive_data_preparation__()

        self.__derive_fixed_holdings__()

        if self.simulation is True:
            self.__derive_traded_holdings__()
        else:
            self.__derive_journal_holdings__()

    def derive_net_value(self):
        """计算和核对净值"""
        assert isinstance(self.current_date, datetime.date)

        # --------------------------------
        self.log.info_running('读取非托管产品数据计提当日银行、券商账户应收利息')
        data_list = List.from_pd(EntryAccount, self.db.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM 会计科目余额表 WHERE 日期 = '{}' AND 科目名称 = '应收利息'
            ;""".format(self.current_date)))
        from core.func import handle_non_mandated_interest_receivable
        self.acc_pos.extend(handle_non_mandated_interest_receivable(data_list, self.current_date))

        self.log.info_running('计算托管产品数据计提当日银行、券商账户应收利息')
        last_acc_pos, acc_pos = List(), List()
        last_acc_pos.extend(self.last_acc_pos.find_value_where(account_name='应收利息'))
        acc_pos.extend(self.acc_pos.find_value_where(account_name='银行存款'))
        acc_pos.extend(self.acc_pos.find_value_where(account_name='证券账户'))
        acc_pos.extend(self.acc_pos.find_value_where(account_name='信用账户'))
        acc_pos.extend(self.acc_pos.find_value_where(account_name='期权账户'))
        from core.func import handle_account_interest_receivable
        self.acc_pos.extend(handle_account_interest_receivable(
            info_board=self.info_board, acc_pos=acc_pos,
            last_acc_pos=last_acc_pos, date=self.current_date, product_range=ManagementProducts,
        ))

        # --------------------------------
        self.log.info_running('读取债券持仓 - 应收债券利息')
        from core.func import handle_bond_interest_receivable
        self.acc_pos.extend(handle_bond_interest_receivable(self.acc_pos, self.current_date))

        # --------------------------------
        # self.log.info_running('读取托管估值表 - 生成应交税费')
        # TODO：应交税费变动 - 托管产品估值表 - 暂时采用托管估值表数据 后期自动计算

        # --------------------------------
        self.log.info_running('读取股利信息表 - 生成应收股利')
        from core.func import handle_dividend_receivable
        data_list = self.info_board.find_dividend_info_list(self.current_date)
        self.log.debug(data_list)
        self.update_acc_pos_to_current_date(self.last_acc_pos.find_value_where(account_name='应收股利'))
        self.acc_pos.extend(handle_dividend_receivable(self.last_acc_pos, self.acc_pos, data_list, self.current_date))

        # 处理第二天的券商提前发放股利
        for entry_acc in List.from_pd(EntryAccount, self.db.read_pd_query(
                DataBaseName.management,
                """SELECT * FROM 会计科目余额表 
                WHERE 日期 = '{}' AND 科目名称 = '证券清算款' AND 二级科目 = '股利收益'
                ;""".format(self.current_date))):
            self.acc_pos.append(AccountPosition(
                product=entry_acc.product, date=self.current_date, institution=entry_acc.base_account,
                account_name='预收递延股利', security_code=entry_acc.note_account, security_name=entry_acc.note_account,
                volume=abs(entry_acc.net_value), currency_origin='RMB', currency='RMB',
            ))

        # 处理税费问题
        for entry_acc in List.from_pd(ValueAddedTaxPayable, self.db.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM 增值税备查簿_预估余额 WHERE 增值税类型 = '价差' AND 日期 = '{}';""".format(self.current_date),
        )):
            if entry_acc.total_tax <= 0.0:
                continue
            else:
                raise NotImplementedError(entry_acc)
            # self.acc_pos.append(AccountPosition(
            #     product=entry_acc.product, date=self.current_date, institution=entry_acc.tax_type,
            #     account_name='应交税费', security_code='-', security_name='-',
            #     volume=abs(entry_acc.total_tax), currency_origin='RMB', currency='RMB',
            # ))

        # --------------------------------
        self.log.info_running('计算当日托管费、外包服务费')
        acc_pos = List()
        acc_pos.extend(self.acc_pos.find_value_where(account_name='其他应付款', institution='托管费'))
        acc_pos.extend(self.acc_pos.find_value_where(account_name='其他应付款', institution='外包服务费'))
        acc_pos.extend(self.acc_pos.find_value_where(account_name='其他应付款', institution='销售服务费'))
        from core.func import handle_product_mandate_fee_payable
        handle_product_mandate_fee_payable(
            info_board=self.info_board, acc_pos=acc_pos, date=self.current_date
        )

        # --------------------------------
        self.log.info_running('计算当日管理费 - 管理费计提')
        from core.func import handle_management_fee_payable
        last_obj_list = self.last_acc_pos.find_value_where(account_name='累计应付管理费')
        self.acc_pos.extend(handle_management_fee_payable(
            info_board=self.info_board,
            last_net_asset_list=self.last_acc_pos.find_value_where(account_name='资产净值'),
            last_management_fee_payable_list=last_obj_list,
            product_range=self.last_acc_pos.collect_attr_set('product'),
            date=self.current_date,
        ))

        # --------------------------------
        self.log.info_running('计算当日管理费 - 管理费返还计提')
        from core.func import handle_management_fee_return
        self.update_acc_pos_to_current_date(
            self.last_acc_pos.find_value_where(account_name='累计应收管理费返还'), zero_drop=False,
        )
        self.acc_pos.extend(handle_management_fee_return(
            last_acc_pos=self.last_acc_pos.find_value_where(account_name='自有产品'),
            acc_pos=self.acc_pos.find_value_where(account_name='累计应收管理费返还'),
            date=self.current_date,
        ))

        acc_pos = List()
        for obj in self.acc_pos:
            if obj.product in ManagementProducts:
                acc_pos.append(obj)

        # for product, p_acc in self.acc_pos.group_by_attr('product').items():
        for product, p_acc in acc_pos.group_by_attr('product').items():
            assert isinstance(p_acc, List)
            if product not in ManagementProducts:
                continue

            # 计算资产净值
            net_value = 0.0
            c_acc = List()
            for obj in p_acc:
                assert isinstance(obj, AccountPosition)
                if obj.account_name in ('资产净值', '实收基金', '单位净值'):
                    continue
                obj.set_attr('market_value', None)
                assert is_valid_float(obj.market_value)
                self.log.debug(obj)
                net_value += obj.market_value
                c_acc.append(obj)

            shares_obj = p_acc.find_value(product=product, account_name='实收基金', )

            self.acc_pos.append(AccountPosition(
                product=product, date=self.current_date, account_name='资产净值',
                institution='-', security_code='-',
                currency_origin=shares_obj.currency_origin, currency=shares_obj.currency,
                volume=net_value,
            ))
            self.log.debug(self.acc_pos[-1])

            net_value_per_share = net_value / shares_obj.volume
            self.acc_pos.append(AccountPosition(
                product=product, date=self.current_date, account_name='单位净值',
                institution='-', security_code='-',
                volume=net_value_per_share,
                currency_origin=shares_obj.currency_origin, currency=shares_obj.currency,
            ))
            self.log.debug(self.acc_pos[-1])

        self.check_mandated_net_value()
        self.check_non_mandated_net_value()

        self.to_db()

    def check_non_mandated_net_value(self):
        """检查非托管估值表 和会计凭证核对"""
        acc_pos = List()
        for obj in self.acc_pos:
            if obj.product in ManagementProducts:
                acc_pos.append(obj)

        entry_value_list = List.from_pd(RawEntryValuation, self.db.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM 会计凭证估值净值表 WHERE 日期 = '{}';""".format(self.current_date)
        ))

        self.log.info('-' * 40)
        # for product in acc_pos.collect_attr_set('product'):
        for product in ManagementProducts:
            log_product_list = list()

            # 忽略托管产品信息
            if self.info_board.check_mandatory(product) is True or product == '稳健22号':
                continue

            entry_value_obj = entry_value_list.find_value(product=product)

            # 核对净资产 左为计算值，右为估值表数据
            left = acc_pos.find_value(product=product, date=self.current_date, account_name='资产净值', ).volume
            right = entry_value_obj.net_asset
            if abs(left - right) > 1.0:
                log_product_list.append('产品 {} 资产净值据出错：计算值 {}, 核对值 {}, 差距 {} {}'.format(
                    product, round(left, 2), round(right, 2), round(round(left, 2) - round(right, 2), 2),
                    round(round(left, 2) - round(right, 2), 2) / right
                ))
            acc_pos.find_value(product=product, date=self.current_date, account_name='资产净值', ).volume = right

            # 核对份额 左为计算值，右为估值表数据
            left = acc_pos.find_value(product=product, date=self.current_date, account_name='实收基金', ).volume
            right = entry_value_obj.fund_shares
            if round(left, 2) != round(right, 2):
                log_product_list.append('产品 {} 份额数据出错：计算值 {}, 核对值 {}, 差距 {}'.format(
                    product, round(left, 2), round(right, 2), abs(round(left, 2) - round(right, 2)),
                ))

            # 核对单位净值
            left = acc_pos.find_value(product=product, date=self.current_date, account_name='单位净值', ).volume
            right = entry_value_obj.net_value
            if round(left, 3) != round(right, 3):
                log_product_list.append('产品 {} 单位净值数据出错：计算值 {}, 核对值 {}, 差距 {}'.format(
                    product, round(left, 3), round(right, 3), abs(round(left, 3) - round(right, 3)),
                ))

            if len(log_product_list) > 0:
                self.log.info('')
                self.log.info_running('{} 和会计凭证估值核对 [{}] {}'.format('-' * 8, product, '-' * 8))
                for msg in log_product_list:
                    self.log.warning(msg)

    def check_mandated_net_value(self):
        """检查托管估值表，核对托管估值表数据"""
        acc_pos = List()
        for obj in self.acc_pos:
            if obj.product in ManagementProducts:
                acc_pos.append(obj)

        value_states = List.from_pd(RawTrusteeshipValuation, self.db.read_pd_query(
            DataBaseName.management,
            """
            SELECT * FROM `原始托管估值表净值表` 
            WHERE `日期` = (SELECT MAX(日期) FROM `原始托管估值表净值表` WHERE `日期` <= '{}')
            ;""".format(self.current_date)
        ))

        self.log.info('-' * 40)
        # for product in acc_pos.collect_attr_set('product'):
        for product in ManagementProducts:
            log_product_list = list()

            # 忽略非托管产品信息
            if self.info_board.check_mandatory(product) is False and product != '稳健22号':
                continue
            if product == '久铭全球（开曼）':
                continue
            try:
                value = value_states.find_value(product=product)
            except ValueError:
                log_product_list.append('估值表产品 {} {} 信息缺失\n{}'.format(product, self.current_date, value_states))
                continue

            # 核对净资产 左为计算值，右为估值表数据
            left = acc_pos.find_value(product=product, date=self.current_date, account_name='资产净值', ).volume
            right = value.net_asset
            if abs(left - right) > 1.0:
                log_product_list.append('产品 {} 资产净值据出错：计算值 {}, 核对值 {}, 差距 {} {}'.format(
                    product, round(left, 2), round(right, 2), round(round(left, 2) - round(right, 2), 2),
                    round(round(left, 2) - round(right, 2), 2) / right,
                ))
            acc_pos.find_value(product=product, date=self.current_date, account_name='资产净值', ).volume = right

            # 核对份额 左为计算值，右为小何估值表数据
            # net_shares =
            left = acc_pos.find_value(product=product, date=self.current_date, account_name='实收基金', ).volume
            right = value.fund_shares
            if round(left, 2) != round(right, 2):
                log_product_list.append('产品 {} 份额数据出错：计算值 {}, 核对值 {}, 差距 {}'.format(
                    product, round(left, 2), round(right, 2), abs(round(left, 2) - round(right, 2)),
                ))
            acc_pos.find_value(product=product, date=self.current_date, account_name='实收基金', ).volume = right

            # 核对单位净值
            # net_value_per_unit = \
            left = acc_pos.find_value(product=product, date=self.current_date, account_name='单位净值', ).volume
            right = value.net_value
            if round(left, 3) != round(right, 3):
                log_product_list.append('产品 {} 单位净值数据出错：计算值 {}, 核对值 {}, 差距 {}'.format(
                    product, round(left, 3), round(right, 3), abs(round(left, 3) - round(right, 3)),
                ))
            acc_pos.find_value(product=product, date=self.current_date, account_name='单位净值', ).volume = right

            if len(log_product_list) > 0:
                self.log.info('')
                self.log.info_running('和托管估值表核对 {} [{}] {}'.format('-' * 8, product, '-' * 8))
                for msg in log_product_list:
                    if '单位净值' in msg:
                        self.log.error(msg)
                    else:
                        self.log.warning(msg)

    def to_db(self):
        acc_pos = List()
        for product in ManagementProducts:
            acc_pos.extend(self.acc_pos.find_value_where(product=product))
        # 储存至缓存
        acc_pos.to_pd().to_sql(AccountPosition.__name__, self.env.cache_db.engine, if_exists='replace')
        # 储存至数据库
        if self.simulation is False:
            for product in ManagementProducts:
                self.db.execute(
                    DataBaseName.management,
                    """DELETE FROM 产品余额持仓表 WHERE 日期 = '{}' AND 产品 = '{}';""".format(
                        self.current_date, product))
                for obj in self.acc_pos.find_value_where(product=product):
                    assert isinstance(obj, AccountPosition)
                    self.db.execute(DataBaseName.management, obj.form_insert_sql('产品余额持仓表'))
        else:
            for product in ManagementProducts:
                self.db.execute(
                    DataBaseName.management,
                    """DELETE FROM 产品模拟余额持仓表 WHERE 日期 = '{}' AND 产品 = '{}';""".format(
                        self.current_date, product))
                for obj in self.acc_pos.find_value_where(product=product):
                    assert isinstance(obj, AccountPosition)
                    self.db.execute(DataBaseName.management, obj.form_insert_sql('产品模拟余额持仓表'))

    def output_market_scale_sheet(self):
        from output.MarketScaleSheet import output_market_scale_sheet

        # 输出产品规模统计表
        self.log.info_running('输出产品规模统计表')
        output_market_scale_sheet(self.info_board, self.current_date, self.path_dict['文件输出'])

    def output_valuation_sheet(self):
        from output.ValuationSheet import output_valuation_sheet

        # 输出会计估值表
        for product in ManagementProducts:
            # 忽略托管产品信息
            if self.info_board.check_mandatory(product) is True:
                continue
            output_valuation_sheet(self.info_board, product, self.current_date, self.path_dict['文件输出'])

    def output_summary_sheet(self):
        """ 输出简单对比表格 """
        from os import path, makedirs
        from xlsxwriter import Workbook

        makedirs(path.join(self.path_dict['文件输出'], ), exist_ok=True)
        book = Workbook(filename=path.join(self.path_dict['文件输出'], '{} 估值汇总表.xlsx'.format(self.current_date)))

        excel_formats = {
            'bold': book.add_format({'bold': True, }), 'center': book.add_format({'align': 'center'}),
            'date': book.add_format({'num_format': 'yyyy-mm-dd'}),
            'number2': book.add_format({'num_format': '#,##0.00'}),
            'number3': book.add_format({'num_format': '#,##0.000'}),
            'number4': book.add_format({'num_format': '#,##0.0000'}),
            'percentage': book.add_format({'num_format': '0.00%'}),
            'bold_number2': book.add_format({'num_format': '#,##0.00', 'bold': True, }, ),
            'bold_number3': book.add_format({'num_format': '#,##0.000', 'bold': True, }, ),
        }
        sheet = book.add_worksheet(name='Sheet1')
        sheet.set_column(0, 5, width=20, )

        content_list = List.from_pd(AccountPosition, self.db.read_pd_query(DataBaseName.management, """
        SELECT * FROM 产品余额持仓表 WHERE 日期 = '{}';""".format(self.current_date)))

        line = 0
        sheet.write_string(line, 0, '非托管部分', cell_format=excel_formats['bold'])

        line += 1
        column_list = [
            '基金名称', '基金代码', '基金份额净值', '基金份额', '基金资产净值',
        ]
        for i in range(len(column_list)):
            sheet.write_string(line, i, column_list[i], cell_format=excel_formats['bold'])

        product_id_list = list()
        for product in content_list.collect_attr_set('product'):
            # 忽略托管产品信息
            if self.info_board.check_mandatory(product) is True or product == '稳健22号':
                continue
            else:
                product_id_list.append(self.info_board.find_product_code_by_name(product))
        product_id_list.sort()

        for product_id in product_id_list:
            product = self.info_board.find_product_info_by_code(product_id).name
            line += 1
            sheet.write_string(line, 0, product)
            sheet.write_string(line, 1, product_id)
            product_obj = content_list.find_value(product=product, account_name='单位净值')
            sheet.write_number(line, 2, round(product_obj.volume, 3), cell_format=excel_formats['number3'])
            product_obj = content_list.find_value(product=product, account_name='实收基金')
            sheet.write_number(line, 3, product_obj.market_value, cell_format=excel_formats['number2'])
            product_obj = content_list.find_value(product=product, account_name='资产净值')
            sheet.write_number(line, 4, product_obj.market_value, cell_format=excel_formats['number2'])

        content_list = List.from_pd(RawTrusteeshipValuation, self.db.read_pd_query(DataBaseName.management, """
        SELECT * FROM 原始托管估值表净值表 WHERE 日期 = '{}';""".format(self.current_date)))

        line += 2
        sheet.write_string(line, 0, '托管部分', cell_format=excel_formats['bold'])

        line += 1
        column_list = [
            '基金名称', '基金代码', '基金份额净值', '基金份额', '基金资产净值',
        ]
        for i in range(len(column_list)):
            sheet.write_string(line, i, column_list[i], cell_format=excel_formats['bold'])

        product_id_list = list()
        for product in content_list.collect_attr_set('product'):
            product_id_list.append(self.info_board.find_product_code_by_name(product))
        product_id_list.sort()

        for product_id in product_id_list:
            product = self.info_board.find_product_info_by_code(product_id).name
            if product == '久铭专享1号':
                product = '专享1号'
            product_obj = content_list.find_value(product=product)
            line += 1
            sheet.write_string(line, 0, product)
            sheet.write_string(line, 1, product_id)
            sheet.write_number(line, 2, round(product_obj.net_value, 3), cell_format=excel_formats['number3'])
            sheet.write_number(line, 3, product_obj.fund_shares, cell_format=excel_formats['number2'])
            sheet.write_number(line, 4, product_obj.net_asset, cell_format=excel_formats['number2'])

        book.close()


if __name__ == '__main__':
    from jetend.structures import MySQL, Sqlite

    ManagementProducts = (
        # 非托管部分
        '久铭2号',
        '久铭3号',
        '全球1号',
        '收益1号',
        '双盈1号',
        '稳利2号',
        '稳健2号',
        '稳健3号',
        '稳健5号',
        '稳健6号',
        '稳健7号',
        '稳健8号',
        '稳健9号',
        '稳健10号',
        '稳健11号',
        '稳健12号',
        '稳健15号',
        '稳健16号',
        '稳健17号',
        '稳健18号',
        '稳健19号',
        '稳健21号',
        '稳健31号',
        '稳健32号',
        '稳健33号',
        # 托管部分
        '久铭1号',
        '久铭5号',
        '久铭6号',
        '久铭7号',
        '久铭8号',
        '久铭9号',
        '久铭10号',
        # '稳健1号',
        '稳健22号',
        '稳健23号',
        '久盈2号',
        '收益2号',
        '创新稳健1号',
        '创新稳健2号',
        '创新稳健5号',
        '创新稳健6号',
        '创新稳健3号',
    )

    # 数据路径
    config_path_dict = {
        '文件输出': r'C:\Users\Administrator\Downloads\程序文件输出',
    }

    env_inst = Modules()

    # from jetend.modules.jmWind import WindClient
    # w = WindClient('192.168.1.184').start()
    # env_inst.deploy_module('wind_engine', w, w.stop)
    from WindPy import w
    w.start()
    env_inst.deploy_module('wind_engine', w, )

    env_inst.deploy_module('sql_db', MySQL(server='192.168.1.31', port=3306, username='root', passwd='jm3389', ))
    env_inst.deploy_module('cache_db', Sqlite(os.path.join(env_inst.root_path, 'cache.db')))

    checker = DailyValuation(config_path_dict, env_inst)

    checker.set_simulation_calculation()
    # checker.set_actual_calculation()

    RUNNING_DATE = datetime.date(2019, 9, 25)

    checker.set_current_working_date(RUNNING_DATE)

    checker.derive_holdings()

    checker.derive_net_value()

    checker.output_market_scale_sheet()

    # from core.Monitor import Monitor
    # monitor = Monitor(env_inst)
    # monitor.compare_by_date(RUNNING_DATE)

    env_inst.exit()
