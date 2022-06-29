# -*- encoding: UTF-8 -*-
import xlrd
import datetime
import os
import re
import shutil

from Abstracts import AbstractInstitution
from Checker import *

from JournalLoader.Move import Move


class ZhongXin(AbstractInstitution):
    """中信"""
    folder_institution_map = {
        '中信普通账户': '中信', '中信两融账户': '中信两融',
        '中信美股': '中信美股', '中信港股': '中信港股',
        '中信期权账户': '中信期权',
        '中信期货账户': '中信期货',
    }

    normal_pos = {
        'shareholder_code': ['股东帐号', '股东账号'], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'hold_volume': ['股份余额', ], 'weight_average_cost': ['参考成本价'], 'total_cost': ['参考成本', ],
        'close_price': ['参考市价', ], 'market_value': ['参考市值', ],
        'None': ['股份可用', '交易冻结', '参考盈亏'],
    }
    normal_flow = {
        'trade_class': ['摘要', ], 'shareholder_code': ['股东帐号', '股东账号'], 'security_code': ['证券代码', ],
        'security_name': ['证券名称', ], 'trade_volume': ['成交股数', ], 'trade_price': ['成交价格', ],
        'cash_move': ['发生金额', ],
        'None': ['发生日期', '股份余额', '手续费', '印花税', '过户费', '委托费', '其他费', '资金余额']
    }
    normal_acc = {
        'capital_account': ['资产账户', ], 'customer_id': ['客户代码', ],
        'capital_sum': ['总资产', ], 'cash_amount': ['资金余额', ], 'market_sum': ['资产市值', ],
        'None': ['可用余额', ],
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        if '两融' in folder_name:
            print("========")
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            ZhongXin.log.debug(file_name)

            if file_name.startswith('.') or file_name.startswith('~'):  # 忽略隐藏文件和临时文件
                continue
            if '副本' in file_name:
                continue
            elif file_name.lower().endswith('xlsx') or file_name.lower().endswith('xls'):
                if '合并交割单' in file_name or '资金合并对账单' in file_name or '600565369' in file_name:
                    os.remove(os.path.join(folder_path, file_name))
                    continue
                if '个股期权对账单' in file_name:
                    target_path = folder_path.replace('中信普通账户', '中信期权账户')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                try:
                    product_name, some_id, date_str = re.match(
                        r"([^\d]+\d*[号指数]*)[^\d]+(\d+)_[^\d]+(\d+)", file_name).groups()
                except AttributeError as a_error:
                    if '久铭9号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '久铭9号', date.strftime('%Y%m%d')
                    elif '久铭信利' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '久铭信利', date.strftime('%Y%m%d')
                    elif '久铭收益2号' in file_name:
                        if '30200142027' in file_name:
                            assert date.strftime('%Y%m%d') in file_name, file_name
                            product_name, date_str = '收益2号', date.strftime('%Y%m%d')
                        else:
                            product_name = '收益2号'
                            continue
                    elif '久铭1号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '久铭1号', date.strftime('%Y%m%d')
                    elif '久铭专享7号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '专享7号', date.strftime('%Y%m%d')
                    elif '久铭专享8号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '专享8号', date.strftime('%Y%m%d')
                    elif '久铭专享9号' in file_name:  # @waves
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '专享9号', date.strftime('%Y%m%d')
                    elif '久铭6号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '久铭6号', date.strftime('%Y%m%d')
                    elif '久铭专享6号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '专享6号', date.strftime('%Y%m%d')
                    elif '久铭专享2号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '专享2号', date.strftime('%Y%m%d')
                    elif '久铭专享15号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '专享15号', date.strftime('%Y%m%d')
                    elif '久铭专享16号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name  # @ wave
                        product_name, date_str = '专享16号', date.strftime('%Y%m%d')
                    elif '久铭专享17号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '专享17号', date.strftime('%Y%m%d')
                    elif '久铭全球丰收1号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '全球丰收1号', date.strftime('%Y%m%d')
                    elif '久铭创新稳禄2号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '创新稳禄2号', date.strftime('%Y%m%d')
                    elif '久铭创新稳禄3号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '创新稳禄3号', date.strftime('%Y%m%d')
                    elif '久铭创新稳禄14号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '创新稳禄14号', date.strftime('%Y%m%d')
                    elif '静康创新稳健1号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '静康创新稳健1号', date.strftime('%Y%m%d')
                    elif '创新稳禄12号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '创新稳禄12号', date.strftime('%Y%m%d')
                    elif '稳健1号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '稳健1号', date.strftime('%Y%m%d')
                    elif '久铭专享25号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '专享25号', date.strftime('%Y%m%d')
                    elif '久铭专享26号' in file_name:
                        assert date.strftime('%Y%m%d') in file_name, file_name
                        product_name, date_str = '专享26号', date.strftime('%Y%m%d')
                    else:
                        raise a_error
                if re.match(r'久铭[稳健全球]+\d+号', product_name):
                    assert isinstance(product_name, str)
                    product_name = product_name.replace('久铭', '')
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': ZhongXin.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                    'offset': OFFSET_OPEN,
                }
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ZhongXin.normal_pos, identified_dict, )
                matcher.ignore_line.update(['合计'])
                matcher.set_start_line('当日持仓清单').set_end_line('新股配号')
                pos_list = matcher.map(content.sheet_by_index(0))
                # print(pos_list)
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongXin.normal_flow, identified_dict, )
                matcher.ignore_line.update(['合计', '期初余额'])
                matcher.ignore_above_line.update(['资产市值', ])
                try:
                    matcher.set_start_line('对账单').set_end_line('当日持仓清单')
                    flow_list = matcher.map(content.sheet_by_index(0))
                except AttributeError:
                    matcher.set_start_line('对帐单').set_end_line('当日持仓清单')
                    flow_list = matcher.map(content.sheet_by_index(0))
                # print(flow_list)
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhongXin.normal_acc, identified_dict)
                matcher.set_start_line('资金情况').set_end_line('对帐单')
                acc_obj = matcher.map(content.sheet_by_index(0))[0]
                # print(acc_obj)
                result_dict[product_name]['account'] = acc_obj

                confirm_normal_account(acc_obj)
                # match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('rar'):
                os.remove(os.path.join(folder_path, file_name))
                continue

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    swap_product_id_map = {
        '101050': '稳健22号', '101767': '稳健23号', '103089': '久铭1号', '103192': '久铭2号',
        '103423': '稳健6号', '103424': '稳健7号', '103448': '全球1号', '106672': '专享7号', '106560': '久铭信利',
        '106725': '久盈2号',
    }
    swap_underlying = {
        'customer_id': ['客户号', ], 'trade_currency': ['交易货币', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'offset': ['持仓类型多空', '标的方向多空', ], 'hold_volume': ['标的数量', '标的名义数量加总', ],
        'contract_multiplier': ['标的乘数', ], 'average_cost_origin': ['平均单位持仓成本交易货币', ],
        'close_price_origin': ['当前价格交易货币', '收盘价格交易货币', ],
        'total_cost_origin': ['该标的持仓成本加总的近似值交易货币', ],
        'accumulated_realized_profit': ['组合累计实现收益加总近似值交易货币', ],
        'accumulated_unrealized_profit': ['组合待实现收益加总近似值交易货币', ],
        'market_value_origin': ['标的市值交易货币', ],
        None: ['计算日期', '涨跌幅', '持仓比例', '当日未到账股息', '当日到账股息', '合并类型',
               '交易所', '初始保证金', '维持保证金', '基本费用', '融资费用', '融券费用', '空头返息'],
    }
    swap_calculation = {
        'customer_id': ['客户号', ], 'trade_currency': ['交易货币', ], 'settle_currency': ['结算货币', ],
        'notional_principle_origin': ['组合名义本金额加总的近似值交易货币', ],
        'prepaid_balance_origin': ['预付金余额加总近似值交易货币', ],
        'capital_sum_origin': ['盯市金额加总的近似值交易货币', ], 'capital_sum': ['盯市金额加总的近似值结算货币', ],
        'exchange_rate': ['汇率交易货币结算货币', ],
        'initial_margin_origin': ['初始保障金额加总的近似值交易货币', ],
        'maintenance_margin_origin': ['维持保障金额加总的近似值交易货币', ],
        'accumulated_interest_accrued': ['累计利率收益金额和预付金返息金额的加总近似值交易货币', ],
        'accumulated_interest_payed': ['应付已付利率收益金额和预付金返息金额加总的近似值交易货币', ],
        None: ['计算日期', '合并类型', '合约价值', '返息基数交易货币', '现金返息基数结算货币'],
    }
    swap_balance = {
        'customer_id': ['客户号', ], 'trade_currency': ['交易货币', ], 'settle_currency': ['结算货币', ],
        'accumulated_withdrawal': ['累计支取预付金净额结算货币', ],
        'carryover_balance_origin': ['结转预付金余额交易货币', ],
        'exchange_rate': ['汇率交易货币结算货币', ],
        'total_balance': ['预付金余额加总近似值交易货币', ],
        'available_balance': ['可用保障金额加总近似值交易货币', ],
        None: ['计算日期', '备注', '合并类型', '可提取金额结算货币', '是否追保', '追保金额结算货币'],
    }

    @staticmethod
    def load_swap(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper

        result_dict, product_file_map = dict(), dict()

        super_folder_path = folder_path.split(os.path.sep)
        super_folder_path.pop()
        super_folder_path = os.path.sep.join(super_folder_path)
        folder_name = folder_path.split(os.path.sep)[-1]

        if not os.path.exists(super_folder_path):
            return FileNotFoundError('文件夹不存在')

        result_dict['loaded_date'] = date

        for file_name in os.listdir(folder_path):
            ZhongXin.log.debug_running(file_name)
            # 忽略系统文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xlsx'):

                # 读取 excel 对账单
                # 获取产品名称
                product_id, date_str = re.match(r'Statement_(\d+)-.*_(\d+)', file_name).groups()

                assert date.strftime('%Y%m%d') == date_str, '{} {}'.format(date, date_str)
                product = ZhongXin.swap_product_id_map[product_id]

                if product not in result_dict:
                    result_dict[product] = dict()
                product_file_map[product] = file_name

                xls_file = xlrd.open_workbook(os.path.join(folder_path, file_name))
                hand_dict = {
                    'product': product, 'date': date, 'institution': ZhongXin.folder_institution_map[folder_name],
                    'account_type': folder_name, 'customer_id': product_id,
                }
                assert product in PRODUCT_NAME_RANGE, product

                mapper = ExcelMapper(ZhongXin.swap_underlying, hand_dict, None)
                mapper.ignore_line.update(['合计', ])
                underlying_list = list()
                for underlying in mapper.map(xls_file.sheet_by_name('Underlying')):
                    if len(underlying.get('offset', '')) == 0:
                        if float_check(underlying.get('hold_volume', 0.0)) < 0.01:
                            underlying['offset'] = OFFSET_OPEN
                        else:
                            raise NotImplementedError(underlying)
                    if abs(float_check(underlying['hold_volume'])) < 0.02:
                        pass
                    else:
                        underlying_list.append(underlying)

                mapper = ExcelMapper(ZhongXin.swap_calculation, hand_dict, None)
                calculation = mapper.map(xls_file.sheet_by_name('Calculation'))[0]

                mapper = ExcelMapper(ZhongXin.swap_balance, hand_dict, None)
                balance = mapper.map(xls_file.sheet_by_name('Balance'))[0]

                # 汇率检查
                assert balance['exchange_rate'] == calculation['exchange_rate'], '汇率错误：{} 汇率不同 {} {}'.format(
                    file_name, balance['exchange_rate'], calculation['exchange_rate'], )

                if 'exchange_rate' in result_dict:
                    exchange_rate = result_dict['exchange_rate']
                    assert balance['exchange_rate'] == exchange_rate, '汇率错误：当日收益互换汇率错误 {} {}'.format(
                        exchange_rate, balance['exchange_rate'])
                else:
                    result_dict['exchange_rate'] = balance['exchange_rate']

                match_swap_citic(balance, calculation, underlying_list)

                result_dict[product] = {
                    'balance_dict': balance,
                    'calculation_dict': calculation,
                    'underlying_list': underlying_list,
                }
            elif file_name.lower().endswith('pdf'):
                pro_id, product = None, None
                for tag in ZhongXin.swap_product_id_map.keys():
                    if tag in file_name:
                        pro_id = tag
                        product = ZhongXin.swap_product_id_map[pro_id]
                        break
                assert pro_id is not None, file_name
                if len(result_dict) > 1:
                    pass
                else:
                    product_file_map[product] = file_name
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    # hongkong_stock_pos = {
    #     'customer_id': ['客户号', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
    #     'offset': ['持仓类型多空', '标的方向多空', ], 'hold_volume': ['标的数量', '标的名义数量加总', ], 'currency': ['交易货币', ],
    #     'close_price': ['当前价格交易货币', '收盘价格交易货币', ], 'total_cost': ['该标的总成本交易货币',
    #                                                               '该标的持仓成本加总的近似值交易货币', ],
    #     'market_value': ['市值交易货币', '标的市值交易货币', ],
    #     'None': ['清单编号', '估值日期', '期初价格交易货币', '涨跌幅', '累计实现收益交易货币', '总浮动盈亏交易货币', '持仓比例',
    #              '计算日期', '平均单位持仓成本交易货币', '组合累计实现收益加总近似值交易货币', '组合待实现收益加总近似值交易货币',
    #              '标的乘数'
    #              ],
    # }
    # # hongkong_stock_acc = {
    # #     'customer_id': ['客户号', ], 'capital_sum': ['盯市金额HKD', '盯市金额加总的近似值交易货币','盯市金额交易货币',],
    # #     'None': ['交易货币', '支付货币', '计算日期', '清单编号', '估值日期', '组合名义本金额HKD', '预付金余额HKD', 'SWAP合约价值HKD',
    # #              '汇率', '盯市金额CNY', '组合名义本金额加总的近似值交易货币', '预付金余额加总近似值交易货币', '汇率交易货币支付货币',
    # #              '盯市金额加总的近似值支付货币', '初始保障金额加总的近似值交易货币', '维持保障金额加总的近似值交易货币',
    # #              '累计利率收益金额和预付金返息金额的加总近似值交易货币', '应付已付利率收益金额加总的近似值交易货币','组合名义本金额交易货币',
    # #              '盯市比率', '初始保障金额HKD', '维持保障金额HKD', '累计利息HKD', '净值', '应付已付利息HKD',
    # #              '预付金余额交易货币', 'SWAP合约价值交易货币', '盯市金额交易货币', '初始保障金额交易货币', '维持保障金额交易货币',
    # #              '累计利息交易货币', '应付已付利息交易货币','盯市金额支付货币', '结算货币', '汇率交易货币结算货币',
    # #              '盯市金额加总的近似值结算货币', '应付已付利率收益金额和预付金返息金额加总的近似值交易货币'
    # #              ],
    # # }
    # hongkong_stock_acc = {
    #     'customer_id': ['客户号', ], 'capital_sum': ['盯市金额HKD', '盯市金额加总的近似值交易货币', '盯市金额交易货币', ],
    #     'notional_principle': ['组合名义本金额HKD', '组合名义本金额加总的近似值交易货币', '组合名义本金额交易货币'],
    #     'prepaid_balance': ['预付金余额', '预付金余额HKD', '预付金余额加总近似值交易货币'], 'SWAP_value': ['合约价值', ],
    #     'cumulative_withdrawal': ['累计支取预付金净额CNY', '累计支取预付金净额结算货币'],
    #     'exchange_rate': ['汇率', '汇率交易货币结算货币'], 'initial_margin': ['初始保障金', '初始保障金额加总的近似值交易货币'],
    #     'maintenance_margin': ['维持保障金', '维持保障金HKD', '维持保障金额加总的近似值交易货币'],
    #     'net_value': ['净值', ], 'accumulated_interest': ['累计利息', '累计利息HKD'], 'interest_paid': ['应付已付利息', ],
    #     'carryover_prepaid_balance': ['结转预付金余额HKD', '结转预付金余额交易货币'], 'available_margin_balance': ['可用保障金额加总近似值交易货币'],
    #     'None': ['交易货币', '结算货币', '计算日期', '盯市金额加总的近似值结算货币', '累计利率收益金额和预付金返息金额的加总近似值交易货币',
    #              '应付已付利率收益金额和预付金返息金额加总的近似值交易货币', '预付金可用余额HKD', '备注', ]
    # }
    # # hongkong_stock_acc = {
    # #     'customer_id': ['客户号', ], 'capital_sum': ['盯市金额HKD', '盯市金额加总的近似值交易货币', '盯市金额交易货币', ],
    # #     'notional_principle': ['组合名义本金额HKD', '组合名义本金额加总的近似值交易货币', '组合名义本金额交易货币'],
    # #     'prepaid_balance': ['预付金余额', '预付金余额HKD', '预付金余额加总近似值交易货币'], 'SWAP_value': ['合约价值', ],
    # #     'exchange_rate': ['汇率', '汇率交易货币结算货币'], 'initial_margin': ['初始保障金', '初始保障金额加总的近似值交易货币'],
    # #     'maintenance_margin': ['维持保障金', '维持保障金HKD', '维持保障金额加总的近似值交易货币'],
    # #     'net_value': ['净值', ], 'accumulated_interest': ['累计利息', '累计利息HKD'], 'interest_paid': ['已付利息', ],
    # #     'None': ['交易货币', '结算货币', '计算日期', '盯市金额加总的近似值结算货币', '累计利率收益金额和预付金返息金额的加总近似值交易货币',
    # #              '应付已付利率收益金额和预付金返息金额加总的近似值交易货币', '预付金可用余额HKD', '备注', '可用保障金额加总近似值交易货币']
    # # }
    #
    # hongkong_stock_flow = {
    #     'security_code': ['标的代码'], 'security_name': ['证券简称', '标的简称'], 'trade_class': ['交易方向'],
    #     'trade_volume': ['交易数量股'],
    #     'trade_price': ['交易均价交易货币'], 'trade_amount': ['成交金额交易货币'], 'currency': ['交易货币', ],
    #     'None': ['交易确认书', '日期'],
    # }
    # @staticmethod
    # def load_hk_stock(folder_path: str, date: datetime.date):
    #     from jetend.structures import ExcelMapper
    #     folder_name = folder_path.split(os.path.sep)[-1]
    #     result_dict = dict()
    #
    #     id_product_map = {
    #         '1050': '稳健22号', '1767': '稳健23号', '3089': '久铭1号', '3192': '久铭2号',
    #         '3423': '稳健6号', '3424': '稳健7号', '3448': '全球1号',
    #     }
    #
    #     pdf_list = list()
    #
    #     for file_name in os.listdir(folder_path):
    #         if file_name.startswith('.'):
    #             continue
    #         elif file_name.endswith('pdf'):
    #             try:
    #                 pdf_list.append(re.search(r"[^证券市场金融衍生品交易补充确认书]SACTC(\d*)H", file_name).group(1))
    #             except AttributeError:
    #                 continue
    #         elif file_name.endswith('xlsx'):
    #             #for xls_file in loader.list_dir(loader.__sub_folder__(folder), 'xlsx'):
    #             #loader.log.info_running(folder, xls_file)
    #             if date > datetime.date(2018, 9, 17):
    #                 pro_id, date_str = re.match(r'Statement_10(\d+)-.*_(\d+)', file_name).groups()
    #                 assert date_str == date.strftime('%Y%m%d')
    #             elif date <= datetime.date(2018, 9, 17):
    #                 pro_id, some_date, date_str = re.match(
    #                     r"[\w\W]*SACTC(\d+)[^\d]+(\d+)[^(]*\((\d+)\)", file_name
    #                 ).groups()
    #                 assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
    #             else:
    #                 raise NotImplementedError
    #             product_name = id_product_map[pro_id]
    #             identified_dict = {
    #                 'product':product_name , 'date': date,
    #                 'institution': folder_institution_map[folder_name],
    #                 'account_type': folder_path, 'currency': 'HKD',
    #             }
    #             content = xlrd.open_workbook(os.path.join(folder_path, file_name))
    #
    #             if product_name not in result_dict:
    #                 result_dict[product_name] = dict()
    #
    #             matcher = ExcelMapper( ZhongXin.hongkong_stock_pos, identified_dict, )
    #             matcher.ignore_line.update(['合计', '汇总'])
    #
    #             try:
    #                 pos_list = matcher.map(content.sheet_by_name('Position'))
    #             except xlrd.biffh.XLRDError:
    #                 pos_list = matcher.map(content.sheet_by_name('Underlying'))
    #
    #             matcher = ExcelMapper(Valuation, ZhongXin.usa_stock_acc, identified_dict, )
    #             try:
    #                 value_acc_obj = matcher.map(content.sheet_by_name('Valuation'))[0]
    #             except xlrd.biffh.XLRDError:
    #                 value_acc_obj = matcher.map(content.sheet_by_name('Calculation'))[0]
    #
    #             matcher = ExcelMapper(Balance, ZhongXin.usa_stock_acc, identified_dict, )
    #             balance_acc_obj = matcher.map(content.sheet_by_name('Balance'))[0]
    #
    #             acc_obj = RawStockAccount.init_from(balance_acc_obj, value_acc_obj)
    #
    #
    #             if pro_id in pdf_list:
    #                 matcher = ExcelMapper(RawNormalFlow, ZhongXin.hongkong_stock_flow, identified_dict, )
    #                 try:
    #                     flow_list = matcher.map(content.sheet_by_name('Flow'))
    #                     for flow_obj in flow_list:
    #                         if flow_obj.trade_class == '买入':
    #                             flow_obj.cash_move = 1.002 * flow_obj.trade_amount
    #                         elif flow_obj.trade_class == '卖出':
    #                             flow_obj.cash_move = 0.998 * flow_obj.trade_amount
    #                         else:
    #                             continue
    #                     loader.normal_flow.extend(flow_list)
    #                 except xlrd.biffh.XLRDError:
    #                     raise NotImplementedError
    #
    #
    #         product_name = id_product_map[pro_id]
    #         # 检查数据匹配
    #
    # usa_stock_pos = {
    #     'customer_id': ['客户号', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
    #     'offset': ['持仓类型多空', '标的方向多空'], 'hold_volume': ['标的数量', '标的名义数量加总', ], 'currency': ['交易货币', ],
    #     'close_price': ['当前价格交易货币', '收盘价格交易货币', ], 'total_cost': ['该标的总成本交易货币',
    #                                                               '该标的持仓成本加总的近似值交易货币', ],
    #     'market_value': ['市值交易货币', '标的市值交易货币', ],
    #     'None': ['清单编号', '估值日期', '期初价格交易货币', '涨跌幅', '累计实现收益交易货币', '总浮动盈亏交易货币', '持仓比例',
    #              '计算日期', '平均单位持仓成本交易货币', '组合累计实现收益加总近似值交易货币', '组合待实现收益加总近似值交易货币',
    #              '标的乘数'],
    # }
    # # usa_stock_acc = {
    # #     'customer_id': ['客户号', ], 'capital_sum': ['盯市金额USD', '盯市金额加总的近似值交易货币','盯市金额交易货币',],
    # #     'None': ['交易货币', '支付货币', '计算日期', '清单编号', '估值日期', '组合名义本金额USD', '预付金余额USD', 'SWAP合约价值USD',
    # #              '汇率', '盯市金额CNY', '组合名义本金额加总的近似值交易货币', '预付金余额加总近似值交易货币', '汇率交易货币支付货币',
    # #              '盯市金额加总的近似值支付货币', '初始保障金额加总的近似值交易货币', '维持保障金额加总的近似值交易货币',
    # #              '累计利率收益金额和预付金返息金额的加总近似值交易货币', '应付已付利率收益金额加总的近似值交易货币','组合名义本金额交易货币',
    # #              '盯市比率', '初始保障金额USD', '维持保障金额USD', '累计利息USD', '净值', '应付已付利息USD',
    # #              '预付金余额交易货币', 'SWAP合约价值交易货币', '盯市金额交易货币', '初始保障金额交易货币', '维持保障金额交易货币',
    # #              '累计利息交易货币', '应付已付利息交易货币', '盯市金额支付货币', '结算货币', '汇率交易货币结算货币',
    # #              '盯市金额加总的近似值结算货币', '应付已付利率收益金额和预付金返息金额加总的近似值交易货币'
    # #              ],
    # # }
    #
    # usa_stock_acc = {
    #     'customer_id': ['客户号', ], 'capital_sum': ['盯市金额USD', '盯市金额加总的近似值交易货币', '盯市金额交易货币', ],
    #     'notional_principle': ['组合名义本金额USD', '组合名义本金额加总的近似值交易货币', '组合名义本金额交易货币'],
    #     'prepaid_balance': ['预付金余额', '预付金余额USD', '预付金余额加总近似值交易货币'], 'SWAP_value': ['合约价值', ],
    #     'cumulative_withdrawal': ['累计支取预付金净额CNY', '累计支取预付金净额结算货币'],
    #     'exchange_rate': ['汇率', '汇率交易货币结算货币'], 'initial_margin': ['初始保障金', '初始保障金额加总的近似值交易货币'],
    #     'maintenance_margin': ['维持保障金', '维持保障金USD', '维持保障金额加总的近似值交易货币'],
    #     'net_value': ['净值', ], 'accumulated_interest': ['累计利息', '累计利息USD'], 'interest_paid': ['应付已付利息', ],
    #     'carryover_prepaid_balance': ['结转预付金余额USD', '结转预付金余额交易货币'], 'available_margin_balance': ['可用保障金额加总近似值交易货币'],
    #     'None': ['交易货币', '结算货币', '计算日期', '盯市金额加总的近似值结算货币', '累计利率收益金额和预付金返息金额的加总近似值交易货币',
    #              '应付已付利率收益金额和预付金返息金额加总的近似值交易货币', '预付金可用余额USD', '备注', '可用保障金额加总近似值交易货币']
    # }
    #
    # usa_stock_flow = {
    #     'security_code': ['标的代码'], 'security_name': ['证券简称', '标的简称', ], 'trade_class': ['交易方向'],
    #     'trade_volume': ['交易数量股'],
    #     'trade_price': ['交易均价交易货币'], 'trade_amount': ['成交金额交易货币'], 'currency': ['交易货币', ],
    #     'None': ['交易确认书', '日期'],
    # }
    #
    # @staticmethod
    # def load_us_stock(folder_path: str, date: datetime.date):
    #     from jetend.structures import ExcelMapper
    #     folder_name = folder_path.split(os.path.sep)[-1]
    #     result_dict = dict()
    #
    #     id_product_map = {
    #         '1050': '稳健22号', '1767': '稳健23号', '3089': '久铭1号', '3192': '久铭2号',
    #         '3423': '稳健6号', '3424': '稳健7号', '3448': '全球1号',
    #     }
    #
    #     pdf_list = list()
    #     for file_name in os.listdir(folder_path):
    #         if file_name.startswith('.'):
    #             continue
    #         elif file_name.endswith('pdf'):
    #             #for pdf_file in loader.list_dir(loader.__sub_folder__(folder), 'pdf'):
    #             try:
    #                 pdf_list.append(re.search(r"[^证券市场金融衍生品交易补充确认书]SACTC(\d*)US", file_name).group(1))
    #             except AttributeError: continue
    #         elif file_name.endswith('xlsx'):
    #         # for xls_file in loader.list_dir(loader.__sub_folder__(folder), 'xlsx'):
    #         #     loader.log.info_running(folder, xls_file)
    #             if date > datetime.date(2018, 9, 17):
    #                 pro_id, date_str = re.match(r'Statement_10(\d+)-.*_(\d+)', xls_file).groups()
    #                 assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
    #             elif date <= datetime.date(2018, 9, 17):
    #                 pro_id, some_date, date_str = re.match(
    #                     r"[\w\W]*SACTC(\d+)[^\d]+(\d+)[^(]*\((\d+)\)", file_name
    #                 ).groups()
    #                 assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
    #             else:
    #                 raise NotImplementedError
    #             product_name = id_product_map[pro_id]
    #             identified_dict = {
    #                 'product': product_name, 'date': date,
    #                 'institution': folder_institution_map[folder_name],
    #                 'account_type': folder_path, 'currency': 'USD',
    #             }
    #
    #             if product_name not in result_dict:
    #                 result_dict[product_name] = dict()
    #
    #             content = xlrd.open_workbook(os.path.join(folder_path, file_name))
    #
    #             matcher = ExcelMapper(, ZhongXin.usa_stock_pos, identified_dict, )
    #             matcher.ignore_line.update(['合计', '汇总'])
    #
    #             try:
    #                 pos_list = matcher.map(content.sheet_by_name('Position'))
    #             except xlrd.biffh.XLRDError:
    #                 pos_list = matcher.map(content.sheet_by_name('Underlying'))
    #             result_dict[product_name]['position'] = pos_list
    #
    #             matcher = ExcelMapper(Valuation, ZhongXin.usa_stock_acc, identified_dict, )
    #
    #             try:
    #                 value_acc_obj = matcher.map(content.sheet_by_name('Valuation'))[0]
    #             except xlrd.biffh.XLRDError:
    #                 value_acc_obj = matcher.map(content.sheet_by_name('Calculation'))[0]
    #
    #
    #             matcher = ExcelMapper(Balance, ZhongXin.usa_stock_acc, identified_dict, )
    #             balance_acc_obj = matcher.map(content.sheet_by_name('Balance'))[0]
    #
    #             acc_obj = RawStockAccount.init_from(balance_acc_obj, value_acc_obj)
    #             result_dict[product_name]['account'] = acc_obj
    #
    #
    #             if pro_id in pdf_list:
    #                 matcher = ExcelMapper(RawNormalFlow, ZhongXin.usa_stock_flow, identified_dict, )
    #                 try:
    #                     flow_list = matcher.map(content.sheet_by_name('Flow'))
    #
    #                     for flow_obj in flow_list:
    #                         if flow_obj.trade_class=='买入':
    #                             flow_obj.cash_move = 1.002*flow_obj.trade_amount
    #                         elif flow_obj.trade_class=='卖出':
    #                             flow_obj.cash_move = 0.998 * flow_obj.trade_amount
    #                         else:
    #                             continue
    #                     loader.normal_flow.extend(flow_list)
    #                 except xlrd.biffh.XLRDError:
    #                     raise NotImplementedError
    #                 result_dict[product_name]['fow'] = flow_list
    #             else:
    #                 raise NotImplementedError(file_name)
    #
    #         return result_dict

    margin_pos = {
        # 'product': [''], 'close_price': ['最新价格', ],
        'security_code': ['证券代码', ], 'security_name': ['证券简称', ], 'hold_volume': ['当前数量', ],
        'weight_average_cost': ['成本价', ], 'market_value': ['当前市值', ],
        'None': ['盈亏', '可用数量']
    }
    margin_flow = {
        'date': ['发生日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券简称', ],
        'trade_class': ['摘要代码', ], 'trade_volume': ['发生数量', ],
        'trade_price': ['成交价格', ], 'cash_move': ['发生金额', ],
        'None': ['业务类型', '佣金', '印花税', '过户费', '清算费', '资金余额'],
    }
    margin_acc = {
        'capital_account': ['信用资金帐号', ],
        'capital_sum': ['总资产', ], 'cash_amount': ['资金余额', ], 'market_sum': ['证券市值', ],
        'net_asset': ['净资产', ], 'total_liability': ['负债合计', ],
        'liability_principal': ['融资余额', ], 'liability_amount_interest': ['未了结融资利息', ],
        'liability_amount_fee': ['融资费用', ], 'liability_amount_for_pay': ['待扣收', ],
        'None': [
            '冻结资金', '保证金可用', '可取金额', '融资保证金', '融券市值', '融券费用', '未了结融券利息', '融券保证金',
        ],
    }
    margin_liability = {
        'contract_date': ['合约日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'contract_type': ['合约类型', ], 'contract_volume': ['未了结合约数量', ], 'contract_amount': ['未了结合约金额', ],
        'interest_payable': ['未了结利息', ], 'fee_payable': ['未了结费用', ], 'payback_date': ['归还截止日', ],
        None: [
            '市场', '待扣收', '盈亏金额',
        ]

    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            ZhongXin.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xlsx') or file_name.lower().endswith('xls'):
                if '副本' in file_name:
                    continue
                if '客户对账单' in file_name:
                    target_path = folder_path.replace('中信两融账户', '中信普通账户')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                if '个股期权对账单' in file_name:
                    target_path = folder_path.replace('中信两融账户', '中信期权账户')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path, )
                    continue
                try:
                    product_name, some_id, date_str = re.match(
                        r"([^\d]+\d*[号指数]*)[^\d]+(\d+)_[^\d]+(\d+)", file_name).groups()
                except AttributeError:
                    try:
                        super_product_name, some_id, date_str = re.match(
                            r"([^\d]+\d*[号指数]*)[^\d]+(\d+)_(\d+)", file_name).groups()
                        sub_product_name = super_product_name.split('－')[-1]
                        product_name = re.match(r'([^\d]+\d*[号指数]*)', sub_product_name).group(1)
                    except AttributeError:
                        product_name, date_str = re.match(r"([^\d]+\d*[号指数]+)[^\d]+(\d+)", file_name).groups()
                if re.match(r'久铭稳健\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                if re.match(r'久铭专享\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                if re.match(r'久铭信利', product_name):
                    product_name = '久铭信利'
                if re.match(r'久铭创新稳禄\d+号', product_name):
                    product_name = product_name.replace('久铭', '')

                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': ZhongXin.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                    'offset': OFFSET_OPEN,
                }
                # 初始化result_dict
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ZhongXin.margin_pos, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                matcher.set_start_line('12证券余额').set_end_line('2负债情况')
                # 解决6.28工作簿中没有sheet1只有sheet0的情况
                pos_list = matcher.map(content.sheet_by_index(0))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongXin.margin_flow, identified_dict)
                matcher.ignore_line.update(['合计', ])
                matcher.set_start_line('三业务流水合并对账单')
                flow_list = matcher.map(content.sheet_by_index(0))
                result_dict[product_name]['flow'] = flow_list

                try:
                    matcher = ExcelMapper(ZhongXin.margin_liability, identified_dict, )
                    matcher.ignore_line.update(['合计', ])
                    matcher.set_start_line('3融资融券负债明细合并对账单').set_end_line('三业务流水合并对账单')
                    liability_list = matcher.map(content.sheet_by_index(0))
                except RuntimeWarning:
                    matcher = ExcelMapper(ZhongXin.margin_liability, identified_dict, )
                    matcher.ignore_line.update(['合计', ])
                    matcher.set_start_line('3融资融券负债明细合并对账单').set_end_line('4约定融资约定融券合约明细')
                    liability_list = matcher.map(content.sheet_by_index(0))

                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(ZhongXin.margin_acc, identified_dict)
                matcher.set_start_line('11当前资产情况').set_end_line('12证券余额')
                matcher.map_horizontal(content.sheet_by_index(0))
                try:
                    acc_obj_01 = matcher.map(content.sheet_by_index(0))[0]
                except IndexError:
                    m = Move(os.path.join(folder_path, file_name))
                    m.output_log("IndexError : list index out of range")
                    continue
                    # if '久铭9号' in file_name and '8009202458' in file_name:
                    #     os.remove(os.path.join(folder_path, file_name))
                    #     continue
                    # else:
                    #     raise IndexError

                matcher = ExcelMapper(ZhongXin.margin_acc, identified_dict, )
                matcher.set_start_line('2负债情况').set_end_line('3融资融券负债明细合并对账单')
                try:
                    acc_obj_02 = matcher.map(content.sheet_by_index(0))[0]
                except IndexError as i_e:
                    if len(liability_list) == 0:
                        acc_obj_02 = {
                            'total_liability': 0.0, 'liability_principal': 0.0, 'liability_amount_interest': 0.0,
                            'liability_amount_fee': 0.0, 'liability_amount_for_pay': 0.0,
                        }
                    else:
                        raise i_e
                assert isinstance(acc_obj_01, dict) and isinstance(acc_obj_02, dict)
                acc_obj = acc_obj_01.copy()
                acc_obj.update(acc_obj_02)
                acc_obj['cash_available'] = acc_obj['cash_amount']
                result_dict[product_name]['account'] = acc_obj

                match_margin_pos_acc(pos_list, acc_obj)
                # match_margin_liability_acc(liability_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            elif file_name.lower().endswith('pdf'):
                if file_name.startswith('久铭6号'):
                    product_name = '久铭6号'
                else:
                    raise NotImplementedError(file_name)
                if product_name not in result_dict:
                    result_dict[product_name] = None
                    product_file_map[product_name] = file_name
                else:
                    continue
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    future_acc = {
        'currency': ['币种', ], 'customer_id': ['客户号', ], 'market_sum': ['保证金占用', ],
        'last_capital_sum': ['期初结存', ], 'market_pl': ['持仓盯市盈亏', ], 'realized_pl': ['平仓盈亏', ],
        'trade_fee': ['手续费', ], 'out_in_cash': ['出入金', ],
        'capital_sum': ['客户权益', ], 'cash_amount': ['可用资金', ],
    }
    future_flow = {
        'date': ['成交日期', ], 'security_name': ['品种', ], 'security_code': ['合约', ],
        'trade_class': ['买卖', ], 'trade_price': ['成交价', ], 'trade_volume': ['手数', ],
        'trade_amount': ['成交额', ], 'offset': ['开平', ], 'trade_fee': ['手续费', ], 'realize_pl': ['平仓盈亏', ],
        'investment_tag': ['投保', ], 'cash_move': ['权利金收支', ],
        'None': ['交易所', '投保', '权利金收支', '成交序号', ]
    }
    future_pos = {
        'security_code': ['合约', ], 'security_name': ['品种', ],
        'long_position': ['买持', ], 'short_position': ['卖持', ],
        'buy_average_cost': ['买均价', ], 'sell_average_cost': ['卖均价', ],
        'prev_settlement': ['昨结算', ], 'settlement_price': ['今结算', ],
        'market_pl': ['持仓盯市盈亏', ], 'margin': ['保证金占用', ], 'investment_tag': ['投保', ],
        'long_mkv': ['多头期权市值', ], 'short_mkv': ['空头期权市值', ],
        'None': ['多头期权市值'],
    }
    future_id_product_map = {
        '800600388': '久铭5号',
    }

    @staticmethod
    def load_future(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        folder_result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('txt'):
                ZhongXin.log.debug(file_name)
                # 20200407_800600388_交易结算单
                date_str, pro_id = re.match(r"(\d+)_(\d+)_交易", file_name).groups()
                product_name = ZhongXin.future_id_product_map[pro_id]
                if product_name not in folder_result_dict:
                    folder_result_dict[product_name] = dict()
                product_file_map[product_name] = file_name
                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                ZhongXin.log.debug(content)
                identified_dict = {
                    'date': date, 'product': product_name,
                    'institution': ZhongXin.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                }

                matcher = TextMapper(ZhongXin.future_acc, identified_dict)
                matcher.set_line_sep('|')
                check = re.search(r"资金状况([\w\W]*)货币质押变化金额", content, re.M)
                if check:
                    acc = check.group(1)
                else:
                    acc = re.search(r"资金状况([\w\W]*)", content, re.M).group(1)
                acc = acc.replace('手 续 费', '手续费').replace('出 入 金', '出入金')
                acc = re.sub(r'[a-zA-Z/]', '', acc)
                matcher.map_horizontal(acc)
                acc_obj = matcher.form_new()
                folder_result_dict[product_name]['account'] = acc_obj

                matcher = TextMapper(ZhongXin.future_pos, identified_dict)
                matcher.set_line_sep('|')
                matcher.ignore_line.update(['Product'])
                check = re.search(r"持仓汇总([\w\W]*)共.*\d+.*条[\w\W]", content, re.M)
                if check:
                    pos = check.group(1)
                else:
                    pos = ''
                pos_list = matcher.map(pos)
                folder_result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(ZhongXin.future_flow, identified_dict)
                matcher.set_line_sep('|')
                matcher.ignore_line.update(['Product'])
                check = re.search(r"成交记录([\w\W]*)共.*\d+条[\w\W]*本地强平", content, re.M)
                if check:
                    flow = check.group(1)
                else:
                    flow = ''
                flow_list = matcher.map(flow)
                folder_result_dict[product_name]['flow'] = flow_list

                confirm_future_flow_list(flow_list)
                match_future_pos_acc(pos_list, acc_obj)
            else:
                raise NotImplementedError(file_name)

        return folder_result_dict, product_file_map

    option_pos = {
        'security_code': ['期权合约代码', ], 'security_name': ['期权合约名称', ],
        # 'rights_warehouse': ['权利仓数量', ], 'voluntary_warehouse': ['义务仓数量', ],
        # 'buy_average_cost': ['买均价', ], 'sell_average_cost': ['卖均价', ],
        'warehouse_class': ['持仓类别', ], 'warehouse_volume': ['当前数量', ], 'warehouse_cost': ['成本价', ],
        'settlement_price': ['结算价', ],
        # 'underlying': ['标的', ],
        # 'maintenance_margin': ['维持保证金', ], 'underlying_close_price': ['标的物收盘价', ],
        'market_value': ['持仓市值', ],  # 'reserve_tag': ['备兑标识', ], 'currency': ['', ],
        'None': ['交易类别', '期权类别', '可用数量'],
    }
    option_acc = {
        'capital_account': ['资产账户', ],
        'cash_amount': ['现金资产', ], 'market_sum': ['期权市值', ], 'capital_sum': ['总权益', ],
        'currency': ['币种', ],
        # 'None': ['可用资金', ],
    }
    option_flow = {
        'security_code': ['期权合约代码', ], 'security_name': ['期权合约名称', ], 'trade_class': ['买卖方向', ],
        'offset': ['开平仓方向', ], 'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ],
        'trade_amount': ['成交金额', ], 'trade_fee': ['手续费', ],

        'None': ['发生日期', '成交编号', '证券代码', '证券名称', '备兑标志', '当前余额'],
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            # 忽略隐藏文件
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('xlsx'):
                ZhongXin.log.debug(file_name)
                if file_name.startswith('上海久铭投资'):
                    if '久铭9号' in file_name:
                        product_name = '久铭9号'
                    elif '专享7号' in file_name:
                        product_name = '专享7号'
                    elif '稳健23号' in file_name:
                        product_name = '稳健23号'
                    elif '久铭6号' in file_name:
                        product_name = '久铭6号'
                    elif '久铭专享6号' in file_name:
                        product_name = '专享6号'
                    elif '久铭专享8号' in file_name:
                        product_name = '专享8号'
                    elif '久铭信利私募' in file_name:
                        product_name = '久铭信利'
                    elif '久铭2号' in file_name:  # wave zhou
                        product_name = '久铭2号'
                    else:
                        raise NotImplementedError(file_name)
                    assert date.strftime('%Y%m%d') in file_name, file_name
                    # product_name = re.match(r"([^\d]+\d*[号指数]*)[^\d]+", file_name.split('-')[1]).group(1)
                    # some_id, date_str = re.match(r"(\d+)_(\d+)", file_name.split('-')[-1]).groups()
                    # product_name, some_id, date_str = re.match(
                    #     r"上海[^\d]+-([^\d]+\d*[号指数]*)[^\d]+\-[^\d]+\-(\d+)_(\d+)", file_name
                    # ).groups()
                else:
                    product_name, some_id, date_str = re.match(
                        r"([^\d]+\d*[号指数]*)[^\d]+(\d+)[^\d]+(\d+)", file_name).groups()
                    assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'date': date, 'product': product_name, 'currency': 'RMB',
                    'institution': ZhongXin.folder_institution_map[folder_name],
                    'account_type': folder_path,
                }
                # 初始化result_dict
                assert product_name in PRODUCT_NAME_RANGE, '{} - {}'.format(product_name, file_name)
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name

                # content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                #
                # matcher = ExcelMapper( ZhongXin.option_pos, identified_dict)
                # matcher.set_start_line('合约持仓清单').set_end_line('组合持仓清单')
                # matcher.ignore_line.update(['合计'])
                # pos_list = matcher.map(content.sheet_by_name('Sheet1'))
                # result_dict[product_name]['position'] = pos_list
                #
                # matcher = ExcelMapper( ZhongXin.option_acc, identified_dict)
                # matcher.map_horizontal(content.sheet_by_name('Sheet1'))
                # acc_obj = matcher.form_new()
                # result_dict[product_name]['account'] = acc_obj
                #
                # matcher = ExcelMapper( ZhongXin.option_flow, identified_dict)
                # matcher.set_start_line('对帐单').set_end_line('合约持仓清单')
                # matcher.ignore_line.update(['合计'])
                # flow_list = matcher.map(content.sheet_by_name('Sheet1'))
                # result_dict[product_name]['flow'] = flow_list
            elif file_name.lower().endswith('xls'):
                if file_name.startswith('905-客户-期权客户'):
                    product_name = '久铭9号'
                elif file_name.startswith('904-客户-期权客户'):
                    product_name = '稳健22号'
                elif file_name.startswith('9008016945'):
                    product_name = '专享7号'
                elif file_name.startswith('9008017753'):
                    product_name = '久铭信利'
                else:
                    raise NotImplementedError(file_name)
                # 初始化result_dict
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
            elif file_name.lower().endswith('rar'):
                os.remove(os.path.join(folder_path, file_name))
                continue

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    valuation_line = {
        'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['币种', ],
        'exchange_rate': ['汇率', ], 'hold_volume': ['数量', ], 'average_cost': ['单位成本', ],
        'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价', '收市价', ],
        'total_market_value': ['市值-本币', '市值', '市值本币'],
        'None': [
            '成本占比', '市值占比', '估值增值-本币', '停牌信息', '权益信息', '市值占净值', '成本占净值', '估值增值', '估值增值本币',
        ]
    }

    @staticmethod
    def load_valuation_table(file_path: str):
        from jetend.Constants import PRODUCT_CODE_NAME_MAP
        from jetend.structures import ExcelMapper
        from utils import identify_valuation_records
        file_name = file_path.split(os.path.sep)[-1]
        ZhongXin.log.debug_running('读取托管估值表', file_name)
        # 文件名：SY0689久铭10号私募证券投资基金委托资产资产估值表20190831 SCJ125久铭50指数私募基金委托资产资产估值表20190831
        product_code, product, date_str = re.search(r'([A-Za-z0-9]+)_久铭(\w+)私募[^\d]+(\d+)', file_name).groups()
        product_name = PRODUCT_CODE_NAME_MAP[product_code]
        date = datetime.datetime.strptime(date_str, '%Y%m%d')
        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '中信证券',
        }
        mapper = ExcelMapper(ZhongXin.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)


if __name__ == '__main__':
    print(ZhongXin.load_margin(r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190726\中信两融账户', datetime.date(2019, 7, 26)))
    # print(ZhongXin.load_margin(r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190701\中信两融账户', datetime.date(2019, 7, 1)))
    # print(ZhongXin.load_margin(r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190605\中信两融账户', datetime.date(2019, 6, 5)))
