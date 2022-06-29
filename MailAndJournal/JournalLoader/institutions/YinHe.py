# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import time
import xlrd
import shutil

from Abstracts import AbstractInstitution
from Checker import *
from BatchDecompression import *


class YinHe(AbstractInstitution):
    """银河普通账户"""
    folder_institution_map = {
        '银河普通账户': '银河',
        '银河两融账户': '银河两融',
        '银河期货账户': '银河期货',
    }

    normal_pos = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'hold_volume': ['当前余额'],
        'market_value': ['证券市值', ], 'close_price': ['最新价', ], 'total_cost': ['参考成本', ],
        'None': ['可用数量', '参考盈亏', '参考成本价格', '盈亏金额', '实时余额'],
    }

    normal_flow = {
        'date': ['日期', ], 'trade_class': ['业务标志', ], 'security_code': ['证券代码', ],
        'security_name': ['证券名称', ], 'trade_price': ['价格', ], 'trade_volume': ['发生数', ],
        'cash_move': ['发生金额', ],
        'None': ['银行', '资金余额', '手续费', '印花税', '过户费', '备注'],
    }

    normal_acc = {
        'cash_amount': ['当前余额', ], 'market_sum': ['当前市值', ], 'capital_sum': ['总资产', ],
        'None': ['当前可用', '实时余额', '币种', ],
    }
    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            YinHe.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.endswith('xls') or file_name.endswith(('xlsx')):
                if '信用' in file_name:
                    target_folder = folder_path.replace('银河普通账户', '银河两融账户')
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(os.path.join(folder_path, file_name), target_folder)
                    continue
                if '久铭5' in file_name:
                    product_name = '久铭5号'
                elif '久铭专' in file_name:
                    product_name = '专享9号'
                elif '静康稳健3' in file_name:
                    product_name = '静康稳健3号'
                elif '静久康铭稳健5号' in file_name:
                    product_name = '静久康铭稳健5号'
                elif file_name.startswith('201000040800上海久铭投资'):
                    product_name = '专享16号'
                else:
                    raise NotImplementedError(file_name)
                # date_str = re.match(r'([\d\W]+)流水', file_name).group(1)
                # content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                # content = open(
                #   os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                # ).read()
                # # 处理银河普通账户对账单名称按照打印时间延后的情形
                # Date = datetime.strptime(date_str, '%Y.%m.%d')
                # if date_str == '2019.5.6':
                #     date_before = Date + timedelta(days = -6)
                # elif date_str in ('2019.4.22','2019.5.13','2019.5.20'):
                #     date_before = Date + timedelta(days = -3)
                # elif date_str in ('2019.4.26','2019.5.21','2019.5.22'):
                #     date_before = Date
                # else:
                #     date_before = Date + timedelta(days = -1)
                # 解决读取file_name中date_str为2019.5.27的情况
                # date_new = time.strftime('%Y%m%d', time.strptime(date_str, '%Y.%m.%d'))
                # assert date_new == date.strftime('%Y%m%d'), '{} {}'.format(date_new, date)
                # print(date_str,loader.date_str)
                identified_dict = {
                    'date' : date, 'product': product_name,
                    'institution' : YinHe.folder_institution_map[folder_name],
                    'account_type': folder_name, 'currency': 'RMB', 'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name

                # matcher = TextMapper(YinHe.normal_flow, identified_dict)
                # matcher.set_line_sep('│')
                # matcher.ignore_line.update(['合计'])
                # flow = re.search(r"资产交割([\w\W]*)资产未交割", content, re.M).groups()
                # assert len(flow) == 1, 'wrong re implication'
                # flow_list = matcher.map(flow[0])
                # result_dict[product_name]['fow'] = flow_list
                #
                # matcher = TextMapper(YinHe.normal_pos, identified_dict)
                # matcher.set_line_sep('│')
                # pos = re.search(r"证券资产([\w\W]*)", content, re.M).groups()
                # assert len(pos) == 1, 'wrong re implication'
                # pos_list = matcher.map(pos[0])
                # result_dict[product_name]['position'] = pos_list
                #
                # matcher = TextMapper(YinHe.normal_acc, identified_dict)
                # matcher.set_line_sep('│')
                # acc = re.search(r"资产信息([\w\W]*)│美", content, re.M).groups()
                # print(acc)
                # assert len(pos) == 1, 'wrong re implication'
                # acc_obj = matcher.map(acc[0])[0]
                # result_dict[product_name]['account'] = acc_obj
                #
                # match_normal_pos_acc(pos_list, acc_obj)
                # confirm_normal_flow_list(flow_list)

            elif file_name.endswith('rar'):
                BatchDecompression(folder_path, folder_path, ['盯市']).batchExt()
                #continue
            elif file_name.lower().split('.')[-1] in ('dbf', 'tsv', 'xml', 'c03'):
                os.remove(os.path.join(folder_path, file_name))
            elif file_name.lower().endswith('txt'):
                if file_name.startswith('ipogh') or file_name.startswith('jckz'):
                    os.remove(os.path.join(folder_path, file_name))
                continue

            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map

    margin_pos = {
        # 'product': [''], 'close_price': ['最新价格', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'hold_volume': ['当前余额', ],
        'total_cost': ['买入成本', ], 'close_price': ['最新价', ],
        'market_value': ['证券市值', ],
        'None': ['期初余额', '盈亏金额', ]
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
        'net_asset': ['净资产', ], 'total_liability': ['融资负债合计', ],
        'liability_principal': ['应付融资款', ], 'liability_amount_interest': ['未了结融资利息', ],
        'liability_amount_fee': ['应付融资费用', ], 'liability_amount_for_pay': ['待扣收', ],
        'None': [
            '冻结资金', '保证金可用', '可取金额', '融资保证金', '融券市值', '融券费用', '未了结融券利息', '融券保证金',
        ],
    }
    margin_liability = {
        'contract_date': ['融资日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'security_account': ['证券账户', ], 'liability_buy_volume': ['融资买入数量', ],
        'liability_amount_for_pay': ['应付融资款', ], 'liability_amount_fee': ['应付融资费用', ],
        'payback_date': ['偿还期限', ],
        None: [
            '市场', '待扣收', '盈亏金额', '合约类型', '保证金比例'
        ]

    }
    margin_id_product_map = {
        '201000040800': '专享16号',
    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            YinHe.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.endswith('xls') or file_name.endswith(('xlsx')):
                pro_id, date_str = re.match(r"(\d+)[^\d]+(\d+)", file_name).groups()
                product_name = YinHe.margin_id_product_map[pro_id]
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                assert product_name in PRODUCT_NAME_RANGE, file_name
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
                # identified_dict = {
                #     'product': product_name, 'date': date,
                #     'institution': GuoJun.folder_institution_map[folder_name],
                #     'currency': 'RMB', 'account_type': folder_name,
                #     'offset': OFFSET_OPEN,
                # }
                # content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                #
                # matcher = ExcelMapper(GuoJun.margin_pos, identified_dict, )
                # # matcher.set_start_line('证券余额')
                # matcher.set_end_line('融资负债')
                # # matcher.ignore_line.update(['合计', ])
                # pos_list = matcher.map(content.sheet_by_name('Sheet1'))
                # result_dict[product_name]['position'] = pos_list
                # GuoJun.log.debug('pos_list: \n{}\n{}'.format(pos_list, len(pos_list)) )
                #
                # matcher = ExcelMapper(GuoJun.margin_flow, identified_dict)
                # matcher.set_start_line('资金股份流水').set_end_line('证券余额')
                # flow_list = matcher.map(content.sheet_by_name('Sheet1'))
                # result_dict[product_name]['flow'] = flow_list
                # print(flow_list)
                #
                # matcher = ExcelMapper(GuoJun.margin_liability, identified_dict, )
                # matcher.set_start_line('融资负债').set_end_line('融资负债')
                # liability_list = matcher.map(content.sheet_by_name('Sheet1'))
                # result_dict[product_name]['liabilities'] = liability_list
                #
                # matcher = ExcelMapper(GuoJun.margin_acc, identified_dict)
                # matcher.map_horizontal(content.sheet_by_name('Sheet1'))
                # acc_obj = matcher.form_new()
                # # market_sum = 0.0
                # # for obj in pos_list:
                # #     market_sum += float_check(obj['market_value'])
                # # acc_obj['market_sum'] = market_sum
                # acc_obj['liability_amount_interest'] = 0.0   # TODO: 测试阶段没有看到融资利息，强制归零
                # acc_obj['liability_amount_for_pay'] = 0.0
                # result_dict[product_name]['account'] = acc_obj
                #
                # match_margin_pos_acc(pos_list, acc_obj)
                # match_margin_liability_acc(liability_list, acc_obj)
                # confirm_normal_flow_list(flow_list)

            elif file_name.endswith('rar'):
                BatchDecompression(folder_path, folder_path, ['盯市']).batchExt()
                #continue
            elif file_name.lower().split('.')[-1] in ('dbf', 'tsv'):
                os.remove(os.path.join(folder_path, file_name))

            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map

    # future_flow = {
    #     'security_code': ['合约', ], 'security_name': ['品种', ], 'trade_class': ['买卖', ],
    #     'trade_price': ['成交价', ], 'trade_volume': ['手数', ], 'offset': ['开平', ],
    #     'trade_amount': ['成交额', ], 'trade_fee': ['手续费', ], 'investment_tag': ['投保', ],
    #     None: ['成交日期', '交易所', '权利金收支', ],
    # }
    future_acc = {
        'capital_sum': ['期末结存', ], 'last_capital_sum': ['期初结存', ], 'cash_amount': ['可用资金', ],
        'market_sum': ['总保证金占用', '保证金占用'], 'market_pl': ['持仓盯市盈亏', ], 'out_in_cash': ['出入金', ],
        'trade_fee': ['手续费', ], 'realized_pl': ['平仓盈亏', ],
    }

    # future_pos = {
    #     'security_code': ['合约', ], 'security_name': ['品种', ],
    #     'long_position': ['买持', ], 'short_position': ['卖持', ],
    #     'buy_average_cost': ['买均价', ], 'sell_average_cost': ['卖均价', ],
    #     'prev_settlement': ['昨结算', ], 'settlement_price': ['今结算', ],
    #     'market_pl': ['持仓盯市盈亏', ], 'floating_pl': ['浮动盈亏', ], 'investment_tag': ['投保', ],
    #     'long_mkv': ['多头期权市值', ], 'short_mkv': ['空头期权市值', ], 'margin': ['保证金占用', ],
    #     None: ['交易所', '期权市值', ],
    # }
    future_id_product_map = {
        '699020': '创新稳健2号', '699021': '创新稳健5号','699099': '稳健22号'
    }

    @staticmethod
    def load_future(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        BatchDecompression(folder_path,folder_path,['盯市']).batchExt()
        for file_name in os.listdir(folder_path):
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            # elif file_name.lower().endswith('zip'):
            #     with zipfile.ZipFile(os.path.join(folder_path, file_name), mode='r') as z_file:
            #         for sub_file in z_file.namelist():
            #             assert isinstance(sub_file, str)
            #             if os.path.sep in file_name or '/' in sub_file:
            #                 continue
            #             if sub_file.endswith('.txt'):
            #                 z_file.extract(sub_file, path=folder_path)
            #     os.remove(os.path.join(folder_path, file_name))

            elif file_name.lower().endswith('txt'):
                try:
                    pro_id = re.match(r"(\d+)", file_name).group(1)
                except AttributeError:
                    pro_id = re.match(r"(\d+)客户结算", file_name).group(1)
                product_name = YinHe.future_id_product_map[pro_id]
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': YinHe.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                    'offset': OFFSET_OPEN,
                }
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()

                # matcher = TextMapper(JianXin.future_pos, identified_dict, )
                # matcher.set_line_sep('|')
                # # matcher.set_line_sep(' ')
                # pos = re.search(r"持仓汇总([\w\W]*)共[\s]*\d+条", content, re.M).groups()
                # assert len(pos) == 1, 'wrong re implication'
                # pos_list = matcher.map(pos[0])
                pos_list = list()
                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(YinHe.future_acc, identified_dict, )
                try:
                    acc = re.search(r"资金状况([\w\W]*)注：", content, re.M).groups()
                except AttributeError:
                    acc = re.search(r"资金状况([\w\W]*)客户", content, re.M).groups()
                assert len(acc) == 1, 'wrong re implication'
                acc = acc[0]
                acc = re.sub(r'[a-zA-Z]', '', acc).replace('/', '').replace('(', '').replace(')', '')
                acc = acc.replace('手 续 费', '手续费').replace('出 入 金', '出入金')
                matcher.map_horizontal(acc)
                acc_obj = matcher.form_new()
                result_dict[product_name]['account'] = acc_obj

                # matcher = TextMapper(JianXin.future_flow, identified_dict, )
                # try:
                #     flow = re.search(r"成交记录([\w\W]*)共\d+条[^共条持仓明细]+持仓明细", content, re.M).groups()
                # except AttributeError:
                #     flow = tuple()
                # if len(flow) == 0:
                #     flow_list = list()
                # elif len(flow) == 1:
                #     flow_list = matcher.map(flow[0])
                # else:
                #     raise RuntimeError(flow)
                # result_dict[product_name]['flow'] = flow_list
                flow_list = list()
                result_dict[product_name]['flow'] = flow_list

                match_future_pos_acc(pos_list, acc_obj)
                confirm_future_flow_list(flow_list)

            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map


if __name__ == '__main__':
    print(YinHe.load_normal(r'C:\Users\Administrator\Downloads\test\久铭产品交割单20191023\银河普通账户',
                            datetime.date(2019, 10, 23)))
    # for xls_file in loader.list_dir(loader.__sub_folder__(folder), 'xls'):
    #     loader.log.info_running(folder, xls_file)
    #     product_name = '稳健22号'
    #
    #     date_str = re.match(r'([^\d]+)(\d+)', re.sub(r'\W', '', xls_file)).group(2)
    #     y = int(date_str[:4])
    #     m = int(date_str[4:6])
    #     d = int(date_str[6:])
    #
    #     assert date_str == loader.date_str, '{} {}'.format(date_str, loader.date_str)
    #     identified_dict = {
    #         'product': product_name, 'date': loader.__date__, 'account_type': folder,
    #         'institution': loader.folder_institution_map[folder]['institution'],'currency':'RMB',
    #     }
    #     content = xlrd.open_workbook(loader.__sub_folder__(folder, xls_file))
    #
    #     if datetime.date(y,m,d) <= datetime.date(2019,4,16):  #2019/4/16之后对账单格式发生变化
    #         matcher = ExcelMapper(RawNormalPosition, YinHe.normal_pos, identified_dict)
    #         matcher.ignore_line.update(['合计'])
    #         pos_list = matcher.map(content.sheet_by_name('股份余额汇总'))
    #
    #         matcher = ExcelMapper(RawNormalFlow, YinHe.normal_flow, identified_dict)
    #         matcher.ignore_line.update(['合计'])
    #         flow_list = matcher.map(content.sheet_by_name('资金流水明细'))
    #
    #         matcher = ExcelMapper(RawAccount, YinHe.normal_acc, identified_dict)
    #         matcher.set_start_line('资金情况')
    #         acc_obj = matcher.map(content.sheet_by_name('资金情况'))[0]
    #     else:
    #         pass
