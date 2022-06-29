# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import os
import re
import xlrd
import datetime

import pandas as pd

from xlrd.biffh import XLRDError

from jetend.structures import ExcelMapper, List, MySQL, Sqlite
from jetend.Constants import DataBaseName
from jetend.jmSheets import *

from core.Interface import AbstractLoader
from loader.institutions.AnXin import AnXin
from loader.institutions.ChangJiang import ChangJiang
from loader.institutions.DeBang import DeBang
from loader.institutions.DongFang import DongFang
from loader.institutions.GuoJun import GuoJun
from loader.institutions.GuoXin import GuoXin
from loader.institutions.HuaTai import HuaTai
from loader.institutions.ShenWan import ShenWan
from loader.institutions.XingYe import XingYe
from loader.institutions.ZhongJin import ZhongJin
from loader.institutions.ZhaoShang import ZhaoShang
from loader.institutions.ZhongXin import ZhongXin
from modules.Checker import *


class TradeFlowLoader(object):
    institution_loader_map = {
        # 普通账户
        '安信证券': AnXin, '长江证券': ChangJiang, '德邦证券': DeBang, '东方证券': DongFang,
        '华泰证券': HuaTai, '国信证券': GuoXin,
        '国君证券': GuoJun, '申万证券': ShenWan,
        '兴业证券': XingYe,
        '中金证券': ZhongJin, '招商证券': ZhaoShang, '中信证券': ZhongXin,
        # 港股通
        '兴业证券港股通': XingYe,
        # 期货账户
        '国投安信': AnXin, '安信期货': AnXin, '长江期货': ChangJiang,
    }

    def __init__(self, db: MySQL, folder_path: str):
        from jetend import get_logger
        from jetend.modules.jmInfoBoard import jmInfoBoard
        from jetend.modules.jmMarketBoard import jmMarketBoard
        self.log = get_logger(self.__class__.__name__)
        self.db = db
        self.info_board = jmInfoBoard(self.db)
        from WindPy import w
        w.start()
        self.market_board = jmMarketBoard(w, Sqlite())

        self.normal_flow = List()       # 普通
        self.margin_flow = List()       # 两融
        self.future_flow = List()       # 期货

        self.current_date = None
        assert os.path.exists(folder_path), '当日交易流水路径 {} 不存在'.format(folder_path)
        self.__path__ = folder_path

    def load_simple_output_flow(self, date: datetime.date):
        """载入陈田田的交易流水 -> List(TradeFlow, )"""
        folder_path = os.path.join(self.__path__, '当日成交{}'.format(date.strftime('%Y%m%d')))
        assert os.path.exists(folder_path), '当日成交文件夹 {} 不存在'.format(folder_path)
        self.current_date = date

        # ---- [读取流水] ----
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            # 忽略隐藏文件和临时文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue

            # 需要手动解压压缩文件包
            if file_name.lower().endswith('rar') or file_name.lower().endswith('zip'):
                raise RuntimeError('存在文件 {}，请确认该文件已正确解压'.format(file_name))

            # 逐个处理excel文件
            self.log.debug_running('loading', file_name)
            try:
                product, account_type, institution = re.search(
                    r'(\D+\d+[号指数]+)([股票两融期货美港收益互换]+)(\w+)', file_name, flags=re.I,
                ).groups()
            except AttributeError as f_a_e:
                self.log.error(file_name)
                raise f_a_e

            if '久铭创新' in product:
                product = product.replace('久铭', '')

            try:
                loader_cls = self.institution_loader_map[institution]
            except KeyError:
                raise NotImplementedError(file_name)
            assert issubclass(loader_cls, AbstractLoader), loader_cls.__name__

            file_type = file_name.lower().split('.')[-1]
            if file_type in ('xls', ):
                try:
                    file_content = xlrd.open_workbook(file_path, encoding_override='gb18030')
                except XLRDError:
                    content_list = list()
                    content_file = open(file_path, mode='r', ).read()
                    for content_line in content_file.split('\n'):
                        line_list = list()
                        for content_cell in content_line.split('\t'):
                            if re.match(r'=\"([\w\W]*)\"', content_cell):
                                line_list.append(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
                                # print(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
                            elif len(re.sub(r'[Ee\d.,:+]', '', content_cell)) == 0:     # 数字表达
                                line_list.append(content_cell)
                            elif len(re.sub(r'\W', '', content_cell)) == 0:
                                line_list.append('-')
                            elif len(re.sub(r'[\w()]', '', content_cell)) == 0:
                                line_list.append(content_cell)
                            elif len(re.sub(r'\w', '', content_cell.replace(' ', ''))) == 0:
                                line_list.append(content_cell.replace(' ', ''))
                            else:
                                raise NotImplementedError('{}\n{}'.format(content_cell, content_line))
                        content_list.append('|'.join(line_list))
                    file_content = '\n'.join(content_list)
            elif file_type in ('csv', ):
                file_content = pd.read_csv(os.path.join(folder_path, file_name), encoding='gb18030')
            else:
                raise NotImplementedError(file_name)

            if account_type == '股票':
                # try:
                #     loaded_result = loader_cls.load_normal_excel(file_path, product, date, institution)
                # except NotImplementedError:
                #     loaded_result = loader_cls.load_normal_text(file_content, product, date, institution)
                if isinstance(file_content, str):
                    loaded_result = loader_cls.load_normal_text(file_content, product, date, institution)
                elif isinstance(file_content, (pd.DataFrame, xlrd.Book)):
                    loaded_result = loader_cls.load_normal_excel(file_path, product, date, institution)
                else:
                    raise NotImplementedError('{} {}'.format(type(file_content), file_content))
                fee_rate_institution = '{}普通'.format(institution.replace('证券', ''))
                for flow in loaded_result:
                    fee_amount = self.info_board.calculate_security_trade_fee(
                        product, date, fee_rate_institution, flow['security_code'], flow['trade_amount'])
                    if flow['trade_direction'] == TRADE_DIRECTION_BUY:
                        flow['cash_move'] = - abs(flow['trade_amount']) - fee_amount
                    elif flow['trade_direction'] == TRADE_DIRECTION_SELL:
                        flow['cash_move'] = abs(flow['trade_amount']) - fee_amount
                    else:
                        raise NotImplementedError(flow)
                    self.log.debug(flow)
                self.normal_flow.extend(List.from_dict_list(EstimatedNormalTradeFlow, loaded_result))

            elif account_type == '两融':
                loaded_result = loader_cls.load_simple_margin(
                    os.path.join(folder_path, file_name), product, date, institution,
                )
                fee_rate_institution = '{}两融'.format(institution.replace('证券', ''))
                for flow in loaded_result:
                    fee_amount = self.info_board.calculate_security_trade_fee(
                        product, date, fee_rate_institution, flow['security_code'], flow['trade_amount'],
                        # trade_name=flow['trade_name'],
                    )
                    if flow['trade_direction'] == TRADE_DIRECTION_BUY:
                        flow['cash_move'] = - abs(flow['trade_amount']) - fee_amount
                    elif flow['trade_direction'] == TRADE_DIRECTION_SELL:
                        flow['cash_move'] = abs(flow['trade_amount']) - fee_amount
                    else:
                        raise NotImplementedError(flow)
                    self.log.debug(flow)
                self.margin_flow.extend(List.from_dict_list(EstimatedMarginTradeFlow, loaded_result))

            elif account_type == '期货':
                if file_type == 'csv':
                    loaded_result = loader_cls.load_future_csv(file_path, product, date, institution)
                else:
                    loaded_result = loader_cls.load_future_excel(file_path, product, date, institution)
                fee_rate_institution = '{}期货'.format(institution.replace('期货', ''))
                for flow in loaded_result:
                    flow['trade_amount'] = flow['trade_price'] * flow['trade_volume'] * self.market_board.float_field(
                        'contractmultiplier', flow['security_code'], flow['date'], '',
                    )
                    fee_amount = self.info_board.calculate_security_trade_fee(
                        product, date, fee_rate_institution, flow['security_code'], flow['trade_amount'])
                    flow['trade_fee'] = fee_amount
                    self.log.debug(flow)
                self.future_flow.extend(List.from_dict_list(EstimatedFutureTradeFlow, loaded_result))

            elif account_type in ('美股收益互换', '港股收益互换'):
                if '开曼' in file_name:
                    continue

                loaded_result = ZhongXin.load_swap_excel(file_path, product, date, account_type)
                for flow in loaded_result:
                    fee_amount = 0.0
                    if flow['trade_direction'] == TRADE_DIRECTION_BUY:
                        flow['cash_move'] = - abs(flow['trade_amount']) - fee_amount
                    elif flow['trade_direction'] == TRADE_DIRECTION_SELL:
                        flow['cash_move'] = abs(flow['trade_amount']) - fee_amount
                    else:
                        raise NotImplementedError(flow)
                    self.log.debug(flow)

                self.normal_flow.extend(List.from_dict_list(EstimatedNormalTradeFlow, loaded_result))

            else:
                raise NotImplementedError(file_name)

    def save_to_database(self):
        if len(self.normal_flow) > 0:
            self.clear_duplicated_in_db('当日普通交易流水')
            self.insert_to_db('当日普通交易流水', self.normal_flow)

        if len(self.margin_flow) > 0:
            self.clear_duplicated_in_db('当日两融交易流水')
            self.insert_to_db('当日两融交易流水', self.normal_flow)

        if len(self.future_flow) > 0:
            self.clear_duplicated_in_db('当日期货交易流水')
            self.insert_to_db('当日期货交易流水', self.future_flow)

    def insert_to_db(self, table_name: str, data_list: List):
        if len(data_list) > 0:
            for obj in data_list:
                sql = getattr(obj, 'form_insert_sql').__call__(table_name)
                try:
                    self.db.execute(DataBaseName.management, sql)
                except BaseException as i_e:
                    print(obj)
                    raise i_e
        self.log.info_running('储存当日', table_name)

    def clear_duplicated_in_db(self, table_name: str, ):
        assert isinstance(self.current_date, datetime.date)
        self.db.execute(
            DataBaseName.management,
            "DELETE FROM {} WHERE 日期 = '{}'".format(table_name, self.current_date),
        )

        # trade_flow_list = List()
        # for sheet_name in xls_book.sheet_names():
        #
        #     elif '收益互换' in security_type:
        #         load_rules = {
        #             'security_code': ['标的代码', ], 'security_name': ['标的简称', ],
        #             'trade_class': ['买卖方向', ], 'trade_price': ['成交均价', ], 'trade_volume': ['成交数量', ],
        #             'trade_amount': ['成交金额', ], 'trade_market': ['市场类型', '交易所名称'],
        #             None: [
        #                 '委托数量', '委托金额', '委托次数', '撤单数量', '撤单次数', '操作人',
        #             ],
        #         }
        #         mapper = ExcelMapper(load_rules, input_dict, )
        #         mapper.log.debug('mapping {}'.format(sheet_name))
        #         for d_dict in mapper.map(xls_book.sheet_by_name(sheet_name)):
        #             assert isinstance(d_dict, dict)
        #             obj = TradeFlow(**d_dict).check_loaded()
        #             print(obj)
        #             trade_flow_list.append(obj)
        #
        #     else:
        #         raise NotImplementedError(sheet_name, '{} {} {}'.format(product, security_type, institution))
        #
        # # ---- [计算交易费用] ----
        # for obj in trade_flow_list:
        #     assert isinstance(obj, TradeFlow)
        #     trade_fee = obj.calculate_trade_fee()
        #     cash_move = obj.calculate_cash_move()
        #
        # return trade_flow_list


def __load_one_valuation_statement__(product: str, file_path: str, date: datetime.date):
    hand_dict = {'product': product, 'date': date, }
    map_rules = {
        'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['币种', ],
        'exchange_rate': ['汇率', ], 'hold_volume': ['数量', ], 'average_cost': ['单位成本', ],
        'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价'],
        'total_market_value': ['市值-本币', '市值', '市值本币'],
        'None': [
            '成本占比', '市值占比', '估值增值-本币', '停牌信息', '权益信息', '市值占净值', '成本占净值', '估值增值', '估值增值本币',
        ]
    }
    mapper = ExcelMapper(map_rules, hand_dict, None).set_duplicated_tolerance(True).set_force_vertical(True)
    m_list = List(mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0)))
    if len(m_list) == 0:
        raise RuntimeError('估值表 {} 读取失败！'.format(file_path))
    # 读取净值、份额、净资产、税费
    product_data = dict()
    product_data['file_path'] = file_path
    for m_dict in m_list:
        assert isinstance(m_dict, dict)
        assert 'account_code' in m_dict and 'account_name' in m_dict, str(
            '丢失科目信息：{} {}').format(file_path, m_dict)
        if re.sub(r'\W', '', m_dict['account_code']) in ('单位净值', '基金单位净值', '今日单位净值'):
            product_data['net_value'] = float_check(m_dict['account_name'])
        if re.sub(r'\W', '', m_dict['account_code']) in ('资产净值', '基金资产净值'):
            product_data['net_asset'] = float_check(m_dict['total_market_value'])
        if m_dict['account_code'] == '实收资本':
            product_data['fund_shares'] = float_check(m_dict['total_market_value'])
        if '税' in m_dict['account_name']:
            if len(str_check(m_dict['account_code'])) == 4:
                assert 'tax_payable' not in product_data, str('重复读取应交税费 {} {} {}'.format(
                    file_path, m_dict, m_list))
                product_data['tax_payable'] = float_check(m_dict['total_market_value'])
            elif len(str_check(m_dict['account_code'])) > 4:
                pass
            else:
                raise NotImplementedError('{} {}'.format(file_path, m_dict))
    assert 'net_value' in product_data, str('读取单位净值失败 {}\n{}'.format(file_path, m_list))
    assert 'net_asset' in product_data, str('读取净资产失败 {}\n{}'.format(file_path, m_list))
    assert 'fund_shares' in product_data, str('读取基金份额失败 {}\n{}'.format(file_path, m_list))
    return product_data


