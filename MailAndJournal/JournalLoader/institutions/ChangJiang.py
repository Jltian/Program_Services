# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import xlrd

from Abstracts import AbstractInstitution
from Checker import *
from BatchDecompression import *


class ChangJiang(AbstractInstitution):
    """长江"""
    folder_institution_map = {
        '长江普通账户': '长江',
        '长江两融账户': '长江两融',
        '长江期货账户': '长江期货',
    }

    # =================================== =================================== #
    normal_pos = {
        'shareholder_code': ['股东帐号', '股东账号'], 'security_code': ['证券代码', ], 'security_name': ['股票名称', ],
        'hold_volume': ['当前数', ], 'market_value': ['市值', ], 'close_price': ['最新价', ],
        'weight_average_cost': ['成本价'], 'currency': ['币种', ],
        'None': ['盈亏金额', '市值价','其他费'],
    }
    normal_flow = {
        'shareholder_code': ['股东帐号', '股东账号'],
        'security_code': ['证券代码', '股票代码'], 'security_name': ['股票名称', ],
        'trade_class': ['业务标志', ], 'trade_volume': ['发生数量', ], 'trade_price': ['成交均价', ],
        'cash_move': ['收付金额', ],
        'None': ['日期', '佣金', '印花税', '其他费', '备注信息', '资金余额', '币种', '备注信息']
    }
    normal_acc = {
        'capital_account': ['资金帐号', '资金账号'], 'customer_id': ['客户编号'],
        'capital_sum': ['资产总值', ], 'cash_amount': ['资金余额', ], 'currency': ['币种', ]
    }
    hk_flow = {
        'currency': ['币种', ], 'shareholder_code': ['股东帐号', '股东账号'],
        'security_name': ['股票名称', ], 'trade_class': ['业务标志', ],
        'trade_volume': ['发生数量', ], 'trade_price': ['成交均价', ], 'cash_move': ['收付金额', ],
        'None': ['日期', '佣金', '印花税', '其他费', '资金余额', '备注信息']
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        # 全目录文件扫描
        for file_name in os.listdir(folder_path):
            ChangJiang.log.debug_running(folder_name, file_name)
            if file_name.startswith('.'):
                continue
            elif '副本' in file_name:
                continue
            elif file_name.endswith('txt'):
                try:
                    product_name, date_str = re.match(r"([^\d]+\d*[号指数]+)[^号指数\d]*[ ]*(\d+)", file_name).groups()
                except AttributeError:
                    try:
                        product_name, date_str = re.search(r"([^\d]+\d*[号指数]+)[ ]*(\d+)", file_name).groups()
                    except AttributeError:
                        product_name, date_str = re.search(r"(久铭\d+指数)私募基金(\d+)", file_name).groups()
                # product_name, date_str = re.match(r"([^\d]+\d+[指数]+)(私募基金)?(\d+)", file_name).group(1, 3)
                # product_name_01, product_name_02 = re.match(r"([^\d]+)(\d*[号指数]+)", file_name).groups()
                if re.match(r'久铭稳健\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                assert product_name in PRODUCT_NAME_RANGE, product_name  # 久铭创新稳健5号没加进来

                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                if '长江证券股份有限公司' not in content:
                    content = open(
                        os.path.join(folder_path, file_name), mode='r', encoding='utf-8', errors='ignore'
                    ).read()

                identified_dict = {
                    'date': date, 'product': product_name, 'account_type': folder_name,
                    'institution': ChangJiang.folder_institution_map[folder_name],
                    'offset': OFFSET_OPEN, 'currency': 'RMB'
                }

                # 流水
                matcher = TextMapper(ChangJiang.normal_flow, identified_dict)
                matcher.set_right_align(True)
                matcher.map_horizontal(content)
                matcher.ignore_line.update(['合计'])
                try:
                    flow = re.search(r"流水明细([\w\W]*)未回业务流水明细:", content, re.M).group(1)
                    flow_list = matcher.map(flow)
                    matcher = TextMapper(ChangJiang.hk_flow, identified_dict, )
                    matcher.ignore_line.update(['合计'])
                    flow = re.search(r"未回业务流水明细:([\w\W]*)", content, re.M).group(1)
                    flow_list.extend(matcher.map(flow.replace(':', '-').replace('：', '-')))
                except AttributeError:
                    try:
                        flow = re.findall(r"流水明细[^，]+", content, re.M)
                        flow_list = matcher.map(flow[0])
                    except IndexError:
                        flow_list = matcher.map('')
                for flow in flow_list:
                    if flow['security_name'] == '建设银行':
                        flow['security_code'] = '0939.HK'
                result_dict[product_name]['flow'] = flow_list
                # 持仓
                matcher = TextMapper(ChangJiang.normal_pos, identified_dict)
                matcher.map_horizontal(content)
                pos = re.findall(r"股票资料[^,]+港币市值", content, re.M)
                if len(pos) == 1:
                    pos_list = matcher.map(clear_str_content(pos[0]))
                else:
                    pos_list = matcher.map('')
                result_dict[product_name]['position'] = pos_list

                # 资金
                matcher = TextMapper(ChangJiang.normal_acc, identified_dict)
                matcher.ignore_line.update(['美元', '港币', '港', '美', ])
                matcher.map_horizontal(content)
                matcher.set_duplicated_tolerance(True)
                try:
                    acc = re.search(r"风险等级到期时间([\w\W]+)股票资料:", content, re.M).group(1)
                except AttributeError:
                    try:
                        acc = re.search(r"风险等级到期时间([\w\W]+)[\w\W]+流水明细:", content, re.M).group(1)
                    except AttributeError:
                        try:
                            acc = re.search(r"风险等级到期时间([\w\W]+)", content, re.M).group(1)
                        except AttributeError:
                            raise AttributeError(content)
                acc_obj = matcher.map(acc)[0]
                if 'market_sum' not in acc_obj:
                    acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    margin_pos = {
        # 'product': [''], 'close_price': ['最新价格', ],
        'security_code': ['证券代码', ], 'security_name': ['证券简称', ], 'hold_volume': ['当前数量', ],
        'weight_average_cost': ['成本价', ], 'market_value': ['当前市值', ],
        'None': ['盈亏', '可用数量','其他费' ]
    }
    margin_flow = {
        'date': ['发生日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券简称', ],
        'trade_class': ['摘要代码', ], 'trade_volume': ['发生数量', ],
        'trade_price': ['成交价格', ], 'cash_move': ['发生金额', ],
        'None': ['业务类型', '佣金', '印花税', '过户费', '清算费', '资金余额', '备注', '委托费','其他费'],
    }
    margin_acc = {
        'capital_account': ['信用资金帐号', ],
        'capital_sum': ['总资产', ], 'cash_amount': ['资金余额', ], 'market_sum': ['证券市值', ],
        'net_asset': ['净资产', ], 'total_liability': ['负债合计', ],
        'liability_principal': ['融资余额', ], 'liability_amount_interest': ['未了结融资利息', ],
        'liability_amount_fee': ['融资费用', ], 'liability_amount_for_pay': ['待扣收', ],
        'None': [
            '冻结资金', '保证金可用', '可取金额', '融资保证金', '融券市值', '融券费用', '未了结融券利息', '融券保证金',
            '其他负债', '未了结其他负债利息', '转融通成本费用', '期初余额','其他费'
        ],
    }
    margin_liability = {
        'contract_date': ['合约日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'contract_type': ['合约类型', ], 'contract_volume': ['未了结合约数量', ], 'contract_amount': ['未了结合约金额', ],
        'interest_payable': ['未了结利息', ], 'fee_payable': ['未了结费用', ], 'payback_date': ['归还截止日', ],
        'trade_price': ['成交价格', ],
        None: [
            '市场', '待扣收', '盈亏金额','其他费'
        ]

    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper, TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            ChangJiang.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif '副本' in file_name:
                continue
            elif file_name.lower().endswith('xls'):
                product_name, date_str = re.match(r"([^\d]+\d+[号指数]+)[^\d]*(\d+)", file_name).groups()
                if re.match(r'久铭稳健\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                # if len(product_name) != 4:
                #     assert isinstance(product_name, str)
                #     product_name = product_name.replace('久铭', '')
                # product_name = loader.env.product_name_map[product_name]
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': ChangJiang.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                    'offset': OFFSET_OPEN,
                }
                # 初始化result_dict
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ChangJiang.margin_pos, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                matcher.set_start_line('12证券余额').set_end_line('2负债情况')
                pos_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ChangJiang.margin_flow, identified_dict)
                matcher.ignore_line.update(['合计', ])
                matcher.set_start_line('三业务流水')
                flow_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ChangJiang.margin_liability, identified_dict, )
                matcher.set_start_line('3融资融券负债明细').set_end_line('三业务流水')
                matcher.ignore_line.update(['合计', ])
                liability_list = matcher.map(content.sheet_by_name('融资融券对账单'))
                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(ChangJiang.margin_acc, identified_dict)
                matcher.set_start_line('11当前资产情况').set_end_line('12证券余额')
                matcher.map_horizontal(content.sheet_by_name('融资融券对账单'))
                acc_obj_01 = matcher.map(content.sheet_by_name('融资融券对账单'))[0]
                matcher = ExcelMapper(ChangJiang.margin_acc, identified_dict, )
                matcher.set_start_line('2负债情况').set_end_line('3融资融券负债明细')
                try:
                    acc_obj_02 = matcher.map(content.sheet_by_name('融资融券对账单'))[0]
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
                match_margin_liability_acc(liability_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('txt'):
                continue
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    # cc = {
    #     'currency': ['币种', ], 'customer_id': ['客户号', ], 'market_sum': ['保证金占用', ],
    #     'capital_sum': ['客户权益', ], 'cash_amount': ['可用资金', ],
    # }
    #
    # future_flow = {
    #     'security_name': ['品种', ], 'security_code': ['合约', ],
    #     'trade_class': ['买卖', ], 'trade_price': ['成交价', ], 'trade_volume': ['手数', ],
    #     'trade_amount': ['成交额', ], 'offset': ['开平', ], 'trade_fee': ['手续费', ], 'realize_pl': ['平仓盈亏', ],
    #     'None': ['交易所', '开仓日期',   '投保', '权利金收支', '成交序号', ]
    # }
    #
    future_flow = {
        'security_code': ['合约', ], 'security_name': ['品种', ], 'trade_class': ['买卖', ],
        'trade_price': ['成交价', ], 'trade_volume': ['手数', ], 'offset': ['开平', ],
        'trade_amount': ['成交额', ], 'trade_fee': ['手续费', ], 'investment_tag': ['投保', ],
        'realized_pl': ['平仓盈亏', ],
        None: ['成交日期', '交易所', '权利金收支', ],
    }
    future_acc = {
        'capital_sum': ['当日结存', '期末结存'], 'last_capital_sum': ['上日结存', '期初结存'], 'cash_amount': ['可用资金', ],
        'market_sum': ['总保证金占用', '保证金占用'], 'market_pl': ['持仓盯市盈亏', ], 'out_in_cash': ['出入金', ],
        'trade_fee': ['手续费', ], 'realized_pl': ['平仓盈亏']
    }
    future_pos = {
        'security_code': ['合约', ], 'security_name': ['品种', ],
        'long_position': ['买持', ], 'short_position': ['卖持', ],
        'buy_average_cost': ['买均价', ], 'sell_average_cost': ['卖均价', ],
        'prev_settlement': ['昨结算', ], 'settlement_price': ['今结算', ],
        'market_pl': ['持仓盯市盈亏', ], 'floating_pl': ['浮动盈亏', ], 'investment_tag': ['投保', ],
        'long_mkv': ['多头期权市值', ], 'short_mkv': ['空头期权市值', ], 'margin': ['保证金占用', ],
        None: ['交易所', '期权市值', ],
    }

    @staticmethod
    def load_future(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        id_product_map = {
            '550825': '久铭300指数', '550826': '久铭500指数',
        }
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for fd in os.listdir(folder_path):
            target_file = os.path.join(folder_path, fd)
            if os.path.isfile(target_file) and target_file.endswith('.rar'):
                BatchDecompression(folder_path, folder_path, ['550825.txt', '550826.txt']).batchExt()
                break
        for file_name in os.listdir(folder_path):
            ChangJiang.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('txt'):
                some_id = re.match(r"(\d+)\.txt", file_name).groups()[0]
                product_name = id_product_map[some_id]
                # assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': ChangJiang.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                    'offset': OFFSET_OPEN,
                }
                # 初始化result_dict
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()

                matcher = TextMapper(ChangJiang.future_pos, identified_dict, )
                # matcher.set_line_sep('|')
                matcher.set_line_sep(' ')
                pos = re.search(r"持仓汇总([\w\W]*)共[\s]*\d+条", content, re.M).groups()
                assert len(pos) == 1, 'wrong re implication'
                ChangJiang.log.debug(pos)
                pos_list = matcher.map(pos[0])
                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(ChangJiang.future_acc, identified_dict, )
                try:
                    acc = re.search(r"资金状况([\w\W]*)客户签字", content, re.M).groups()
                except AttributeError:
                    acc = re.search(r"资金状况([\w\W]*) 行权冻结其他费用", content, re.M).groups()
                assert len(acc) == 1, 'wrong re implication'
                acc = acc[0]
                acc = re.sub(r'[a-zA-Z]', '', acc).replace('/', '').replace('(', '').replace(')', '')
                acc = acc.replace('手 续 费', '手续费').replace('出 入 金', '出入金')
                matcher.map_horizontal(acc)
                acc_obj = matcher.form_new()
                result_dict[product_name]['account'] = acc_obj

                matcher = TextMapper(ChangJiang.future_flow, identified_dict, )
                if '平仓明细' in content:
                    try:
                        flow = re.search(r"成交记录([\w\W]*)共\d+条[^共条平仓明细]+平仓明细", content, re.M).groups()
                    except AttributeError:
                        flow = tuple()
                else:
                    try:
                        flow = re.search(r"成交记录([\w\W]*)共\d+条[^共条持明细]+持仓明细", content, re.M).groups()
                    except AttributeError:
                        flow = tuple()
                ChangJiang.log.debug(flow)
                if len(flow) == 0:
                    flow_list = list()
                elif len(flow) == 1:
                    flow_list = matcher.map(flow[0])
                else:
                    raise RuntimeError(flow)
                for flow in flow_list:
                    if not is_valid_float(flow.get('realize_pl', None)):
                        flow['realize_pl'] = 0.0
                    if not is_valid_float(flow.get('cash_move', None)):
                        flow['cash_move'] = 0.0
                result_dict[product_name]['flow'] = flow_list

                match_future_pos_acc(pos_list, acc_obj)
                confirm_future_flow_list(flow_list)

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map


if __name__ == '__main__':
    print(ChangJiang.load_normal(
        r'D:\Documents\久铭产品交割单20190820\长江普通账户',
        datetime.date(2019, 8, 20)
    ))
    # print(ChangJiang.load_margin(
    #     r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190702\长江两融账户',
    #     datetime.date(2019, 7, 2)
    # ))
    # print(ChangJiang.load_future(
    #     r'C:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190701\长江期货账户',
    #     datetime.date(2019, 7, 1)
    # ))
