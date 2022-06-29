import datetime
import os
import re
import shutil
import xlrd

from Abstracts import AbstractInstitution
from Checker import *


class DeBang(AbstractInstitution):
    """德邦"""
    folder_institution_map = {
        '德邦普通账户': '德邦',
        '德邦两融账户': '德邦两融'
    }

    # =================================== =================================== #
    normal_pos = {
        'security_name': ['股票名称', ], 'security_code': ['股票代码', '证券代码'], 'shareholder_code': ['股东帐号', ],
        'hold_volume': ['当前数', ], 'market_value': ['市值', ],
        'currency': ['币种', ], 'close_price': ['最新价', ],
        'weight_average_cost': ['成本价'],
        'None': ['盈亏金额', '市值价', '股份表可用数', '可用数', ],
    }
    normal_flow = {
        'security_name': ['股票名称', ], 'security_code': ['股票代码', ], 'shareholder_code': ['股东帐号', ],
        'trade_class': ['业务标志', ], 'trade_volume': ['发生数量', ], 'trade_price': ['成交均价', ],
        'cash_move': ['收付金额', ],
        'None': ['日期', '佣金', '印花税', '其他费', '资金余额', '币种', '备注信息', ]
    }
    normal_acc = {
        'capital_account': ['资金帐号', ], 'customer_id': ['客户编号'],
        'capital_sum': ['资产总值', ], 'cash_amount': ['资金余额', ], 'currency': ['币种', ],
        'None': ['可用资金', '港股可用', ]
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper, TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        product_id_name_map = {
            '02110000335780': '创新稳健5号',
        }

        # 全目录文件扫描
        for file_name in os.listdir(folder_path):
            DeBang.log.debug_running(folder_name, file_name)
            if file_name.startswith('.'):
                continue
            elif '副本' in file_name:
                continue
            elif file_name.endswith('txt'):
                try:
                    product_name, date_str = re.match(r"([^\d]+\d+[号指数]+)私募基金(\d+)对账单", file_name).groups()
                except AttributeError:
                    try:
                        product_name, date_str = re.search(r'([^\d]+\d+[号指数]+)[^\d]*(\d+)', file_name).groups()

                    except AttributeError:
                        #try:
                        product_name, date_str = re.search(r'([^\d]+\d+[号指数]+)\s(\d+)', file_name).groups()
                        #except AttributeError:
                            #product_name, date_str = re.search(r'([^\d]+\d+[号指数]+)[^\d]+', file_name).groups()  # waves

                if product_name[:4] in ('久铭稳健', '久铭创新', '久铭专享'):
                    product_name = product_name.replace('久铭', '')
                assert product_name in PRODUCT_NAME_RANGE, product_name

                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()

                identified_dict = {
                    'date': date, 'product': product_name, 'account_type': folder_name,
                    'institution': DeBang.folder_institution_map[folder_name],
                    'offset': OFFSET_OPEN, 'currency': 'RMB'
                }
                # 流水
                matcher = TextMapper(DeBang.normal_flow, identified_dict)
                matcher.map_horizontal(content)
                matcher.set_duplicated_tolerance(True)
                matcher.ignore_line.update(['合计', '对帐日期', ])
                try:
                    flow = re.search(r"流水汇总:([\w\W]+)汇总股票资料", content, re.M).groups()
                except AttributeError:
                    try:
                        flow = re.search(r"流水明细:([\w\W]+)股票资料", content, re.M).groups()
                    except AttributeError:
                        try:
                            flow = re.search(r"流水明细:([\w\W]+)", content, re.M).groups()
                        except AttributeError:
                            flow = ''

                if len(flow) == 1:
                    DeBang.log.debug(flow[0])
                    flow_list = matcher.map(clear_str_content(flow[0]))
                else:
                    flow_list = matcher.map('')
                # 解决20190726 稳健23号流水里面无证券代码的情况
                if date in (datetime.date(2019, 7, 26), datetime.date(2019, 8, 14), datetime.date(2019, 8, 20)):
                    for flow in flow_list:
                        if flow['security_name'] == '建设银行':
                            flow['security_code'] = '601939.SH'
                        else:
                            pass
                # 解决20190806创新稳健5号流水里面无证券代码的情况
                if date == datetime.date(2020, 8, 6):
                    for flow in flow_list:
                        if flow['security_name'] == '葫芦娃':
                            flow['security_code'] = '605199.SH'
                        else:
                            pass
                result_dict[product_name]['flow'] = flow_list

                # 持仓
                matcher = TextMapper(DeBang.normal_pos, identified_dict)
                # matcher.map_horizontal(content)
                matcher.set_duplicated_tolerance(True)
                try:
                    pos = re.search(r"汇总股票资料([\w\W]+)人民币市值", content, re.M).groups()
                except AttributeError:
                    try:
                        pos = re.search(r"股票资料:([\w\W]+)人民币市值", content, re.M).groups()
                    except AttributeError:
                        pos = ''
                if len(pos) == 1:
                    pos_list = matcher.map(clear_str_content(pos[0]))
                else:
                    pos_list = matcher.map('')
                result_dict[product_name]['position'] = pos_list

                # 资金
                matcher = TextMapper(DeBang.normal_acc, identified_dict)
                matcher.ignore_line.update(['美元', '港币', '港', '美', ])
                matcher.map_horizontal(content)
                matcher.ignore_line.update(['证件类型'])
                try:
                    acc = re.search(r"(币种[\w\W]+)流水", content, re.M).group(1)
                except AttributeError:
                    try:
                        acc = re.search(r"(币种[\w\W]+)股票资料", content, re.M).group(1)
                    except AttributeError:
                        try:
                            acc = re.search(r"(币种[\w\W]+)[^未回业务]+流水", content, re.M).group(1)
                        except AttributeError:
                            acc = content
                acc_obj = matcher.map(acc)[0]
                if 'market_sum' not in acc_obj:
                    acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(
                        acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('xls'):
                margin_code_name_map = {
                    '02110000335780': '创新稳健5号',
                }
                pro_id = re.match(r'(\d+)', file_name).group(1)
                if pro_id in margin_code_name_map:
                    target_path = folder_path.replace('德邦普通', '德邦两融')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                else:
                    raise NotImplementedError(file_name)
            #     product_name = product_id_name_map[pro_id]
            #     assert date.strftime('%Y%m%d') in file_name, file_name
            #     # assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
            #     identified_dict = {
            #         'product': product_name, 'date': date,
            #         'institution': DeBang.folder_institution_map[folder_name],
            #         'account_type': folder_name, 'currency': 'RMB', 'offset': OFFSET_OPEN,
            #     }
            #     assert product_name in PRODUCT_NAME_RANGE, product_name
            #     if product_name not in result_dict:
            #         result_dict[product_name] = dict()
            #
            #     content = xlrd.open_workbook(os.path.join(folder_path, file_name))
            #     matcher = ExcelMapper(DeBang.normal_flow, identified_dict, )
            #     try:
            #         matcher.set_start_line('三业务流水合并对账单')
            #         matcher.ignore_line.update(['合计'])
            #         flow_list = matcher.map(content.sheet_by_name('融资融券对账单'))
            #     except RuntimeError:
            #         flow_list = []
            #     result_dict[product_name]['fow'] = flow_list
            #
            #     try:
            #         matcher = ExcelMapper(DeBang.normal_pos, identified_dict, )
            #         matcher.set_start_line('股票资料').set_end_line('流水明细')
            #         pos_list = matcher.map(content.sheet_by_name('融资融券对账单'))
            #     except RuntimeWarning:
            #         matcher = ExcelMapper(DeBang.normal_pos, identified_dict, )
            #         matcher.set_start_line('股票资料').set_end_line('股票汇总资料')
            #         pos_list = matcher.map(content.sheet_by_name('融资融券对账单'))
            #     result_dict[product_name]['position'] = pos_list
            #
            #     matcher = ExcelMapper(DeBang.normal_acc, identified_dict, )
            #     matcher.set_start_line('风险等级到期时间').set_end_line('股票资料')
            #     acc_obj = matcher.map(content.sheet_by_name('融资融券对账单'))[0]
            #     if 'market_sum' not in acc_obj:
            #         acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(acc_obj['cash_amount'])
            #     result_dict[product_name]['account'] = acc_obj
            #
            #     match_normal_pos_acc(pos_list, acc_obj)
            #     confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('rar'):
                os.remove(os.path.join(folder_path, file_name))

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

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
        'None': ['业务类型', '佣金', '印花税', '过户费', '清算费', '资金余额', '备注'],
    }
    margin_acc = {
        'capital_account': ['信用资金帐号', ],
        'capital_sum': ['总资产', ], 'cash_amount': ['资金余额', ], 'market_sum': ['证券市值', ],
        'net_asset': ['净资产', ], 'total_liability': ['负债合计', ],
        'liability_principal': ['融资余额', ], 'liability_amount_interest': ['未了结融资利息', ],
        'liability_amount_fee': ['融资费用', ], 'liability_amount_for_pay': ['待扣收', ],
        'None': [
            '冻结资金', '保证金可用', '可取金额', '融资保证金', '融券市值', '融券费用', '未了结融券利息', '融券保证金',
            '其他负债', '未了结其他负债利息', '转融通成本费用', '期初余额',
        ],
    }
    margin_liability = {
        'contract_date': ['合约日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'contract_type': ['合约类型', ], 'contract_volume': ['未了结合约数量', ], 'contract_amount': ['未了结合约金额', ],
        'interest_payable': ['未了结利息', ], 'fee_payable': ['未了结费用', ], 'payback_date': ['归还截止日', ],
        'trade_price': ['成交价格', ],
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
            DeBang.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif '副本' in file_name:
                continue
            elif file_name.lower().endswith('xls'):
                try:
                    product_name, date_str = re.match(r"([^\d]+\d*[号指数]+)[^\d]*(\d+)", file_name).groups()
                except AttributeError:
                    product_name, date_str = re.match(r"\d+([^\d]+\d*[号指数]+)[^\d]*(\d+)", file_name).groups()
                if re.match(r'久铭创新\w*\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                # if len(product_name) != 4:
                #     assert isinstance(product_name, str)
                #     product_name = product_name.replace('久铭', '')
                # product_name = loader.env.product_name_map[product_name]
                # assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': DeBang.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                    'offset': OFFSET_OPEN,
                }
                # 初始化result_dict
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(DeBang.margin_pos, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                matcher.set_start_line('12证券余额').set_end_line('2负债情况')
                pos_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                # pos_list = matcher.map(content.sheet_by_name('当前资产'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(DeBang.margin_flow, identified_dict)
                matcher.ignore_line.update(['合计', ])
                matcher.set_start_line('三业务流水')
                flow_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                # flow_list = matcher.map(content.sheet_by_name('业务流水'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(DeBang.margin_liability, identified_dict, )
                matcher.set_start_line('3融资融券负债明细').set_end_line('三业务流水')
                matcher.ignore_line.update(['合计', ])
                liability_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                # liability_list = matcher.map(content.sheet_by_name('负债明细'))
                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(DeBang.margin_acc, identified_dict)
                matcher.set_start_line('11当前资产情况').set_end_line('12证券余额')
                # matcher.map_horizontal(content.sheet_by_name('资产负债情况'))
                # matcher.map_horizontal(content.sheet_by_name('融资融券对账单'))
                acc_obj_01 = matcher.map(content.sheet_by_name('融资融券对账单'))[0]
                # acc_obj_01 = matcher.map(content.sheet_by_name('资产负债情况'))[0]
                matcher = ExcelMapper(DeBang.margin_acc, identified_dict, )
                matcher.set_start_line('2负债情况').set_end_line('3融资融券负债明细')
                try:
                    acc_obj_02 = matcher.map(content.sheet_by_name('融资融券对账单'))[0]
                    # acc_obj_02 = matcher.map(content.sheet_by_name('负债情况'))[0]
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
            elif file_name.lower().endswith('txt'):
                continue
            else:
                raise NotImplementedError(file_name)

            return result_dict, product_file_map


if __name__ == '__main__':
    print(DeBang.load_margin(
        r'D:\Documents\久铭产品交割单20190816\德邦两融账户',
        datetime.date(2019, 8, 16)
    ))
