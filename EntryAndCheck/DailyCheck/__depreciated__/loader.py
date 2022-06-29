# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import os
import re
import xlrd
import datetime

from xlrd.biffh import XLRDError

from jetend.structures import ExcelMapper, List, MySQL
from jetend.DataCheck import *

from modules.TradeFlow import TradeFlow


class TradeFlowLoader(object):

    def __init__(self, db: MySQL):
        self.db = db

    def load_simple_output_flow(self, file_path: str, date: datetime.date):
        """载入陈田田的交易流水 -> List(TradeFlow, )"""
        assert date.strftime('%Y%m%d') in file_path

        # ---- [读取流水] ----
        trade_flow_list = List()
        for sheet_name in xls_book.sheet_names():
            product, security_type, institution = re.search(
                r'(\D+\d+[号指数]+)([股票两融期货美港收益互换]+)(\w+)', sheet_name, flags=re.I,
            ).groups()
            input_dict = {'product': product, 'date': date, 'institution': institution, }

            # 读取股票类流水
            if security_type == '股票':
                load_rules = {
                    'date': ['成交日期', ],
                    'time': ['成交时间', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
                    'trade_class': ['买卖标志', ], 'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ],
                    'trade_amount': ['成交金额', ], 'trade_market': ['市场', '交易所名称'],
                    'hashable_key': ['成交编号', ],
                    None: [
                        '委托编号', '委托时间', '委托类型', '股东代码', '资金账号', '资金帐号', '客户代码', '股东姓名',
                        '委托价格', '委托数量', '状态说明', '备注',
                    ],
                }
                mapper = ExcelMapper(load_rules, input_dict, )
                mapper.log.debug('mapping {}'.format(sheet_name))
                for d_dict in mapper.map(xls_book.sheet_by_name(sheet_name)):
                    assert isinstance(d_dict, dict)
                    obj = TradeFlow(**d_dict).check_loaded()
                    print(obj)
                    trade_flow_list.append(obj)

            elif '收益互换' in security_type:
                load_rules = {
                    'security_code': ['标的代码', ], 'security_name': ['标的简称', ],
                    'trade_class': ['买卖方向', ], 'trade_price': ['成交均价', ], 'trade_volume': ['成交数量', ],
                    'trade_amount': ['成交金额', ], 'trade_market': ['市场类型', '交易所名称'],
                    None: [
                        '委托数量', '委托金额', '委托次数', '撤单数量', '撤单次数', '操作人',
                    ],
                }
                mapper = ExcelMapper(load_rules, input_dict, )
                mapper.log.debug('mapping {}'.format(sheet_name))
                for d_dict in mapper.map(xls_book.sheet_by_name(sheet_name)):
                    assert isinstance(d_dict, dict)
                    obj = TradeFlow(**d_dict).check_loaded()
                    print(obj)
                    trade_flow_list.append(obj)

            else:
                raise NotImplementedError(sheet_name, '{} {} {}'.format(product, security_type, institution))

        # ---- [计算交易费用] ----
        for obj in trade_flow_list:
            assert isinstance(obj, TradeFlow)
            trade_fee = obj.calculate_trade_fee()
            cash_move = obj.calculate_cash_move()

        return trade_flow_list


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
            if '静康' in file_name:
                continue
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


hk_swap_product_id_map = {
    '101050': '稳健22号', '101767': '稳健23号', '103089': '久铭1号', '103192': '久铭2号',
    '103423': '稳健6号', '103424': '稳健7号', '103448': '全球1号',
}
underlying_map_rules = {
    'customer_id': ['客户号', ], 'trade_currency': ['交易货币', ],
    'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
    'offset': ['持仓类型多空', '标的方向多空', ], 'hold_volume': ['标的数量', '标的名义数量加总', ],
    'contract_multiplier': ['标的乘数', ], 'average_cost_origin': ['平均单位持仓成本交易货币', ],
    'close_price_origin': ['当前价格交易货币', '收盘价格交易货币', ],
    'total_cost_origin': ['该标的持仓成本加总的近似值交易货币', ],
    'accumulated_realized_profit': ['组合累计实现收益加总近似值交易货币', ],
    'accumulated_unrealized_profit': ['组合待实现收益加总近似值交易货币', ],
    'market_value_origin': ['标的市值交易货币', ],
    None: ['计算日期',  '涨跌幅', '持仓比例']
}
calculation_map_rules = {
    'customer_id': ['客户号', ], 'trade_currency': ['交易货币', ], 'settle_currency': ['结算货币', ],
    'notional_principle_origin': ['组合名义本金额加总的近似值交易货币', ],
    'prepaid_balance_origin': ['预付金余额加总近似值交易货币', ],
    'capital_sum_origin': ['盯市金额加总的近似值交易货币', ], 'capital_sum': ['盯市金额加总的近似值结算货币', ],
    'exchange_rate': ['汇率交易货币结算货币', ],
    'initial_margin_origin': ['初始保障金额加总的近似值交易货币', ],
    'maintenance_margin_origin': ['维持保障金额加总的近似值交易货币', ],
    'accumulated_interest_accrued': ['累计利率收益金额和预付金返息金额的加总近似值交易货币', ],
    'accumulated_interest_payed': ['应付已付利率收益金额和预付金返息金额加总的近似值交易货币', ],
    None: ['计算日期', ],
}
balance_map_rules = {
    'customer_id': ['客户号', ], 'trade_currency': ['交易货币', ], 'settle_currency': ['结算货币', ],
    'accumulated_withdrawal': ['累计支取预付金净额结算货币', ],
    'carryover_balance_origin': ['结转预付金余额交易货币', ],
    'exchange_rate': ['汇率交易货币结算货币', ],
    'total_balance': ['预付金余额加总近似值交易货币', ],
    'available_balance': ['可用保障金额加总近似值交易货币', ],
    None: ['计算日期', '备注', ],
}


# def __get_super_folder__(path: str):
#     """获取当前路径所在的文件夹"""
#     super_folder_path = path.split(os.path.sep)
#     super_folder_path.pop()
#     super_folder_path = os.path.sep.join(super_folder_path)
#     return super_folder_path


def load_swap(folder_path: str, date: datetime.date):
    """
    读取收益互换
    返回 {
        product: [balance_dict, underlying_list, calculation_dict],
        exchange_rate: float,
    }
    """
    from jetend.structures import ExcelMapper
    # assert date.strftime('%Y%m%d') in folder_path, '收益互换读取日期 {} 与文件夹 {} 不匹配'.format(date, folder_path)

    result_dict = dict()

    super_folder_path = folder_path.split(os.path.sep)
    super_folder_path.pop()
    super_folder_path = os.path.sep.join(super_folder_path)

    if not os.path.exists(super_folder_path):
        return FileNotFoundError('文件夹不存在')

    result_dict['loaded_date'] = date

    for file_name in os.listdir(folder_path):
        # 忽略系统文件
        if file_name.startswith('.'):
            continue

        if not file_name.endswith('xlsx'):
            continue

        # 读取 excel 对账单
        # 获取产品名称
        try:
            if date >= datetime.date(2019, 3, 1):
                product_id, date_str = re.match(r'Statement_(\d+)-.*_(\d+)', file_name).groups()
            else:
                raise NotImplementedError(date)
        except AttributeError:
            raise RuntimeError('文件名匹配失败 {} - {}'.format(file_name, folder_path))
        assert date.strftime('%Y%m%d') == date_str, '{} {}'.format(date, date_str)
        product = hk_swap_product_id_map[product_id]

        xls_file = xlrd.open_workbook(os.path.join(folder_path, file_name))
        hand_dict = {'product': product, 'date': date, }

        mapper = ExcelMapper(underlying_map_rules, hand_dict, None)
        mapper.ignore_line.update(['合计', ])
        underlying_list = mapper.map(xls_file.sheet_by_name('Underlying'))

        mapper = ExcelMapper(calculation_map_rules, hand_dict, None)
        calculation = mapper.map(xls_file.sheet_by_name('Calculation'))[0]

        mapper = ExcelMapper(balance_map_rules, hand_dict, None)
        balance = mapper.map(xls_file.sheet_by_name('Balance'))[0]

        # 汇率检查
        assert balance['exchange_rate'] == calculation['exchange_rate'], '汇率错误：收益互换同一文件 {} 汇率不同 {} {}'.format(
            file_name, balance['exchange_rate'], calculation['exchange_rate'], )
        if 'exchange_rate' in result_dict:
            exchange_rate = result_dict['exchange_rate']
            assert balance['exchange_rate'] == exchange_rate, '汇率错误：当日收益互换汇率错误 {} {}'.format(
                exchange_rate, balance['exchange_rate'])
        else:
            result_dict['exchange_rate'] = balance['exchange_rate']

        # 读取 pdf 流水 （难度比较高，暂时不实现）

        result_dict[product] = [balance, underlying_list, calculation]

    return result_dict


if __name__ == '__main__':
    pass
# if __name__ == '__main__':
#     import datetime
#     from loader.TradeLoader import TradeFlowLoader
#
#     from jetend.structures import MySQL
#
#     loader = TradeFlowLoader(
#         MySQL('lr01', '123', '192.168.1.172', 3306),
#         r'Z:\当日交易流水'
#     )
#     loader.load_simple_output_flow(datetime.date(2019, 9, 20))
#     loader.save_to_database()
