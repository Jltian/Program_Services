# -*- encoding: UTF-8 -*-
import os
import re
import datetime
import xlrd
import shutil

from Abstracts import AbstractInstitution
from Checker import *


class ZhaoShang(AbstractInstitution):
    """招商"""
    folder_institution_map = {
        '招商普通账户': '招商',
        '招商两融账户': '招商两融',
        '招商期权账户': '招商期权',
    }

    normal_pos = {
        'shareholder_code': ['股东代码'], 'security_code_name': ['产品代码简称', ],
        'hold_volume': ['库存数', ], 'market_value': ['市值', ], 'weight_average_cost': ['成本价', ],
        'None': [
            '当日买入', '当日买入金额', '摘要', '当日卖出', '当日卖出金额', '可用数量', '牛卡号', '市场', '发生日期',
            '成交数', '成交均价', '成交金额', '手续费', '印花税等', '变动金额', '资金余额', '招商证券北京车公庄西路证券营业部对账单',
        ]
    }
    normal_flow = {
        'date': ['发生日期', ], 'shareholder_code': ['股东代码', ],
        'trade_class': ['摘要', ], 'trade_volume': ['成交数', ], 'trade_amount': ['成交金额', ],
        'trade_price': ['成交均价', ], 'cash_move': ['变动金额', ],
        'None': ['市场', '库存数', '手续费', '印花税等', '资金余额', '牛卡号'],
    }
    normal_acc = {
         'currency': ['货币类型', ], 'capital_sum': ['资产合计', ], 'cash_amount': ['资金余额', ], 'market_sum': ['市值合计', ],
         'None': ['牛卡号', ]
    }

    # option_pos = {
    #     'security_code': ['期权合约代码', ], 'security_name': ['期权合约名称', ],
    #     # 'rights_warehouse': ['权利仓数量', ], 'voluntary_warehouse': ['义务仓数量', ],
    #     # 'buy_average_cost': ['买均价', ], 'sell_average_cost': ['卖均价', ],
    #     'warehouse_class': ['持仓类别', ], 'warehouse_volume': ['当前数量', ], 'warehouse_cost': ['成本价', ],
    #     'settlement_price': ['结算价', ],
    #     # 'underlying': ['标的', ],
    #     # 'maintenance_margin': ['维持保证金', ], 'underlying_close_price': ['标的物收盘价', ],
    #     'market_value': ['持仓市值', ],  # 'reserve_tag': ['备兑标识', ], 'currency': ['', ],
    #     'None': ['交易类别', '期权类别', '可用数量'],
    # }
    # option_acc = {
    #     'capital_account': ['资产账户', ],
    #     'cash_amount': ['现金资产', ], 'market_sum': ['期权市值', ], 'capital_sum': ['总权益', ],
    #     'currency': ['币种', ],
    #     # 'None': ['可用资金', ],
    # }
    # option_flow = {
    #     'security_code': ['期权合约代码', ], 'security_name': ['期权合约名称', ],
    #     'warehouse_class': ['持仓类别', ], 'trade_class': ['买卖方向', ], 'offset': ['开平仓方向', ],
    #     'reserve_tag': ['备兑标志', ], 'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ],
    #     'trade_amount': ['成交金额', ],  'trade_fee': ['手续费', ],  # cash_move currency
    #     'None': ['发生日期', '交易类别', '证券代码', '证券名称', '当前余额'],
    # }
    #
    # option_bank_flow = {
    #     'currency': ['币种类别', ], 'trade_class': ['业务标志', ], 'cash_move': ['发生金额', ],
    #     'None': ['发生日期', '当前时间', '后资金额', ],
    # }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        id_product_map = {
            '0537535101': '久铭1号', '0537535102': '久铭2号',  '0537535013': '久铭3号', '0537535103': '稳健11号',
            '0537535003': '稳健3号', '0537390166': '稳健16号', '0537536306': '稳健10号', '0537536302': '稳健9号',
            '0537536301': '稳健15号', '0537536300': '稳健18号', '0537535012': '稳利2号', '0537535011': '双盈1号',
            '0537535005': '稳健5号', '0537536305': '稳健6号', '0537556778': '稳健22号',
        }

        for file_name in os.listdir(folder_path):
            ZhaoShang.log.debug_running(folder_name, file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            if '副本' in file_name:
                continue
            elif file_name.lower().endswith('xlsx'):
                some_id, date_str = re.match(r'(\d+)[^\d]+(\d+)', file_name).groups()
                product_name = id_product_map[some_id]

                identified_dict = {
                    'product': product_name, 'date': date, 'currency': 'RMB',
                    'institution': ZhaoShang.folder_institution_map[folder_name],
                    'account_type': folder_name, 'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ZhaoShang.normal_flow, identified_dict)
                # matcher.set_duplicated_tolerance(True)
                matcher.set_start_line('发生日期').set_end_line('请注意交易类资金变动的变动金额为成交金额含费用如印花税手续费过户费等')
                # matcher.set_start_line('资金情况')
                # matcher.set_end_line('请注意：交易类资金变动的变动金额为成交金额含费用(如印花税手续费过户费等)')
                flow_list = matcher.map(content.sheet_by_name('导出数据'))
                # 解决招商两融账户里面成交金额、交易数量、成交均价对不上的问题
                sub_map_trade_class = [
                    '证券卖出(002714)牧原股份', '证券卖出(600566)济川药业', '证券卖出(601939)建设银行', '证券买入(00939)建设银行',
                    '证券买入(600519)贵州茅台', '证券买入(000858)五粮液', '证券卖出(688168)N安博通', '证券卖出(600519)贵州茅台',
                    '证券卖出(000858)五粮液',  # '融资融券证券冻结(600519)贵州茅台', '融资融券证券冻结(000858)五粮液'
                ]
                for flow in flow_list:
                    assert isinstance(flow, dict), str(flow)
                    trade_class = str_check(flow['trade_class'])
                    if flow['trade_class'] in sub_map_trade_class:
                        flow['trade_price'] = float_check(flow['trade_amount']) / float_check(flow['trade_volume'])
                    else:
                        pass
                    if '(' in trade_class and ')' in trade_class:
                        if ',' in trade_class:
                            flow['security_code'], flow['security_name'] = '', ''
                        else:
                            try:
                                flow['trade_class'], flow['security_code'], flow['security_name'] = re.search(
                                    r'(\w+)\((\d+)\)(\w*)', trade_class).groups()
                            except AttributeError as a_error:
                                print(flow)
                                raise a_error
                        # print(trade_class, flow['security_code'], flow['security_name'])
                    else:
                        trade_class, flow['security_code'], flow['security_name'] = '|', '', ''
                    # print(flow['trade_price'],flow['trade_volume'])
                    # if flow['trade_price'] == 0.00 or flow['trade_volume'] == 0.00:
                    #     flow['trade_amount'] = 0.00
                    flow['trade_amount'] = float_check(flow['trade_price']) * float_check(flow['trade_volume'])

                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhaoShang.normal_pos, identified_dict)
                matcher.set_start_line('交易类资金变动的变动金额为成交金额含费用')
                matcher.set_end_line('股票库存数为上一交易日余额当日买卖和市值仅供参考')
                matcher.set_duplicated_tolerance(True)
                pos_list = matcher.map(content.sheet_by_name('导出数据'))
                for pos in pos_list:
                    assert isinstance(pos, dict), str(pos)
                    security_code_name = pos['security_code_name']
                    if ' ' in security_code_name:
                        security_code_name = security_code_name.split(' ')
                        pos['security_code'] = security_code_name[0]
                        pos['security_name'] = security_code_name[1]
                    else:
                        raise NotImplementedError(pos)
                result_dict[product_name]['position'] = pos_list

                # 资金
                matcher = ExcelMapper(ZhaoShang.normal_acc, identified_dict)
                matcher.map_horizontal(content.sheet_by_name('导出数据'))
                acc_obj = matcher.form_new()
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            elif file_name.lower().endswith('xls'):
                if '期权' in file_name:
                    target_path = folder_path.replace('招商普通账户', '招商期权账户')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                elif file_name.startswith('9970'):
                    target_path = folder_path.replace('招商普通账户', '招商两融账户')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                # if '个股期权对账单' in file_name:
                #     target_path = folder_path.replace('中信两融账户', '中信期权账户')
                #     if not os.path.exists(target_path):
                #         os.makedirs(target_path)
                #     shutil.move(os.path.join(folder_path, file_name), target_path)
                #     continue
            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map

    margin_pos = {
        # 'product': [''], 'close_price': ['最新价格', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'hold_volume': ['当前余额', ],
        'weight_average_cost': ['参考成本价', ], 'market_value': ['市值', ], 'close_price': ['最新价'],
        'total_cost': ['参考成本', ], 'shareholder_code': ['股东代码'],
        'None': ['股份可用数', '浮动盈亏', '市场']
    }
    margin_flow = {
        'date': ['发生日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'shareholder_code': ['股东代码', ],
        'trade_class': ['摘要', '摘要名称', ], 'trade_volume': ['成交数量', '股份发生数', ], 'trade_amount': ['成交金额', ],
        'trade_price': ['成交均价', '成交价格', ], 'cash_move': ['资金发生数', ],
        'None': ['佣金', '印花税', '过户费', '其他费用', '市场', '委托价格', '委托数量', '本次资金余额', '手续费','日终融资利息自动扣收', ],
    }
    margin_acc = {
        'capital_account': ['信用资金账号', '资金账号'],
        'cash_amount': ['资金余额', ],
        'capital_sum': ['资产合计', '资产总值'],
        'market_sum': ['市值合计', '证券市值'],
        'total_liability': ['融资总负债', '融资负债总额'],
        'liability_principal': ['未还融资本金', ],
        'liability_amount_interest': ['未结融资利息', ],
        'liability_amount_for_pay': ['已结未付融资利息', ],
        None: [
            '未还其他融资利息','日终融资利息自动扣收',
        ]
    }
    # margin_liability = {
    #     'contract_date': ['合约日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
    #     'contract_type': ['合约类型', ], 'contract_volume': ['未了结合约数量', ], 'contract_amount': ['未了结合约金额', ],
    #     'interest_payable': ['未了结利息', ], 'fee_payable': ['未了结费用', ], 'payback_date': ['归还截止日', ],
    #     None: [
    #         '市场', '待扣收', '盈亏金额',
    #     ]
    # }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        id_product_map = {
            '9970532941': '双盈1号', '9970532942': '稳利2号', '9970532953': '久铭3号',
            '9970532973': '稳健3号', '9970532975': '稳健5号', '9970533059': '稳健15号',
            '9970533060': '稳健18号', '9970533000': '稳健11号', '9970533057': '稳健9号',
            '9970533058': '稳健10号', '9970532915': '稳健16号', '9970533302': '稳健22号',
            '22': '稳健22号','9': '稳健9号',
        }

        for file_name in os.listdir(folder_path):
            ZhaoShang.log.debug(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().split('.')[-1] in ('xls', 'xlsx'):
                some_id = re.search(r"(\d+)", file_name).groups()[0]
                if some_id == '905':
                    product_name = '稳健22号'
                    if product_name not in result_dict:
                        result_dict[product_name] = None
                    product_file_map[product_name] = file_name
                    continue

                product_name = id_product_map[some_id]

                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': ZhaoShang.folder_institution_map[folder_name], 'currency': 'RMB',
                    'offset': OFFSET_OPEN,
                }
                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                matcher = ExcelMapper(ZhaoShang.margin_flow, identified_dict, )
                matcher.ignore_line.update(['合计'])
                matcher.ignore_cell.update(['', ])
                matcher.set_start_line('历史成交明细').set_end_line('股份余额汇总')
                flow_list = matcher.map(content.sheet_by_name('信用账户对账单'))
                # print(flow_list)
                # 解决0709和0716招商两融稳健22号流水里面无证券代码的情况
                SUB_SECURITY_CODE_MAP = {
                    '建设银行': '601939.SH', '完美世界': '002624.SZ', '济川药业': '600566.SH',
                    '五 粮 液': '000858.SZ', '贵州茅台': '600519.SH', '工商银行': '601398.SH',
                    '春秋航空': '601021', 'XD春秋航': '601021.SH','万 科Ａ':'000002.SZ','永辉超市':'601933.SH',
                    '首旅酒店': '600258.SH','万  科Ａ':'000002.SZ','华贸物流':'603128.SH','环旭电子':'60jm33891.SH',
                    '复星医药': '600196.SH','金禾实业': '002597.SZ','正邦科技': '002157.SZ','牧原股份': '002714.SZ',
                    '牧原转债': '127045.SZ','宁波银行': '002142.SZ','美的集团': '000333.SZ','上港集团': '600018.SH',
                    '宁行A1配': '082142.SZ','博威合金':'601137.SH','石头科技':'688169.SH','坚朗五金':'002791.SZ','奥佳华':'002614.SZ'
                }
                for flow in flow_list:
                    if flow['security_name'] in SUB_SECURITY_CODE_MAP:
                        flow['security_code'] = SUB_SECURITY_CODE_MAP[flow['security_name']]
                    elif flow['security_name'] in ('/', '、', ):
                        flow['security_code'] = ''
                    else:
                        raise NotImplementedError(flow['security_name'])
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhaoShang.margin_pos, identified_dict, )
                matcher.ignore_line.update(['合计'])
                matcher.ignore_cell.update(['', '沪Ａ', '深Ａ息归本'])
                matcher.set_start_line('股份余额汇总').set_end_line('融资负债')
                # pos_list = matcher.map(content.sheet_by_name(''.join([some_id, '1'])))
                pos_list = matcher.map(content.sheet_by_name('信用账户对账单'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhaoShang.margin_acc, identified_dict)
                matcher.map_horizontal(content.sheet_by_name('信用账户对账单'))
                acc_obj_01 = matcher.form_new()
                # matcher = ExcelMapper(ZhaoShang.margin_acc, identified_dict)
                # matcher.ignore_cell.update(['', ])
                # matcher.set_start_line('以下为人民币的融资负债情况').set_end_line('以下为人民币的融券负债情况')
                # try:
                #     acc_obj_02 = matcher.map(content.sheet_by_name('信用账户对账单'))[0]
                # except IndexError as e:
                #     print(matcher.map(content.sheet_by_name(''.join([some_id, '1']))))
                #     raise e
                # acc_obj = acc_obj_01.copy()
                # acc_obj.update(acc_obj_02)
                acc_obj = acc_obj_01
                acc_obj['liability_principal'] = 0.0
                acc_obj['liability_amount_fee'] = 0.0
                acc_obj['liability_amount_interest'] = 0.0
                acc_obj['liability_amount_for_pay'] = 0.0
                acc_obj['cash_available'] = acc_obj['cash_amount']
                # acc_obj['liability_amount_for_pay'] = 0.0
                result_dict[product_name]['account'] = acc_obj

                result_dict[product_name]['liabilities'] = list()

                match_margin_pos_acc(pos_list, acc_obj)
                # match_margin_liability_acc(liability_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map

    option_pos = {
        'security_code': ['期权合约代码', ], 'security_name': ['期权合约名称', ],
        'warehouse_class': ['持仓类别', ], 'warehouse_volume': ['当前数量', ],  'warehouse_cost': ['成本价', ],
        'settlement_price': ['结算价', ], 'hold_volume': ['当前数量', ],
        'market_value': ['持仓市值', ],
        'None': ['交易类别', '期权类别', '可用数量', '维持保证金', '发生日期', '组合策略占用数量'],
    }
    option_acc = {
        'cash_amount': ['期末余额', ], 'market_sum': ['期权市值', ], 'capital_sum': ['总权益', ],
        'cash_available': ['当前余额', ],
        'None': ['发生日期', '客户编号', '客户姓名', '资产账户', '资产属性', '币种', '期初余额', '冻结金额', '已用保证金', '可用保证金', '风险度', '权利金汇总', '出入金汇总', '总费用'],
    }
    option_flow = {
        'security_code': ['期权合约代码', ], 'security_name': ['期权合约名称', ],
        'warehouse_class': ['持仓类别', ], 'trade_class': ['买卖方向', ], 'offset': ['开平仓方向', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
        'trade_fee': ['手续费', ], 'cash_rest': ['当前余额', ], 'reserve_tag': ['备兑标志', ],
        'cash_move': ['清算金额', ],
        'None': [
            '发生日期', '交易类别', '证券代码', '证券名称','组合方向'
        ],
    }
    option_acc_flow = {
        'trade_class': ['业务标志', ], 'cash_move': ['发生金额', ], 'cash_rest': ['后资金额', ],
        'None': ['发生日期', '当前时间', '币种类别', ]
    }
    option_id_product_map = {
        '68880537536302': '稳健9号', '68880537556778': '稳健22号',
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xls'):
                if file_name.startswith('905'):
                    if file_name.startswith('905') and file_name.endswith(date.strftime('%Y%m%d.xls')):
                        product_name = '稳健22号'
                    elif file_name.startswith('905') and file_name.endswith('0537536302.xls'):
                        product_name = '稳健9号'
                        raise NotImplementedError('{} 未转换成 xlsx'.format(file_name))
                    else:
                        raise NotImplementedError(file_name)
                else:
                    some_id = re.match(r'(\d+)', file_name).group(1)
                    product_name = ZhaoShang.option_id_product_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, file_name
                if product_name not in result_dict:
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
                # identified_dict = {
                #     'product': product_name, 'date': date, 'account_type': folder_path,
                #     'institution': folder_institution_map[folder_name],
                #     'warehouse_class': '权利仓',
                # }
                # content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                #
                # matcher = ExcelMapper(GuoJun.option_acc, identified_dict)
                # acc_obj = matcher.map(content.sheet_by_name(xls_file.split('.')[0]))[0]
                # result_dict[product_name]['account'] = acc_obj
                #
                # option_flow_filename = '历史交收明细查询{}.xls'.format(pro_id)
                # if os.path.exists(os.listdir(folder_path, option_flow_filename)):
                #     content = xlrd.open_workbook(os.listdir(folder, option_flow_filename))
                #     matcher = ExcelMapper(GuoJun.option_flow, identified_dict)
                #     flow_list = matcher.map(content.sheet_by_name(option_flow_filename.split('.')[0]))
                # else:
                #     flow_list = DataList(RawOptionFlow)
                # result_dict[product_name]['fow'] = flow_list
                #
                # pos_list = DataList(RawOptionPosition)
            # elif file_name.lower().endswith('xlsx'):
            #     if file_name.startswith('905'):
            #         if file_name.startswith('905') and file_name.endswith('0537536302.xlsx'):
            #             product_name = '稳健9号'
            #         elif file_name.startswith('905') and file_name.endswith('6778.xlsx'):
            #             product_name = '稳健22号'
            #         else:
            #             raise NotImplementedError(file_name)

            elif file_name.lower().endswith('xlsx'):
                if file_name.startswith('06005'):
                    if file_name.__contains__('0537536302'):
                        product_name = '稳健9号'
                    elif file_name.__contains__('0537556778'):
                        product_name = '稳健22号'
                    else:
                        raise NotImplementedError(file_name)
                else:
                    some_id = re.match(r'(\d+)', file_name).group(1)
                    product_name = ZhaoShang.option_id_product_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, file_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_path,
                    'institution': ZhaoShang.folder_institution_map[folder_name],
                    'warehouse_class': '权利仓', 'currency': 'RMB',
                }
                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                # option_flow_filename = '历史交收明细查询{}.xls'.format(pro_id)
                # if os.path.exists(os.listdir(folder_path, option_flow_filename)):
                #     content = xlrd.open_workbook(os.listdir(folder, option_flow_filename))
                #     matcher = ExcelMapper(GuoJun.option_flow, identified_dict)
                #     flow_list = matcher.map(content.sheet_by_name(option_flow_filename.split('.')[0]))
                # else:
                #     flow_list = DataList(RawOptionFlow)
                # result_dict[product_name]['fow'] = flow_list

                matcher = ExcelMapper(ZhaoShang.option_flow, identified_dict)
                matcher.ignore_line.update(['合计'])
                flow_list = matcher.map(content.sheet_by_name('对账单'))
                for flow_obj in flow_list:
                    flow_obj['reserve_tag'] = '投'
                    # assert 'trade_class' in flow_obj, flow_obj
                    # if str_check(flow_obj['trade_class']) in ('买',) and str_check(flow_obj['offset']) in ('开仓',):
                    #     flow_obj['cash_move'] = - abs(
                    #         float_check(flow_obj['trade_amount'])
                    #     ) - abs(float_check(flow_obj['trade_fee']))
                    # else:
                    #     pass
                    # flow_obj['cash_move'] = float_check(flow_obj['trade_amount'])
                    # flow_obj['trade_amount'] = 0.0
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhaoShang.option_pos, identified_dict)
                matcher.ignore_line.update(['合计'])
                pos_list = matcher.map(content.sheet_by_name('合约持仓清单'))
                for pos_obj in pos_list:
                    pos_obj['warehouse_class'] = '权利方'
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhaoShang.option_acc, identified_dict)
                matcher.set_start_line('股票期权资金对账单')
                pos_list = matcher.map(content.sheet_by_name('资金情况'))
                result_dict[product_name]['position'] = pos_list
                # if product_name == '稳健9号' and folder_name.__contains__('招商'):
                #     matcher.map_horizontal(content.sheet_by_name('资金情况'))
                #     acc_obj = matcher.form_new()
                #     result_dict[product_name]['account'] = acc_obj
                # matcher.map_horizontal(content.sheet_by_name('资金情况'))
                # acc_obj = matcher.form_new()
                # result_dict[product_name]['account'] = acc_obj
                #
                # confirm_option_flow_list(flow_list)

                match_option_pos_acc(pos_list, acc_obj)

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    valuation_line = {
        # 'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['币种', ],
        # 'exchange_rate': ['汇率', ], 'hold_volume': ['数量', ], 'average_cost': ['单位成本', ],
        # 'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价', '收市价', ],
        # 'market_value': ['市值-本币', '市值', '市值本币'], 'value_changed': ['估值增值-本币', '估值增值本币', '估值增值'],
        # 'suspension_info': ['停牌信息', ],
        # 'None': [
        #     '成本占比', '市值占比', '权益信息', '市值占净值', '成本占净值',
        #     ],
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
        ZhaoShang.log.debug_running('读取托管估值表', file_name)
        # 文件名：SY0689久铭10号私募证券投资基金委托资产资产估值表20190831 SCJ125久铭50指数私募基金委托资产资产估值表20190831
        product_id, product, date_str = re.search(r'([A-Za-z0-9]+)(\w+)私募[^\d]+(\d+)', file_name).groups()
        product_code, product_name = product_id, PRODUCT_CODE_NAME_MAP[product_id]
        date = datetime.datetime.strptime(date_str, '%Y%m%d')
        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '招商证券',
        }
        mapper = ExcelMapper(ZhaoShang.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)


