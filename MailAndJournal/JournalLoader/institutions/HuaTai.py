# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import xlrd
import shutil

from Abstracts import AbstractInstitution
from Checker import *


class HuaTai(AbstractInstitution):
    """华泰"""
    folder_institution_map = {
        '华泰普通账户': '华泰',
        '华泰两融账户': '华泰两融',
        '华泰期权账户': '华泰期权',
        '华泰互换': '华泰互换',
    }

    # =================================== =================================== #
    normal_pos = {
        'product': ['客户姓名', ], 'cash_account': ['资金帐号', '资金账号'], 'shareholder_code': ['股东帐号', '股东账号'],
        'security_code': ['证券代码', '股票代码', ], 'security_name': ['股票名称', ],
        'hold_volume': ['当前数', ], 'weight_average_cost': ['成本价'],  # 'last_hold_volume': ['上日余额', ],
        'close_price': ['最新价', ], 'market_value': ['市值', '市值总额', ], 'currency': ['币种', ],
        'None': ['市值价', '盈亏金额', ],
    }
    normal_flow = {
        'currency': ['币种', ], 'shareholder_code': ['股东帐号', ],
        'security_code': ['证券代码', '股票代码', ], 'security_name': ['股票名称', ],
        'trade_class': ['业务标志', ], 'trade_volume': ['发生数量', ],
        'trade_price': ['成交均价', ], 'cash_move': ['收付金额', ],
        'customer_id': ['客户号', ],
        'None': ['日期', '佣金', '印花税', '其他费', '资金余额', '备注信息', ]
    }
    hk_flow = {
        'currency': ['币种', ], 'shareholder_code': ['股东帐号', '股东账号', ],
        'security_code': ['证券代码', ], 'security_name': ['股票名称', ], 'trade_class': ['业务标志', ],
        'trade_volume': ['发生数量', ], 'trade_price': ['成交均价', ], 'cash_move': ['收付金额', ],
        'None': ['日期', '佣金', '印花税', '其他费', '资金余额', '备注信息', ]
    }
    normal_acc = {
        'capital_account': ['资金帐号', '资金账号', ],
        'capital_sum': ['资产总值', ], 'cash_amount': ['资金余额', ], 'currency': ['币种', ]
    }
    normal_id_product_map = {
        '666810006045': '全球丰收1号'
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            HuaTai.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif '副本' in file_name:
                continue
            elif file_name.lower().endswith('txt'):
                try:
                    product_name = re.match(r'([^\d]+\d*[号指数]+)(\d+)', file_name).group(1)
                except AttributeError:
                    # 解决华泰文件名字里面经常出现空格的情况，例如20190719
                    try:
                        product_name = re.match(r'([^\d]+\d*[号指数]+)\s(\d+)', file_name).group(1)
                    except AttributeError:
                        product_name = re.match(r'([久铭稳健]+\d+[号指数]+)', file_name).group(1)

                if re.match(r'久铭稳健\d+', product_name):
                    product_name = product_name.replace('久铭', '')
                if re.match(r'久铭全球丰收\d+', product_name):
                    product_name = product_name.replace('久铭', '')

                content = open(
                    os.path.join(folder_path, file_name), mode='r', errors='ignore',  # encoding='gb18030',
                ).read()

                assert product_name in PRODUCT_NAME_RANGE, product_name

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                identified_dict = {
                   'date': date, 'product': product_name,
                   'institution': HuaTai.folder_institution_map[folder_name],
                   'account_type': folder_name, 'offset': OFFSET_OPEN,
                }


                matcher = TextMapper(HuaTai.normal_pos, identified_dict, )
                matcher.map_horizontal(content)
                try:
                    pos = re.search(r"股票资料([\w\W]+)人民币市值[\w\W]+配号信息", content, re.M).group(1)
                except AttributeError:
                    try:
                        pos = re.search(r"股票资料([\w\W]+)", content, re.M).group(1)
                    except AttributeError:
                        pos = ''
                if len(pos) != 0:
                    pos_list = matcher.map(pos)
                else:
                    pos_list = matcher.map('')
                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(HuaTai.normal_flow, identified_dict, )
                matcher.ignore_line.update(['合计'])
                try:
                    flow = re.search(r"流水明细([\w\W]*)未回业务流水明细:", content, re.M).group(1)
                    flow_list = matcher.map(flow)
                    matcher = TextMapper(HuaTai.hk_flow, identified_dict, )
                    flow = re.search(r"未回业务流水明细:([\w\W]*)合计：", content, re.M).group(1)
                    flow_list.extend(matcher.map(flow.replace(':', '-').replace('：', '-')))
                except AttributeError:
                    try:
                        flow = re.search(r"流水明细([\w\W]*)股票资料:", content, re.M).group(1)
                        flow_list = matcher.map(flow)
                    except AttributeError:
                        try:
                            flow = re.search(r"流水明细([\w\W]*)合计", content, re.M).group(1)
                            flow_list = matcher.map(flow)
                        except AttributeError:
                            flow_list = matcher.map('')
                result_dict[product_name]['flow'] = flow_list

                matcher = TextMapper(HuaTai.normal_acc, identified_dict, )
                matcher.map_horizontal(content)
                try:
                    acc = re.search(r"(起始|统计)日期([\w\W]+)^流水明细:\n对帐日期", content, re.M).group(2)
                except AttributeError:
                    try:
                        acc = re.search(r"(起始|统计)日期([\w\W]+)股票资料", content, re.M).group(2)
                    except AttributeError:
                        try:
                            acc = re.search(r"(起始|统计)日期([\w\W]+)", content, re.M).group(2)
                        except AttributeError:
                            acc = ''

                acc_obj = matcher.map(acc)[0]
                if 'market_sum' not in acc_obj:
                    acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj
                # HuaTai.log.debug(acc_obj)

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            elif file_name.lower().endswith('xlsx'):
                # rzrqdzd_960000046721_久铭全球丰收1号_20200923
                account_type, pro_id = re.match(r'(\w+)_(\d+)_[^\d]+', file_name).groups()
                if pro_id in HuaTai.normal_id_product_map:
                    product_name = HuaTai.normal_id_product_map[pro_id]
                elif pro_id in HuaTai.margin_id_product_map:
                    target_path = folder_path.replace('华泰普通账户', '华泰两融账户')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                else:
                    raise NotImplementedError('{} {} {}'.format(account_type, pro_id, file_name))

                assert product_name in PRODUCT_NAME_RANGE, product_name

                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name

                # identified_dict = {
                #    'date': date, 'product': product_name,
                #    'institution': HuaTai.folder_institution_map[folder_name],
                #    'account_type': folder_name, 'offset': OFFSET_OPEN,
                # }
            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map

    margin_pos = {
        'security_code': ['证券代码', ], 'security_name': ['证券简称', ], 'hold_volume': ['当前数量', ],
        'weight_average_cost': ['成本价', ], 'market_value': ['当前市值', ],
        'None': ['盈亏', '可用数量'],
    }
    margin_flow = {
        'date': ['发生日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券简称', ],
        'trade_class': ['摘要代码', ], 'trade_volume': ['发生数量', ],
        'trade_price': ['成交价格', ], 'cash_move': ['发生金额', ],
        'None': ['佣金', '资金余额', '印花税', '过户费', '清算费', '业务类型', ],
    }
    margin_acc = {
        'capital_account': ['信用资金帐号', ],
        'capital_sum': ['总资产', ], 'cash_amount': ['资金余额', ], 'market_sum': ['证券市值', ],
        'net_asset': ['净资产', ], 'total_liability': ['负债合计', ],
        'liability_principal': ['融资余额', ], 'liability_amount_interest': ['未了结融资利息', ],
        'liability_amount_fee': ['融资费用', ], 'liability_amount_for_pay': ['待扣收', ],
        'None': [
            '冻结资金', '保证金可用', '可取金额', '融资保证金', '融券市值', '融券费用', '未了结融券利息', '融券保证金',
            '其他负债', '未了结其他负债利息', '转融通成本费用', '专项融资成本费用', '专项融券成本费用',
        ],
    }
    margin_liability = {
        'contract_date': ['合约日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'contract_type': ['合约类型', ], 'contract_volume': ['未了结合约数量', ], 'contract_amount': ['未了结合约金额', ],
        'interest_payable': ['未了结利息', ], 'fee_payable': ['未了结费用', ], 'payback_date': ['归还截止日', ],
        None: [
            '市场', '待扣收', '盈亏金额', '成交价格',
        ]
    }
    margin_id_product_map = {
        '960000046721': '全球丰收1号'
    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            HuaTai.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif '副本' in file_name:
                continue
            elif file_name.lower().endswith('xls'):
                product_name, date_str = re.match(r"([^\d]+\d*[号指数]*)\d+[^\d]+(\d+)", file_name).groups()
                if re.match(r'久铭稳健\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                if re.match(r'久铭全球丰收\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                # if len(product_name) != 4:
                #     assert isinstance(product_name, str)
                #     product_name = product_name.replace('久铭', '')
                # product_name = loader.env.product_name_map[product_name]
                # assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': HuaTai.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                    'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(HuaTai.margin_pos, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                pos_list = matcher.map(content.sheet_by_name('当前资产'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(HuaTai.margin_flow, identified_dict)
                matcher.ignore_line.update(['合计', ])
                flow_list = matcher.map(content.sheet_by_name('业务流水'))
                # 解决20190712证券买入和证券卖出的交易类型都是证券买卖的情况
                if date_str == '20190715':
                    for flow in flow_list:
                        if flow['security_name'] == '济川药业':
                            flow['trade_class'] = '证券买入'
                        elif flow['security_name'] == '天邦股份':
                            flow['trade_class'] = '证券卖出'

                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(HuaTai.margin_liability, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                liability_list = matcher.map(content.sheet_by_name('负债明细'))
                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(HuaTai.margin_acc, identified_dict)
                acc_obj_01 = matcher.map(content.sheet_by_name('资产负债情况'))[0]
                matcher = ExcelMapper(HuaTai.margin_acc, identified_dict, )
                try:
                    acc_obj_02 = matcher.map(content.sheet_by_name('负债情况'))[0]
                except IndexError as i_e:
                    if len(liability_list) == 0:
                        acc_obj_02 = {
                            'total_liability': 0.0, 'liability_principal': 0.0, 'liability_amount_interest': 0.0,
                            'liability_amount_fee': 0.0,
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

            elif file_name.lower().endswith('xlsx'):
                # rzrqdzd_960000046721_久铭全球丰收1号_20200923
                account_type, pro_id = re.match(r'(\w+)_(\d+)_[^\d]+', file_name).groups()
                if pro_id in HuaTai.margin_id_product_map:
                    product_name = HuaTai.margin_id_product_map[pro_id]
                else:
                    raise NotImplementedError('{} {} {}'.format(account_type, pro_id, file_name))

                assert product_name in PRODUCT_NAME_RANGE, product_name

                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name

                # identified_dict = {
                #    'date': date, 'product': product_name,
                #    'institution': HuaTai.folder_institution_map[folder_name],
                #    'account_type': folder_name, 'offset': OFFSET_OPEN,
                # }
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    # option_pos = {
    #     'security_code': ['期权合约代码', ], 'capital_account': ['期权合约名称', ],
    #     'warehouse_class': ['持仓类别', ], 'warehouse_cost': ['成本价', ],
    #     'settlement_price': ['结算价', ], 'warehouse_volume': ['当前数量', ],
    #     'market_value': ['持仓市值', ],
    #     'None': ['交易类别', '期权类别', '可用数量', ],
    # }
    # option_flow = {
    #     'trade_class': ['交易类别', ], 'security_code': ['期权合约代码', ], 'capital_account': ['期权合约名称', ],
    #     'warehouse_class': ['持仓类别', ], 'offset': ['开平仓方向', ], 'reserve_tag': ['备兑标志', ],
    #     'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
    #     'trade_fee': ['手续费', ],
    #     'None': ['发生日期', '证券代码', '证券名称', '买卖方向', '当前余额'],
    # }
    # option_acc = {
    #     'product': ['客户姓名', ],
    #     'capital_account': ['资产账户', ], 'customer_id': ['客户编号', ],
    #     'market_sum': ['期权市值', ], 'capital_sum': ['总权益', ], 'cash_amount': ['现金资产', ],
    # }
    #
    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xls'):
                # identified_dict = {
                #     'date': date, 'account_type': folder_name, 'currency': 'RMB',
                #     'institution': HuaTai.folder_institution_map[folder_name],
                # }
                # product_name, date_str = re.match(r'(久铭-[^\d]+)[对账单]*(\d*)', file_name).group()
                if file_name.startswith('久铭-期权客户对账单{}'.format(date.strftime('%Y%m%d'))):
                    product_name = '稳健18号'
                elif file_name.startswith('久铭-股票期权客户对账单{}'.format(date.strftime('%Y%m%d'))):
                    product_name = '稳健18号'
                else:
                    raise NotImplementedError(file_name)
                if product_name not in result_dict:
                    result_dict[product_name] = None
                    # result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                # # assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                # content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                #
                # matcher = ExcelMapper(HuaTai.option_acc, identified_dict, )
                # matcher.map_horizontal(content.sheet_by_name('资金情况'))
                # acc_obj = matcher.form_new()
                # product_name = acc_obj[product]
                # identified_dict.update({'product': product_name})
                # if product_name not in result_dict:
                #     result_dict[product_name] = dict()
                # result_dict[product_name]['account'] = acc_obj
                #
                # matcher = ExcelMapper(HuaTai.option_flow, identified_dict)
                # matcher.ignore_line.update(['合计'])
                # flow_list = matcher.map(content.sheet_by_name('对帐单'))
                # result_dict[product_name]['flow'] = flow_list
                #
                # matcher = ExcelMapper(HuaTai.option_pos, identified_dict, )
                # matcher.ignore_line.update(['合计'])
                # pos_list = matcher.map(content.sheet_by_name('合约持仓清单'))
                # result_dict[product_name]['position'] = pos_list
            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map

    swap_product_id_map = {
        '20006': '稳健22号', '20151': '久铭5号', '20153': '久铭10号', '20113': '全球1号', '20152': '稳健9号',
        '20111': '久铭1号', '20114': '稳健7号', '20115': '稳健23号', '20193': '专享5号',
        '20279': '创新稳健6号', '20300': '专享8号', '20297': '创新稳健5号', '20304': '稳健1号',
    }
    swap_position = {
        'trade_currency': ['币种', ], 'trade_market': ['市场', ], 'security_code': ['标的', ],
        'hold_volume': ['数量', ], 'avg_cost': ['成本', ], 'close_price': ['现价', ],
        'market_pl': ['浮动盈亏', ], 'hold_interest': ['券息', ],
        None: ['日期', 'IM', 'MM', 'initial_margin', 'maintain_margin', 'INITIAL_MARGIN', 'MAINTAIN_MARGIN'],
    }
    swap_balance = {
        'trade_currency': ['币种', ], 'trade_market': ['市场', ], 'exchange_rate': ['汇率', ],
        'margin_balance': ['保证金余额', '预付金余额'], 'long_position_principle': ['多头持仓名义本金', ],
        'short_position_principle': ['空头持仓名义本金', ], 'long_market_pl': ['多头浮动盈亏', ],
        'short_market_pl': ['空头浮动盈亏', ], 'long_accumulated_interest_payable': ['多头累计利息', ],
        'short_accumulated_interest_payable': ['空头累计利息', ],
        'balance_interest_receivable': ['保证金累计利息', '预付金累计利息'],
        'accumulated_loan_fee': ['累计借券费','累计券息', ], 'initial_margin': ['期初保证金', ],
        'maintenance_margin': ['维持保证金', ],
        None: [],
    }  # 'net_asset': '资产净值',
    swap_balance_missing = {
        'net_asset': ['资产净值', ],
    }

    @staticmethod
    def load_swap(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        result_dict, product_file_map = dict(), dict()
        # super_folder_path = folder_path.split(os.path.sep)
        # super_folder_path.pop()
        # super_folder_path = os.path.sep.join(super_folder_path)
        folder_name = folder_path.split(os.path.sep)[-1]

        # if not os.path.exists(super_folder_path):
        #     return FileNotFoundError('文件夹不存在')
        result_dict['loaded_date'] = date
        for file_name in os.listdir(folder_path):
            HuaTai.log.debug_running(file_name)
            # 忽略系统文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xlsx'):
                # 读取 excel 对账单
                # 获取产品名称  HTSC_20006_D1S_20200319_久铭稳健22号南向互换
                product_id, date_str = re.match(r'HTSC_(\d+)_\w+_(\d+)_', file_name).groups()
                assert date.strftime('%Y%m%d') == date_str, '{} {}'.format(date, date_str)
                product = HuaTai.swap_product_id_map[product_id]
                if product not in result_dict:
                    result_dict[product] = dict()
                product_file_map[product] = file_name

                xls_file = xlrd.open_workbook(os.path.join(folder_path, file_name))
                hand_dict = {
                    'product': product, 'date': date, 'institution': HuaTai.folder_institution_map[folder_name],
                    'account_type': folder_name, 'customer_id': product_id,
                }
                assert product in PRODUCT_NAME_RANGE, product

                mapper = ExcelMapper(HuaTai.swap_position, hand_dict, None)
                # underlying_list = list()
                # for underlying in mapper.map(xls_file.sheet_by_name('Underlying')):
                #     if len(underlying.get('offset', '')) == 0:
                #         if float_check(underlying.get('hold_volume', 0.0)) < 0.01:
                #             underlying['offset'] = OFFSET_OPEN
                #         else:
                #             raise NotImplementedError(underlying)
                #     if abs(float_check(underlying['hold_volume'])) < 0.02:
                #         pass
                #     else:
                #         underlying_list.append(underlying)
                underlying_list = mapper.map(xls_file.sheet_by_name('汇总持仓'))

                mapper = ExcelMapper(HuaTai.swap_balance_missing, hand_dict, {'估值日期', '客户编号', })
                mapper.map_horizontal(xls_file.sheet_by_name('估值表'), force_map=True)
                missing_info = mapper.form_new()
                HuaTai.log.debug(missing_info)

                mapper = ExcelMapper(HuaTai.swap_balance, hand_dict, None)
                account_list = mapper.map(xls_file.sheet_by_name('估值表'))
                for obj in account_list:
                    obj['net_asset'] = missing_info['net_asset']
                    obj['maintenance_margin'] = 0.0

                result_dict[product] = {
                    'account_list': account_list,
                    'underlying_list': underlying_list,
                }
            elif file_name.lower().endswith('pdf'):
                # pro_id, product = None, None
                # for tag in ZhongXin.swap_product_id_map.keys():
                #     if tag in file_name:
                #         pro_id = tag
                #         product = ZhongXin.swap_product_id_map[pro_id]
                continue

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    valuation_line = {
        'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['币种', ],
        'exchange_rate': ['汇率', ], 'hold_volume': ['数量', ], 'average_cost': ['单位成本', ],
        'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价'],
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
        HuaTai.log.debug_running('读取托管估值表', file_name)
        # 文件名：SX9408_久铭9号私募证券投资基金_产品估值表_日报_20190831
        product_code, product_name, date_str = re.search(
            r'([A-Za-z0-9]+)_(\w+)私募证券投资基金_产品估值表_日报_(\d+)', file_name.replace(' ', '')
        ).groups()
        product_name = PRODUCT_CODE_NAME_MAP[product_code]

        date = datetime.datetime.strptime(date_str, '%Y%m%d')

        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '华泰证券',
        }
        mapper = ExcelMapper(HuaTai.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)


if __name__ == '__main__':
    print(HuaTai.load_normal(
        r'D:\Documents\久铭产品交割单20190823\华泰普通账户',
        datetime.date(2019, 8, 23)
    ))
    # print(HuaTai.load_margin(
    #     r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190715\华泰两融账户',
    #     datetime.date(2019, 7, 15)
    #  ))
    # loaded_result = HuaTai.load_normal(
    #     r'C:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190625\华泰普通账户',
    #     datetime.date(2019, 6, 25)
    # )
    # for product, sub_loaded in loaded_result.items():
    #     print('='*50)
    #     print(product)
    #     print('position', sub_loaded['position'])
    #     print('flow', sub_loaded['flow'])
    #     print('account', sub_loaded['account'])
