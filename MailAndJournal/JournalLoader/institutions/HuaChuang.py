# -*- encoding: UTF-8 -*-
import datetime
import os
# import re
import xlrd
import shutil
import utils

from Abstracts import AbstractInstitution
from Checker import *


class HuaChuang(AbstractInstitution):
    folder_institution_map = {
        '华创普通账户': '华创',
        '华创两融账户': '华创两融',
        '华创期权账户': '华创期权',
    }

    # =================================== =================================== #
    normal_flow = {
        'security_code': ['股票代码', '证券代码', ], 'security_name': ['股票名称', '证券名称', ],
        # 'trade_direction': '交易方向',
        'trade_class': ['业务标志', ], 'trade_price': ['成交均价', ],
        'cash_move': ['收付金额', ], 'trade_volume': ['发生数量', ],
        'shareholder_code': ['股东帐号', '股东账号', ],
        'None': [
            '日期', '币种', '佣金', '印花税', '其他费', '资金余额', '备注信息',
        ]
    }
    normal_pos = {
        'shareholder_code': ['股东帐号', ],
        'security_name': ['股票名称'], 'security_code': ['证券代码', '股票代码'],
        'hold_volume': ['当前数'], 'weight_average_cost': ['成本价'],  # 'total_cost': ['参考成本'],
        'close_price': ['最新价'], 'market_value': ['市值'],
        'None': ['可用数', '市值价', '盈亏金额', '币种', '股份表可用数', ],
    }
    normal_acc = {
        'capital_account': ['资产账户', ], 'customer_id': ['客户代码', ],
        # 'market_sum': ['资产市值', ],
        'capital_sum': ['资产总值', ], 'cash_amount': ['资金余额', ],
        'None': ['币种', '可用金额', '可取现金', '资金资产', ],
    }
    normal_product_id_map = {
        '50061487': '创新稳健1号',
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper, TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            HuaChuang.log.debug_running(file_name)
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('txt'):
                assert date.strftime('%Y%m%d') in file_name, file_name
                if file_name.startswith('久铭创新稳健{}'.format(date.strftime('%Y%m%d'))):
                    product_name = '创新稳健1号'
                else:
                    raise NotImplementedError(file_name)
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()

                identified_dict = {
                    'date': date, 'product': product_name,
                    'institution': HuaChuang.folder_institution_map[folder_name],
                    'account_type': folder_name, 'currency': 'RMB', 'offset': OFFSET_OPEN,
                }

                matcher = TextMapper(HuaChuang.normal_flow, identified_dict)
                matcher.map_horizontal(content)
                matcher.ignore_line.update(['合计'])
                try:
                    flow = re.search(r"流水明细([\w\W]+)汇总股票资料", content, re.M).group(1)
                except AttributeError:
                    flow = ''
                flow_list = matcher.map(clear_str_content(flow))
                result_dict[product_name]['flow'] = flow_list

                matcher = TextMapper(HuaChuang.normal_pos, identified_dict)
                matcher.set_duplicated_tolerance(True).set_right_align(True)
                try:
                    pos = re.findall(r"股票资料[^,]+(?=流水明细)", content, re.M)
                    assert len(pos) == 1, 'wrong re implication'
                except AssertionError:
                    pos = re.findall(r"股票资料[^,]+(?=汇总股票)", content, re.M)
                pos_list = matcher.map(clear_str_content(pos[0]))

                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(HuaChuang.normal_acc, identified_dict)
                # matcher.set_duplicated_tolerance(True).set_right_align(True)
                acc = re.search(r"风险等级到期时间:([\w\W]+)[^汇总]+股票资料:", content, re.M).group(1)
                acc_obj = matcher.map(acc)[0]
                if 'market_sum' not in acc_obj:
                    acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            elif file_name.lower().endswith('xls'):
                pro_id = re.match(r'(\d+)', file_name).group(1)
                if pro_id in {'995001193': '创新稳健1号', }:
                    target_folder = folder_path.split(os.path.sep)
                    target_folder.pop(-1)
                    target_folder.append('华创两融账户')
                    target_folder = os.path.sep.join(target_folder)
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(os.path.join(folder_path, file_name), target_folder)
                    continue
                elif pro_id in {'8850061487': '创新稳健1号', }:
                    target_folder = folder_path.split(os.path.sep)
                    target_folder.pop(-1)
                    target_folder.append('华创期权账户')
                    target_folder = os.path.sep.join(target_folder)
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(os.path.join(folder_path, file_name), target_folder)
                    continue
                else:
                    pass
            # elif file_name.lower().endswith('xlsx'):
                assert date.strftime('%Y%m%d') in file_name, file_name
                if file_name.startswith('50061487'.format(date.strftime('%Y%m%d'))):
                    product_name = '创新稳健1号'
                elif file_name.startswith('50062949'.format(date.strftime('%Y%m%d'))):
                    product_name = '专享7号'
                elif file_name.startswith('50062494'.format(date.strftime('%Y%m%d'))):
                    product_name = '专享7号'
                elif file_name.startswith('50074228'.format(date.strftime('%Y%m%d'))):
                    product_name = '专享8号'
                elif file_name.startswith('50063746'.format(date.strftime('%Y%m%d'))):
                    product_name = '专享11号'
                else:
                    raise NotImplementedError(file_name)
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                identified_dict = {
                    'date': date, 'product': product_name,
                    'institution': HuaChuang.folder_institution_map[folder_name],
                    'account_type': folder_name, 'currency': 'RMB', 'offset': OFFSET_OPEN,
                }

                matcher = ExcelMapper(HuaChuang.normal_flow, identified_dict)
                matcher.set_duplicated_tolerance(True)
                matcher.set_start_line('流水明细')
                matcher.set_end_line('证券汇总')
                matcher.ignore_line.update(['合计', ])
                print(content.sheet_by_index(0))
                flow_list = matcher.map(content.sheet_by_index(0))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(HuaChuang.normal_pos, identified_dict)
                # matcher.set_start_line('证券汇总')
                # matcher.set_end_line('流水汇总')
                matcher.set_start_line('证券明细')
                matcher.set_end_line('流水明细')
                matcher.ignore_line.update(['人民币市值', '人民币参考盈亏', ])
                pos_list = matcher.map(content.sheet_by_index(0))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(HuaChuang.normal_acc, identified_dict)
                matcher.set_start_line('资金信息')
                matcher.set_end_line('证券明细')
                acc_obj = matcher.map(content.sheet_by_index(0))[0]
                if 'market_sum' not in acc_obj:
                    acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            elif file_name.lower().endswith('xlt'):
                assert date.strftime('%Y%m%d') in file_name, file_name
                if file_name.startswith('50061487'.format(date.strftime('%Y%m%d'))):
                    product_name = '创新稳健1号'
                else:
                    raise NotImplementedError(file_name)
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
            elif file_name.lower().endswith('rar'):
                os.remove(os.path.join(folder_path, file_name))
                continue
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    margin_pos = {
        'shareholder_code': ['股东账号', '股东帐号'],
        'security_code': ['证券代码', ], 'security_name': ['证券简称', ], 'hold_volume': ['可用数量', ],
        'weight_average_cost': ['成本价', ], 'market_value': ['当前市值', ],
        # 'total_cost': ['参考成本', ],
        'None': ['当前数量', '盈亏', ],
    }
    margin_flow = {
        'trade_class': ['摘要代码', ], 'security_code': ['证券代码', ], 'security_name': ['证券简称', ],
        'trade_volume': ['发生数量', ], 'trade_price': ['成交价格', ], 'cash_move': ['发生金额', ],
        'None': [
            '发生日期', '业务类型', '资金余额', '佣金', '印花税', '过户费', '清算费', '备注',
        ],
    }
    margin_acc = {
        'capital_sum': ['总资产', ], 'market_sum': ['证券市值', ], 'cash_amount': ['资金余额', ],
        'cash_available': ['可取金额', ],
        'liability_principal': ['融资余额', ], 'liability_amount_interest': ['未了结融资利息', ],
        'liability_amount_fee': ['融资费用', ], 'net_asset': ['净资产', ], 'total_liability': ['负债合计', ],
        'liability_amount_for_pay': ['待扣收', ],
        'None': [
            '冻结资金', '保证金可用',
            '交易冻结', '在途资金', '在途可用', '融资保证金',
            '融券市值', '融券费用', '未了结融券利息', '融券保证金', '上一日未了结融资利息', '上一日未了结融券利息',
            '其他负债', '未了结其他负债利息', '转融通成本费用', '期初余额',
        ],
    }
    margin_liability = {
        'contract_date': ['合约日期', ], 'payback_date': ['归还截止日', ],
        'security_code': ['证券代码', ],  'security_name': ['证券名称', ],
        'contract_type': ['合约类型', ], 'contract_amount': ['未了结合约金额', ], 'fee_payable': ['未了结费用', ],
        'contract_volume': ['未了结合约数量', ], 'interest_payable': ['未了结利息', ],
        'liability_amount_for_pay': ['待扣收', ],
        None: [
            '市场', '盈亏金额', '成交价格',
        ]
    }
    margin_id_product_map = {
        '995001193': '创新稳健1号', '995001369': '专享11号',
    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        option_product_id_map = {
            '8850061487': '创新稳健1号',
        }
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            HuaChuang.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xls'):
                #在这里把文件名改成前缀带ID的
                if re.search(r"专享",file_name) != None:
                    os.remove(os.path.join(folder_path,file_name))
                    continue
                assert date.strftime('%Y%m%d') in file_name, file_name
                os.rename(os.path.join(folder_path,file_name),os.path.join(folder_path,"995001193"+file_name))
                if re.search(r"995001193",file_name) == None:
                    file_name = "995001193"+file_name
                pro_id = re.match(r'(\d+)', file_name).group(1)
                if pro_id in option_product_id_map:
                    target_path = folder_path.replace('华创两融', '华创期权')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                print(pro_id)
                product_name = HuaChuang.margin_id_product_map[pro_id]
                # if file_name.startswith('久铭创新稳健融资融券对账单'):
                #     product_name = '创新稳健1号'
                # else:
                #     raise NotImplementedError(file_name)
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                identified_dict = {
                    'product': product_name, 'date': date, 'institution': HuaChuang.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name, 'offset': OFFSET_OPEN,
                }

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(HuaChuang.margin_pos, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                matcher.set_end_line('2负债情况')
                pos_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(HuaChuang.margin_flow, identified_dict)
                matcher.ignore_line.update(['合计', ])
                matcher.set_start_line('三业务流水')
                flow_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(HuaChuang.margin_liability, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                matcher.set_start_line('3融资融券负债明细')
                matcher.set_end_line('三业务流水')
                liability_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(HuaChuang.margin_acc, identified_dict)
                matcher.set_end_line('12证券余额')
                acc_obj_01 = matcher.map(content.sheet_by_name('融资融券对账单'))[0]
                matcher = ExcelMapper(HuaChuang.margin_acc, identified_dict, )
                matcher.set_start_line('2负债情况')
                matcher.set_end_line('三业务流水')
                acc_obj_02 = matcher.map(content.sheet_by_name('融资融券对账单'))[0]
                assert isinstance(acc_obj_01, dict) and isinstance(acc_obj_02, dict)
                acc_obj = acc_obj_01.copy()
                acc_obj.update(acc_obj_02)
                result_dict[product_name]['account'] = acc_obj

                match_margin_pos_acc(pos_list, acc_obj)
                # match_margin_liability_acc(liability_list, acc_obj)
                # confirm_margin_account(acc_obj)
                confirm_margin_flow_list(flow_list)
            elif file_name.lower().endswith('.rar'):
                os.remove(os.path.join(folder_path, file_name))
            elif file_name.lower().endswith('xlsx'):
                pro_id = re.match(r'(\d+)', file_name).group(1)
                if pro_id in HuaChuang.normal_product_id_map:
                    target_path = folder_path.replace('华创两融', '华创普通')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                else:
                    raise NotImplementedError(file_name)
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    option_id_product_map = {
        '8850061487': '创新稳健1号',
    }
    @staticmethod
    def load_option(folder_path: str, date):
        # folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            HuaChuang.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('xls'):
                # continue
                assert date.strftime('%Y%m%d') in file_name, file_name
                some_id = re.match(r'(\d+)', file_name).group(1)
                if some_id in HuaChuang.option_id_product_map:
                    product_name = HuaChuang.option_id_product_map[some_id]
                elif some_id in HuaChuang.normal_product_id_map:
                    target_path = folder_path.replace('华创期权', '华创普通')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                elif some_id in HuaChuang.margin_id_product_map:
                    target_path = folder_path.replace('华创期权', '华创两融')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                else:
                    raise NotImplementedError(file_name)
                assert product_name in PRODUCT_NAME_RANGE, '{} {}'.format(product_name, file_name)
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map