if __name__ == '__main__':
    print(ZhaoShang.load_normal(
        r'D:\Documents\久铭产品交割单20190906\招商普通账户',
        datetime.date(2019, 9, 6),
    ))

    # print(ZhaoShang.load_margin(
    #     r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190605\招商两融账户',
    #     datetime.date(2019, 6, 5)))

    # @staticmethod
    # def load_option(folder_path: str, date: datetime.date):
    #     from jetend.structures import ExcelMapper
    #     folder_name = folder_path.split(os.path.sep)[-1]
    #     result_dict = dict()
    #     # from journal_load.Mapper import ExcelMapper
    #     # from sheets.raws.RawAccount import RawAccount
    #     # from sheets.raws.RawOption import RawOptionFlow, RawOptionPosition
    #     # from journal_load.Loader import JournalLoader
    #     # assert isinstance(loader, JournalLoader), str(type(loader))
    #     id_product_map = {
    #         '905': '久铭1号',
    #     }
    #     # 全目录文件扫描
    #     for file_name in os.listdir(folder_path):
    #         # 忽略隐藏文件
    #         if file_name.startswith('.'):
    #             continue
    #         elif file_name.lower().endswith('xls'):
    #             if date < datetime.date(2018, 1, 2):
    #                 pro_id, date_str = re.search(r"[^\d]+\d+[号指数]+[^\d]*(\d+)[^\d]+(\d+)", file_name).groups()
    #             else:
    #                 pro_id, date_str = re.search(r"(\d+)-客户-[^\d]+(\d+)", file_name).groups()
    #             product_name = id_product_map[pro_id]
    #             assert date < datetime.date(date_str)
    #             identified_dict = {
    #                 'date': date, 'product': product_name, 'currency': 'RMB',
    #                 'institution': folder_institution_map_03[folder_name],
    #                 'account_type': folder,
    #             }
    #             content = xlrd.open_workbook(loader.__sub_folder__(folder, xls_file))
    #
    #             matcher = ExcelMapper( ZhaoShang.option_flow, identified_dict)
    #             matcher.ignore_line.update(['合计'])
    #             flow_list = matcher.map(content.sheet_by_name('对帐单'))
    #             matcher = ExcelMapper( ZhaoShang.option_bank_flow, identified_dict)
    #             matcher.ignore_line.update(['合计'])
    #             try:
    #                 bank_flow_list = matcher.map(content.sheet_by_name('资金变动清单'))
    #                 for bank_flow_obj in bank_flow_list:
    #                     bank_flow_obj.trade_price = bank_flow_obj.cash_move
    #                     bank_flow_obj.trade_volume = 1
    #                 flow_list.extend(bank_flow_list)
    #             except AttributeError:
    #                 continue
    #             result_dict[product_name]['fow'] = flow_list
    #
    #             matcher = ExcelMapper( ZhaoShang.option_pos, identified_dict)
    #             matcher.ignore_line.update(['合计'])
    #             pos_list = matcher.map(content.sheet_by_name('合约持仓清单'))
    #             result_dict[product_name]['position'] = pos_list
    #
    #             matcher = ExcelMapper(RawAccount, ZhaoShang.option_acc, identified_dict)
    #             matcher.map_horizontal(content.sheet_by_name('资金情况'))
    #             acc_obj = matcher.form_new()
    #             result_dict[product_name]['account'] = acc_obj
    #         else:
    #             raise NotImplementedError(file_name)
    #
    #     return result_dict
    #
    #         # # 检查数据匹配
    #         # loader.option_flow.extend(flow_list)
    #         # loader.option_position.extend(pos_list)
    #         # loader.account_list.append(acc_obj)
    #         # loader.check_flow_acc_match(folder, product_name, flow_list, acc_obj)
    #         # loader.check_flow_pos_match(folder, product_name, flow_list, pos_list)
    #         # loader.check_pos_acc_match(pos_list, acc_obj)