def load_valuation_statements(folder_path: str, date: datetime.date):
    from modules.Modules import Modules
    result_dict = dict()

    env_inst = Modules.get_instance()
    product_name_range = env_inst.info_board.product_info_list.collect_attr_map('full_name', 'name')
    product_name_range.update(env_inst.info_board.product_info_list.collect_attr_map('name', 'name'))

    while not os.path.exists(os.path.join(folder_path, date.strftime('%Y%m%d'))):
        date = date - datetime.timedelta(days=1)
    result_dict['operation_date'] = date

    search_date, end_date = date - datetime.timedelta(days=1), date + datetime.timedelta(days=20)
    while search_date <= end_date:
        # 搜索文件夹是否存在
        sub_folder = os.path.join(folder_path, search_date.strftime('%Y%m%d'))
        # print(sub_folder)
        if not os.path.exists(sub_folder):
            search_date += datetime.timedelta(days=1)
            continue
        for file_name in os.listdir(sub_folder):
            # print(os.path.join(sub_folder, file_name))
            if file_name.startswith('.'):
                continue
            if date.strftime('%Y%m%d') not in file_name and date.strftime('%Y-%m-%d') not in file_name:
                continue

            product = None
            for name in product_name_range:
                if product is not None:
                    continue
                if name in file_name:
                    product = product_name_range[name]
            if product is None:
                raise RuntimeError('未能识别产品名称：{}'.format(file_name))
            assert product not in result_dict, '重复估值表 {} {}'.format(
                product, os.path.join(sub_folder, file_name), result_dict[product]['file_path'])
            result_dict[product] = __load_one_valuation_statement__(product, os.path.join(sub_folder, file_name), date)
        search_date += datetime.timedelta(days=1)
    return result_dict


