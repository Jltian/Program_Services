# -*- encoding: UTF-8 -*-
import datetime
import os
# import re
import xlrd
import shutil
import utils

from Abstracts import AbstractInstitution
from Checker import *


class ZhongYinGuoJi(AbstractInstitution):
    folder_institution_map = {
        '中银国际普通账户': '中银国际普通',
        '中银国际两融账户': '中银国际两融',
        '中银国际期权账户': '中银国际期权',
    }

    # =================================== =================================== #
    normal_pos = {
        'security_code': ['证券代码', ], 'security_name': ['股票名称', ],
        'hold_volume': ['当前数', ],   # 'last_hold_volume': ['上日余额', ],
        'close_price': ['市值价', ], 'market_value': ['市值', ],   # 'total_cost': ['买入成本', ],
        'None': ['股东帐号', '最新价', '盈亏金额', '币种', '成本价']
    }
    normal_flow = {
        'product': ['姓名', ], 'capital_account': ['资金帐号', '资金账号'],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['摘要名称', '业务标志'], 'trade_volume': ['成交数量', '发生数'],
        'trade_price': ['成交价格', '价格'], 'total_fee': ['交易费', ],
        'cash_move': ['资金发生数', '发生金额', ],
        'customer_id': ['客户号', ],
        'None': [
            '佣金', '净佣金', '印花税', '过户费', '附加费', '备注', '证券余额', '资金余额', '发生日期', '日期', '银行',
        ]
    }
    normal_acc = {
        'cash_amount': ['资金余额', ], 'capital_sum': ['资产总值', ],
        None: ['币种', ],
    }
    normal_id_product_map = {
        '29202731': '久铭10号',
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper, TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            ZhongYinGuoJi.log.debug_running(folder_name, file_name)
            if file_name.startswith('.') or file_name.startswith('~') or '副本' in file_name:
                continue
            elif file_name.lower().endswith('txt'):
                # 29202731久铭10号2020年3月17号对账单
                some_id, product_name = re.match(r'(\d+)(\D+\d+[号指数]+)', file_name).groups()
                # assert date.strftime('%Y年%m月%d日') in file_name, file_name
                product_name = ZhongYinGuoJi.normal_id_product_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, product_name
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': ZhongYinGuoJi.folder_institution_map[folder_name],
                    'currency': 'RMB', 'offset': OFFSET_OPEN,
                }
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                try:
                    content = open(
                        os.path.join(folder_path, file_name), mode='r', encoding='gb18030'
                    ).read()
                except UnicodeDecodeError:
                    content = open(
                        os.path.join(folder_path, file_name), mode='r', encoding='utf-8'
                    ).read()

                # matcher = TextMapper(ZhongYinGuoJi.normal_flow, identified_dict)
                # matcher.set_duplicated_tolerance(True)
                # flow = re.search(r"对帐期间([\w\W]+)盈亏金额", content, re.M).group(1)
                # flow = flow.replace('日    期', '日期').replace('价    格', '价格')
                # flow_list = matcher.map(clear_str_content(flow))
                flow_list = list()
                ZhongYinGuoJi.log.debug(flow_list)
                result_dict[product_name]['flow'] = flow_list

                matcher = TextMapper(ZhongYinGuoJi.normal_pos, identified_dict)
                # matcher.ignore_line.update(['业务标志', ])
                try:
                    pos = re.findall(r"股票资料[^,]+(?=人民币市值)", content, re.M)
                    assert len(pos) == 1, 'wrong re implication'
                except AssertionError:
                    pos = ['', ]
                # pos_list = matcher.map(clear_str_content(pos[0]))
                pos_list = matcher.map(clear_str_content(pos[0]))
                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(ZhongYinGuoJi.normal_acc, identified_dict)
                try:
                    acc = re.search(r"风险等级到期时间([\w\W]+)日期", content).group(1)
                except AttributeError:
                    acc = content
                ZhongYinGuoJi.log.debug(acc)
                acc_obj = matcher.map(acc)[0]
                if 'market_sum' not in acc_obj:
                    # acc_obj['capital_sum'] = float_check(acc_obj['market_sum']) + float_check(acc_obj['cash_amount'])
                    acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            elif file_name.lower().endswith('xls'):
                some_id, product_name = re.match(r'(\d+)(\D+\d+[号指数]+)', file_name).groups()
                if some_id in ZhongYinGuoJi.margin_id_product_map:
                    target_path = folder_path.replace('中银国际普通账户', '中银国际两融账户')

                elif some_id in ZhongYinGuoJi.option_id_product_map:
                    target_path = folder_path.replace('中银国际普通账户', '中银国际期权账户')
                else:
                    raise NotImplementedError(file_name)
                if not os.path.exists(target_path):
                    os.makedirs(target_path)
                shutil.move(os.path.join(folder_path, file_name), target_path)
                continue
            elif file_name.lower().endswith('zip'):
                os.remove(os.path.join(folder_path,file_name))
                continue
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    margin_pos = {
        # 'product': [''], 'close_price': ['最新价格', ],
        'security_code': ['证券代码', ], 'security_name': ['证券简称', ], 'hold_volume': ['当前数量', ],
        # 'total_cost': ['买入成本', ],
        # 'close_price': ['最新价', ],
        'market_value': ['当前市值', ],
        'None': ['可用数量', '成本价', '盈亏']
    }
    margin_flow = {
        'date': ['发生日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券简称', '证券名称'],
        'trade_class': ['摘要代码', '摘要名称'], 'trade_volume': ['发生数量', ],
        'trade_price': ['成交价格', ], 'cash_move': ['发生金额', '资金发生数'],
        'None': ['业务类型', '佣金', '印花税', '过户费', '清算费', '资金余额', '证券余额', '备注'],
    }
    margin_acc = {
        'capital_account': ['信用资金帐号', ],
        'capital_sum': ['总资产', ], 'cash_amount': ['资金余额', ], 'market_sum': ['证券市值', '担保证券市值'],
        'net_asset': ['净资产', ], 'total_liability': ['负债合计', ],
        'liability_principal': ['融资余额', ], 'liability_amount_interest': ['未了结融资利息', ],
        'liability_amount_fee': ['融资费用', ], 'liability_amount_for_pay': ['待扣收', ],
        'None': [
            '冻结资金', '保证金可用', '可取金额', '融资保证金', '融券市值', '融券费用', '未了结融券利息', '融券保证金',
            '期初余额', '其他负债', '未了结其他负债利息', '转融通成本费用',
        ],
    }
    margin_liability = {
        'contract_date': ['融资日期', '合约日期', ], 'contract_type': ['合约类型', ],
        'contract_volume': ['未了结合约数量', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'security_account': ['证券账户', ],  # 'liability_buy_volume': ['未了结合约数量', ],
        'liability_amount_for_pay': ['应付融资款', '未了结合约金额', ],
        'fee_payable': ['应付融资费用', '未了结费用', ],
        'interest_payable': ['未了结利息', ],
        'payback_date': ['偿还期限', '归还截止日', ],
        None: [
            '市场', '待扣收', '盈亏金额', '合约类型', '保证金比例', '成交价格'
        ]

    }
    margin_id_product_map = {
        '929202731': '久铭10号',
    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict = dict()
        product_file_map = dict()
        for file_name in os.listdir(folder_path):
            ZhongYinGuoJi.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xls'):
                try:
                    some_id, product_name = re.match(r'(\d+)(\D+\d+[号指数]+)', file_name).groups()
                except AttributeError:
                    some_id = re.match(r'(\d+)', file_name).group(1)
                # assert date.strftime('%Y年%m月%d日') in file_name, file_name
                product_name = ZhongYinGuoJi.margin_id_product_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, product_name
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': ZhongYinGuoJi.folder_institution_map[folder_name],
                    'currency': 'RMB', 'offset': OFFSET_OPEN,
                }
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ZhongYinGuoJi.margin_pos, identified_dict, )
                matcher.set_start_line('12证券余额').set_end_line('2负债情况')
                matcher.ignore_line.update(['合计', ])
                pos_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongYinGuoJi.margin_flow, identified_dict)
                matcher.set_start_line('三业务流水')
                matcher.ignore_line.update(['合计', ])
                flow_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhongYinGuoJi.margin_liability, identified_dict, )
                matcher.set_start_line('3融资融券负债明细').set_end_line('三业务流水')
                matcher.ignore_line.update(['合计', ])
                liability_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                for obj in liability_list:
                    obj['contract_amount'] = obj['liability_amount_for_pay']
                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(ZhongYinGuoJi.margin_acc, identified_dict)
                matcher.set_start_line('11当前资产情况').set_end_line('12证券余额')
                acc_obj = matcher.map(content.sheet_by_name('融资融券对账单'))[0]
                matcher = ExcelMapper(ZhongYinGuoJi.margin_acc, identified_dict)
                matcher.set_start_line('2负债情况').set_end_line('3融资融券负债明细')
                acc_obj_compensation = matcher.map(content.sheet_by_name('融资融券对账单'))[0]
                acc_obj.update(acc_obj_compensation)
                acc_obj['cash_available'] = acc_obj['cash_amount']
                # market_sum = 0.0
                # for obj in pos_list:
                #     market_sum += float_check(obj['market_value'])
                # acc_obj['market_sum'] = market_sum
                # acc_obj['liability_amount_interest'] = 0.0   # TODO: 测试阶段没有看到融资利息，强制归零
                # acc_obj['liability_amount_for_pay'] = 0.0
                result_dict[product_name]['account'] = acc_obj

                match_margin_pos_acc(pos_list, acc_obj)
                match_margin_liability_acc(liability_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    option_id_product_map = {
        '829202731': '久铭10号',
        '929202731' : '久铭10号'
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        # from jetend.structures import ExcelMapper
        # from structures import DataList
        # from sheets.raws.RawOption import RawOptionFlow, RawOptionPosition
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xls'):
                try:
                    some_id, product_name = re.match(r'(\d+)(\D+\d+[号指数]+)', file_name).groups()
                except AttributeError:
                    some_id = re.match(r'(\d+)', file_name).group(1)
                product_name = ZhongYinGuoJi.option_id_product_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, product_name

                if product_name not in result_dict:
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
                # identified_dict = {
                #     'product': product_name, 'date': date, 'account_type': folder_name,
                #     'institution': ZhongYinGuoJi.folder_institution_map[folder_name],
                #     'currency': 'RMB', 'offset': OFFSET_OPEN,
                # }
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
                # raise NotImplementedError

            # elif file_name.lower().endswith('pdf'):
            #     pro_id = re.match(r"(\d+)", file_name).group(1)
            #     product_name = id_product_map[pro_id]
            #     if product_name not in result_dict:
            #         result_dict[product_name] = None
            #     product_file_map[product_name] = file_name

            elif file_name.lower().endswith('zip'):
                raise RuntimeError(file_name)
            else:
                raise NotImplementedError(file_name)

            return result_dict, product_file_map
        else:
            raise NotImplementedError(folder_name)
