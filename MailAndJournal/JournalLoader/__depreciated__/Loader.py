# -*- encoding: UTF-8 -*-
import datetime
import os

from jetend.Constants import DataBaseName
from jetend.structures import List, MySQL
from jetend.DataCheck import *
from jetend.jmSheets import *


from Abstracts import AbstractInstitution
from institutions.AnXin import AnXin
from institutions.CaiTong import CaiTong
from institutions.ChangJiang import ChangJiang
from institutions.GuoJun import GuoJun
from institutions.HaiTong import HaiTong
from institutions.HuaTai import HuaTai
from institutions.ShenWan import ShenWan
from institutions.XingYe import XingYe
from institutions.YinHe import YinHe
from institutions.ZhaoShang import ZhaoShang
from institutions.ZhongJin import ZhongJin
from institutions.ZhongTai import ZhongTai
from institutions.ZhongXin import ZhongXin
from institutions.ZhongXinJianTou import ZhongXinJianTou
from institutions.DongFang import DongFang
from institutions.DeBang import DeBang
from Limits import *


class JournalLoader(object):
    normal_loader_map = {
        '安信普通账户': AnXin,
        '财通普通账户': CaiTong,
        '长江普通账户': ChangJiang,
        '国君普通账户': GuoJun,
        '海通普通账户': HaiTong,
        '华泰普通账户': HuaTai,
        '申万普通账户': ShenWan,
        '兴业普通账户': XingYe,
        '招商普通账户': ZhaoShang,
        '中金普通账户': ZhongJin,
        '中泰普通账户': ZhongTai, '中信普通账户': ZhongXin, '中信建投普通账户': ZhongXinJianTou,
        '东方普通账户': DongFang,
        '德邦普通账户': DeBang,

    }
    margin_loader_map = {
        '安信两融账户': AnXin,
        '华泰两融账户': HuaTai,
        # '国君两融账户': GuoJun,
        '招商两融账户': ZhaoShang,
        '中信两融账户': ZhongXin,
        '长江两融账户': ChangJiang
    }
    swap_loader_map = {
        '中信港股': ZhongXin, '中信美股': ZhongXin,
    }
    future_loader_map = {
        # '长江期货账户': ChangJiang,
        # '国君期货账户': GuoJun,
        # '建信期货账户': None,
        # '永安期货账户': None,
        # '安信期货账户': AnXin
    }
    option_loader_map = {
        '国君期权账户': GuoJun,
        '海通期权账户': HaiTong,
        '华泰期权账户': HuaTai,
        '兴业期权账户': XingYe,
        '中泰期权账户': ZhongTai,
        '中信期权账户': ZhongXin,
    }
    valuation_loader_map = {
    }
    non_loader_map = {
        '多余',
        '国君客户结算单', '国君期货账户', '建信期货账户', '永安期货账户', '长江期货账户',
        '安信期货账户',
        '国君两融账户',   # TODO: 暂时不读！！！
        '浦睿1号',   # TODO: 暂时不读！！！
        '申万两融账户',  # TODO: 暂时不读！！！
        '银河普通账户',
        '国信普通账户', # TODO: 暂时不读！！！
    }

    def __init__(self, db: MySQL):
        from jetend import get_logger
        self.log = get_logger(self.__class__.__name__)
        self.__path__ = None
        self.current_date = None                        # 当前日期
        self.last_date = None
        self.db = db

        self.normal_account, self.normal_position, self.normal_flow = List(), List(), List()
        self.margin_account, self.margin_position, self.margin_flow = List(), List(), List()
        self.future_account, self.future_position, self.future_flow = List(), List(), List()
        self.valuation_essential = List()
        self.margin_liabilities = List()

        self.swap_account, self.swap_position = List(), List()

        self.__critical_log__ = list()              # 储存需要严重注意的信息，在结束时日志输出

    def load_account_statement(self, folder: str, current_date: datetime.date, last_date: datetime.date):
        assert os.path.exists(folder), folder
        self.__path__ = folder
        assert current_date > last_date, '{} {}'.format(current_date, last_date)
        self.current_date = current_date  # 当前日期
        self.last_date = last_date

        folder_list = os.listdir(folder)
        self.log.debug(folder_list)
        for sub_folder in folder_list:
            self.log.info_running('reading folder {}'.format(sub_folder))
            if not os.path.isdir(os.path.join(self.__path__, sub_folder)):
                continue
            elif sub_folder in self.normal_loader_map:
                method = self.normal_loader_map[sub_folder]
                assert issubclass(method, AbstractInstitution), '{}'.format(method)
                assert sub_folder in method.folder_institution_map, '{}'.format(sub_folder)
                loaded_result = method.load_normal(os.path.join(self.__path__, sub_folder), self.current_date)
                assert isinstance(loaded_result, dict), loaded_result
                institution = method.folder_institution_map[sub_folder]
                for product, sub_loaded in loaded_result.items():
                    # self.log.debug_running(product, str(sub_loaded))
                    assert isinstance(sub_loaded, dict), sub_loaded
                    flow_list = List.from_dict_list(RawNormalFlow, sub_loaded['flow'])
                    pos_list = List.from_dict_list(RawNormalPosition, sub_loaded['position'])
                    last_pos_list = List.from_pd(RawNormalPosition, self.fetch_last_pos_list(
                        '原始普通持仓记录', product, self.last_date, institution
                    ))
                    self.check_flow_pos_match(sub_folder, product, flow_list, pos_list, last_pos_list)
                    self.normal_flow.extend(flow_list)
                    self.normal_position.extend(pos_list)
                    acc_obj = RawNormalAccount.from_dict(sub_loaded['account'])
                    last_acc_list = List.from_pd(RawNormalAccount, self.fetch_last_acc(
                        '原始普通账户资金记录', product, self.last_date, institution, sub_folder
                    ))
                    self.check_flow_acc_match(sub_folder, product, flow_list, acc_obj, last_acc_list)
                    self.normal_account.append(acc_obj)
                    # self.log.debug(pos_list)

            elif sub_folder in self.margin_loader_map:
                method = self.margin_loader_map[sub_folder]
                assert issubclass(method, AbstractInstitution), '{}'.format(method)
                assert sub_folder in method.folder_institution_map, '{}'.format(sub_folder)
                loaded_result = method.load_margin(os.path.join(self.__path__, sub_folder), self.current_date)
                assert isinstance(loaded_result, dict), loaded_result
                institution = method.folder_institution_map[sub_folder]
                for product, sub_loaded in loaded_result.items():
                    assert isinstance(sub_loaded, dict), sub_loaded
                    flow_list = List.from_dict_list(RawMarginFlow, sub_loaded['flow'])
                    pos_list = List.from_dict_list(RawMarginPosition, sub_loaded['position'])
                    last_pos_list = List.from_pd(RawMarginPosition, self.fetch_last_pos_list(
                        '原始两融持仓记录', product, self.last_date, institution
                    ))
                    # self.log.debug_running(product, str(last_pos_list))
                    # self.log.debug_running(str(sub_loaded))
                    self.check_flow_pos_match(sub_folder, product, flow_list, pos_list, last_pos_list)
                    self.margin_flow.extend(flow_list)
                    self.margin_position.extend(pos_list)
                    acc_obj = RawMarginAccount.from_dict(sub_loaded['account'])
                    last_acc_list = List.from_pd(RawMarginAccount, self.fetch_last_acc(
                        '原始两融账户资金记录', product, self.last_date, institution, sub_folder
                    ))
                    lia_list = List.from_dict_list(RawMarginLiability, sub_loaded['liabilities'])
                    self.log.debug_running(product)
                    self.check_flow_acc_match(sub_folder, product, flow_list, acc_obj, last_acc_list)
                    self.margin_account.append(acc_obj)
                    self.margin_liabilities.extend(lia_list)

            elif sub_folder in self.swap_loader_map:
                method = self.swap_loader_map[sub_folder]
                assert issubclass(method, AbstractInstitution), '{}'.format(method)
                assert sub_folder in method.folder_institution_map, '{}'.format(sub_folder)
                loaded_result = method.load_swap(os.path.join(self.__path__, sub_folder), self.current_date)
                assert isinstance(loaded_result, dict), loaded_result
                # institution = method.folder_institution_map[sub_folder]
                for product, sub_loaded in loaded_result.items():
                    if not isinstance(sub_loaded, dict):
                        continue
                    acc_obj = RawSwapAccount(**sub_loaded['balance_dict'])
                    acc_obj.update(sub_loaded['calculation_dict'])
                    self.swap_account.append(acc_obj)
                    pos_list = List.from_dict_list(RawSwapPosition, sub_loaded['underlying_list'])
                    self.swap_position.extend(pos_list)

            elif sub_folder in self.future_loader_map:
                # TODO: 非托管暂时没有期货交易，尽快完成
                method = self.future_loader_map[sub_folder]
                assert issubclass(method, AbstractInstitution), '{}'.format(method)
                assert sub_folder in method.folder_institution_map, '{}'.format(sub_folder)
                loaded_result = method.load_future(os.path.join(self.__path__, sub_folder), self.current_date)
                assert isinstance(loaded_result, dict), loaded_result
                institution = method.folder_institution_map[sub_folder]
                for product, sub_loaded in loaded_result.items():
                    assert isinstance(sub_loaded, dict), sub_loaded
                    flow_list = List.from_dict_list(RawFutureFlow, sub_loaded['flow'])
                    pos_list = List.from_dict_list(RawFuturePosition, sub_loaded['position'])
                    last_pos_list = List.from_pd(RawFuturePosition, self.fetch_last_pos_list(
                        '原始期货持仓记录', product, self.last_date, institution
                    ))
                    # self.log.debug_running(product, str(last_pos_list))
                    # self.log.debug_running(str(sub_loaded))
                    self.check_flow_pos_match(sub_folder, product, flow_list, pos_list, last_pos_list)
                    self.future_flow.extend(flow_list)
                    self.future_position.extend(pos_list)
                    acc_obj = RawFutureAccount.from_dict(sub_loaded['account'])
                    last_acc_list = List.from_pd(RawFutureAccount, self.fetch_last_acc(
                        '原始期货账户资金记录', product, self.last_date, institution, sub_folder
                    ))
                    # self.check_flow_acc_match(sub_folder, product, flow_list, acc_obj, last_acc_list)
                    self.future_account.append(acc_obj)
            elif sub_folder in self.option_loader_map:
                # TODO: 非托管暂时没有期权交易，尽快完成
                continue
            elif sub_folder == '托管估值表':
                continue
            elif sub_folder in self.non_loader_map:
                continue
            else:
                raise NotImplementedError(sub_folder)

        # 储存账户资金信息
        self.clear_duplicated_in_db('原始普通账户资金记录')
        self.insert_to_db('原始普通账户资金记录', self.normal_account)
        self.clear_duplicated_in_db('原始普通流水记录')
        self.insert_to_db('原始普通流水记录', self.normal_flow)
        self.clear_duplicated_in_db('原始普通持仓记录')
        self.insert_to_db('原始普通持仓记录', self.normal_position)

        self.clear_duplicated_in_db('原始两融账户资金记录')
        self.insert_to_db('原始两融账户资金记录', self.margin_account)
        self.clear_duplicated_in_db('原始两融持仓记录')
        self.insert_to_db('原始两融持仓记录', self.margin_position)
        self.clear_duplicated_in_db('原始两融流水记录')
        self.insert_to_db('原始两融流水记录', self.margin_flow)
        self.clear_duplicated_in_db('原始两融负债记录')
        self.insert_to_db('原始两融负债记录', self.margin_liabilities)

        self.clear_duplicated_in_db('原始收益互换持仓记录')
        self.insert_to_db('原始收益互换持仓记录', self.swap_position)
        self.clear_duplicated_in_db('原始收益互换账户资金记录')
        self.insert_to_db('原始收益互换账户资金记录', self.swap_account)

        self.clear_duplicated_in_db('原始期货持仓记录')
        self.insert_to_db('原始期货持仓记录', self.future_position)
        self.clear_duplicated_in_db('原始期货流水记录')
        self.insert_to_db('原始期货流水记录', self.future_flow)
        self.clear_duplicated_in_db('原始期货账户资金记录')
        self.insert_to_db('原始期货账户资金记录', self.future_account)

    def load_valuation_sheet(self, folder: str, current_date: datetime.date, last_date: datetime.date):
        assert os.path.exists(folder), folder
        self.__path__ = folder
        assert current_date > last_date, '{} {}'.format(current_date, last_date)
        self.current_date = current_date  # 当前日期
        self.last_date = last_date

        folder_list = os.listdir(folder)
        self.log.debug(folder_list)

        for sub_folder in folder_list:
            self.log.info_running('reading folder {}'.format(sub_folder))
            if not os.path.isdir(os.path.join(self.__path__, sub_folder)):
                continue
            elif sub_folder in self.normal_loader_map:
                continue
            elif sub_folder in self.margin_loader_map:
                continue
            elif sub_folder in self.swap_loader_map:
                continue
            elif sub_folder in self.future_loader_map:
                continue
            elif sub_folder in self.option_loader_map:
                continue
            elif sub_folder == '托管估值表':
                for file_name in os.listdir(os.path.join(folder, sub_folder)):
                    if file_name.startswith('.') or file_name.startswith('~'):
                        continue
                    if '创新' in file_name:
                        continue
                    product = None
                    for name in PRODUCT_NAME_RANGE:
                        if name in file_name:
                            product = name
                    assert product is not None, file_name
                    if product in self.valuation_loader_map:
                        raise NotImplementedError
                    else:
                        method = ZhaoShang
                    assert issubclass(method, AbstractInstitution), '{}'.format(method)
                    loaded_result = method.load_valuation_table(
                        os.path.join(folder, sub_folder, file_name), self.current_date
                    )
                    self.valuation_essential.append(RawTrusteeshipValuation(**loaded_result))
            elif sub_folder in self.non_loader_map:
                continue
            else:
                raise NotImplementedError(sub_folder)

        self.clear_duplicated_in_db('原始托管估值表净值表')
        self.insert_to_db('原始托管估值表净值表', self.valuation_essential)

    def fetch_last_acc(self, table_name: str, product: str, date: datetime.date, institution: str, account_type: str):
        return self.db.read_pd_query(
            DataBaseName.management,
            """
            SELECT * FROM `{}` 
            WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}' AND 账户类型 = '{}'
            ;""".format(table_name, product, date, institution, account_type)
        )

    def fetch_last_pos_list(self, table_name: str, product: str, date: datetime.date, institution: str):
        return self.db.read_pd_query(
            DataBaseName.management,
            """
            SELECT * FROM `{}` 
            WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}'
            ;""".format(table_name, product, date, institution)
        )

    def check_flow_pos_match(self, folder: str, product: str, flow_list: List, pos_list: List, last_pos_list: List):
        """验证前日持仓模拟流水操作后与今日持仓比较"""
        security_code_set = set()
        security_code_set.update(pos_list.collect_attr_set('security_code'))
        security_code_set.update(last_pos_list.collect_attr_set('security_code'))

        if '' in security_code_set:
            security_code_set.remove('')
        if None in security_code_set:
            security_code_set.remove(None)

        for security_code in security_code_set:
            if security_code is None or security_code == '':
                continue

            this_pos = pos_list.find_value_where(security_code=security_code)
            if len(this_pos) == 1:
                this_pos = this_pos[0]
                if isinstance(this_pos, RawNormalPosition):
                    end_position = float_check(this_pos.hold_volume)
                elif isinstance(this_pos, RawFuturePosition):
                    assert abs(float_check(this_pos.short_position)) < 0.01, this_pos
                    end_position = float_check(this_pos.long_position)
                else:
                    raise NotImplementedError(this_pos)
            elif len(this_pos) == 0:
                this_pos = None
                end_position = 0.0
            else:
                print(folder, product)
                print(this_pos)
                raise RuntimeError('存在重复持仓信息')

            last_pos = last_pos_list.find_value_where(security_code=security_code)
            if len(last_pos) == 1:
                last_pos = last_pos[0]
                if isinstance(last_pos, RawNormalPosition):
                    calculate_position = float_check(last_pos.hold_volume)
                elif isinstance(last_pos, RawFuturePosition):
                    calculate_position = float_check(last_pos.long_position)
                else:
                    raise NotImplementedError(last_pos)
            elif len(last_pos) == 0:
                if this_pos is None:
                    raise RuntimeError('出现不应该出现的证券代码：{}'.format(security_code))
                else:
                    last_pos = None
                    calculate_position = 0.0
            else:
                print(folder, product)
                print(last_pos)
                raise RuntimeError('存在重复持仓信息')

            for flow in flow_list.find_value_where(security_code=security_code):
                if isinstance(flow, RawNormalFlow):
                    if '买入' in flow.trade_class or flow.trade_class in NORMAL_DIRECTION_BUY_TRADE_CLASS:
                        calculate_position += abs(flow.trade_volume)
                    elif '卖出' in flow.trade_class or flow.trade_class in NORMAL_DIRECTION_SELL_TRADE_CLASS:
                        calculate_position -= abs(flow.trade_volume)
                    else:
                        raise NotImplementedError(flow)
                elif isinstance(flow, RawFutureFlow):
                    if '买' in flow.trade_class or flow.trade_class in FUTURE_DIRECTION_BUY_TRADE_CLASS:
                        calculate_position += abs(flow.trade_volume)
                    elif '卖' in flow.trade_class or flow.trade_class in FUTURE_DIRECTION_SELL_TRADE_CLASS:
                        calculate_position -= abs(flow.trade_volume)
                    else:
                        raise NotImplementedError(flow)
                else:
                    raise NotImplementedError(flow)

            if is_different_float(calculate_position, end_position):
                info = "\n\treaded: {},\n\tcalculated: {},\n\tlast: {},\n\tflow: {}".format(
                    this_pos, calculate_position, last_pos, flow_list.find_value_where(security_code=security_code)
                )
                if last_pos is None:
                    self.log.warning('读取账户持仓与流水计算持仓差距过大，可能源于没有前日持仓历史 {}'.format(info))
                else:
                    self.log.warning('读取账户持仓与流水计算持仓差距超过0.1%  {}'.format(security_code) + info)

    def check_flow_acc_match(self, folder: str, product: str, flow_list: List, acc_obj, last_acc_list: List):
        """验证前日资金经过流水操作后与今日资金比较"""
        if len(last_acc_list) == 1:
            last_acc = last_acc_list[0]
            if isinstance(last_acc, (RawNormalAccount, RawMarginAccount)):
                calculation_cash = last_acc.cash_amount
            else:
                raise NotImplementedError(last_acc)
        elif len(last_acc_list) == 0:
            last_acc = None
            calculation_cash = 0.0
        else:
            print(product, folder)
            raise RuntimeError('出现重复账户信息')

        if isinstance(acc_obj, (RawNormalAccount, RawMarginAccount)):
            end_cash = float_check(acc_obj.cash_amount)
        else:
            raise NotImplementedError(acc_obj)
        assert is_valid_float(end_cash), str(acc_obj)

        for flow in flow_list:
            if isinstance(flow, (RawNormalFlow, RawMarginFlow)):
                calculation_cash += float_check(flow.cash_move)
            else:
                raise NotImplementedError(flow)

        info = "\n\treaded: {},\n\tcalculated: {},\n\tlast: {}, \n\tflow: {}".format(
            acc_obj, calculation_cash, last_acc, flow_list)
        if calculation_cash < - 0.5:
            self.log.error('计算账户现金为负 {}'.format(info))
        elif is_different_float(calculation_cash, end_cash, gap=max(0.001 * end_cash, 1)):
            self.log.error('读取账户现金与流水计算差距超过0.1% -> {} {}'.format(calculation_cash - end_cash, info))
        else:
            pass

    def insert_to_db(self, table_name: str, data_list: List):
        if len(data_list) > 0:
            self.to_csv(table_name, data_list)
            for obj in data_list:
                sql = getattr(obj, 'form_insert_sql').__call__(table_name)
                try:
                    self.db.execute(DataBaseName.management, sql)
                except BaseException as i_e:
                    print(obj)
                    raise i_e
        self.log.info_running('储存当日', table_name)

    def clear_duplicated_in_db(self, table_name: str):
        # pass
        self.db.execute(
            DataBaseName.management,
            "DELETE FROM {} WHERE 日期 = '{}'".format(table_name, self.current_date),
        )

    def to_csv(self, table_name: str, data: List):
        if len(data) > 0:
            root_path = os.path.abspath(os.path.dirname(__file__))
            data.to_pd().to_csv(os.path.join(root_path, 'temp', '{}_{}.csv').format(
                self.current_date.strftime('%Y-%m-%d'), table_name,
            ), encoding='gb18030')


if __name__ == '__main__':

    base_folder = r'C:\NutStore\久铭产品交割单\2019年'
    current_day = datetime.date(2019, 7, 2)
    last_day = datetime.date(2019, 7, 1)

    loader = JournalLoader(MySQL('root', 'jm3389', '192.168.1.31', 3306))
    # ---- ---- #

    loader.load_account_statement(
        os.path.join(base_folder, '久铭产品交割单{}'.format(current_day.strftime('%Y%m%d'))),
        # r'D:\Documents\久铭产品交割单20190621-sp\久铭产品交割单20190621-sp',
        current_day, last_day,
    )
    loader.load_valuation_sheet(
        os.path.join(base_folder, '久铭产品交割单{}'.format(current_day.strftime('%Y%m%d'))),
        # r'D:\Documents\久铭产品交割单20190621-sp\久铭产品交割单20190621-sp',
        current_day, last_day,
    )