def load_valuation_statements_folder(folder_path: str, date: datetime.date):
    """
    读取托管估值表 -- 净值、份额、净资产、税费
    :return: {
        product: {
            net_value: 单位净值,
            net_asset: 净资产,
            fund_shares: 基金份额,
            tax_payable: 应交税费,
        }
    }
    """
    from jetend.structures import ExcelMapper
    from modules.Modules import Modules
    assert date.strftime('%Y%m%d') in folder_path, str(folder_path)

    result_dict = dict()
    if not os.path.exists(folder_path):
        return result_dict

    env_inst = Modules.get_instance()
    product_name_range = env_inst.info_board.product_info_list.collect_attr_map('full_name', 'name')
    product_name_range.update(env_inst.info_board.product_info_list.collect_attr_map('name', 'name'))

    for file_name in os.listdir(folder_path):
        if file_name.startswith('.'):
            continue
        # 从文件名当中获取产品名字
        product = None
        for name in product_name_range:
            if product is not None:
                continue
            if name in file_name:

                product = product_name_range[name]
        if product is None:
            raise RuntimeError('未能识别产品名称：{}'.format(file_name))
        assert product not in result_dict, '重复估值表 {} {}'.format(product, file_name)
        print(product, file_name)
        # if product in result_dict:
        #     raise RuntimeError('读取重复估值表：{} {}'.format(product, file_name))
        hand_dict = {'product': product, 'date': date, }
        map_rules = {
            'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['币种', ],
            'exchange_rate': ['汇率', ], 'hold_volume': ['数量', ], 'average_cost': ['单位成本', ],
            'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价'],
            'total_market_value': ['市值-本币', '市值', '市值本币'],
            'None': [
                '成本占比', '市值占比', '估值增值-本币', '停牌信息', '权益信息', '市值占净值', '成本占净值', '估值增值', '估值增值本币',
            ]
        }
        mapper = ExcelMapper(map_rules, hand_dict, None).set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = List(mapper.map(xlrd.open_workbook(os.path.join(folder_path, file_name)).sheet_by_index(0)))
        if len(m_list) == 0:
            raise RuntimeError('估值表 {} 读取失败！'.format(file_name))
        # 读取净值、份额、净资产、税费
        product_data = dict()
        for m_dict in m_list:
            assert isinstance(m_dict, dict)
            assert 'account_code' in m_dict and 'account_name' in m_dict, str(
                '丢失科目信息：{} {}').format(file_name, m_dict)
            if re.sub(r'\W', '', m_dict['account_code']) in ('单位净值', '基金单位净值', '今日单位净值'):
                product_data['net_value'] = float_check(m_dict['account_name'])
            if re.sub(r'\W', '', m_dict['account_code']) in ('资产净值', '基金资产净值'):
                product_data['net_asset'] = float_check(m_dict['total_market_value'])
            if m_dict['account_code'] == '实收资本':
                product_data['fund_shares'] = float_check(m_dict['total_market_value'])
            if '应交税费' in m_dict['account_name']:
                if len(str_check(m_dict['account_code'])) == 4:
                    assert 'tax_payable' not in product_data, str('重复读取应交税费 {} {} {}'.format(
                        file_name, m_dict, m_list))
                    product_data['tax_payable'] = float_check(m_dict['total_market_value'])
                elif len(str_check(m_dict['account_code'])) > 4:
                    pass
                else:
                    raise NotImplementedError('{} {}'.format(file_name, m_dict))
        assert 'net_value' in product_data, str('读取单位净值失败 {}\n{}'.format(file_name, m_list))
        assert 'net_asset' in product_data, str('读取净资产失败 {}\n{}'.format(file_name, m_list))
        assert 'fund_shares' in product_data, str('读取基金份额失败 {}\n{}'.format(file_name, m_list))
        # assert 'net_value' in product_data, str('读取单位净值失败 {}'.format(file_name))
        print(product, product_data)
        result_dict[product] = product_data
    return result_dict


if __name__ == '__main__':
    from jetend.structures import MySQL
    from modules.Modules import Modules

    loader = TradeFlowLoader(
        MySQL('lr01', '123', '192.168.1.172', 3306),
        r'Z:\NutStore\久铭产品交割单\当日交易流水'
    )
    loader.load_simple_output_flow(datetime.date(2019, 9, 2))
    loader.save_to_database()
