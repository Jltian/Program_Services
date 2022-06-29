# -*- encoding: UTF-8 -*-
import datetime
import os,rarfile
import re
import shutil
import xlrd

from Abstracts import AbstractInstitution
from Checker import *
from BatchDecompression import *
from plan.utils.MysqlProxy import MysqlProxy
# TODO: 读取出入金
# class ChuRuJin(object):
#     # 期货出入金
#     inout_flow = {
#         'date': ['发生日期', ], 'in_cash': ['入金',], 'out_cash': ['出金',],
#         'None': ['交易所', '出入金类型', '说明'],
#     }
#     def __init__(self, in_cash: float = None, out_cash: float = None):
#         self.in_cash = float_check(in_cash)
#         self.out_cash = float_check(out_cash)
#
#     def check_loaded(self):
#         if not is_valid_float(self.in_cash):
#             return CheckResult(False, '入金信息遗失！')
#         if not is_valid_float(self.out_cash):
#             return CheckResult(False, '出金信息遗失！')
#
#         return CheckResult(True, '')


class GuoJun(AbstractInstitution):
    """国君"""
    folder_institution_map = {
        '国君普通账户': '国君', '国君两融账户': '国君两融',
        '国君期货账户': '国君期货', '国君期权账户': '国君期权',
        '国君客户结算单': '国君期权',
    }

    # =================================== =================================== #
    normal_pos = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'hold_volume': ['当前余额', ], 'last_hold_volume': ['上日余额', ],
        'close_price': ['最新价格', ], 'market_value': ['证券市值', ], 'total_cost': ['买入成本', ],
        'currency' :['币种'],
        'None': ['上日余额', '发生日期', '股份性质']
    }
    normal_flow = {
        'product': ['姓名', ], 'capital_account': ['资金帐号', '资金账号'],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['摘要名称', '业务标志'], 'trade_volume': ['成交数量', '发生数','证券发生数'],
        'trade_price': ['成交价格', '价格'], 'total_fee': ['交易费', ],
        'cash_move': ['资金发生数', '发生金额', ],
        'customer_id': ['客户号', ],
        'None': [
            '佣金', '净佣金', '印花税', '过户费', '附加费', '备注', '证券余额', '资金余额', '发生日期', '日期', '银行',
        ]
    }
    normal_acc = {
        'market_sum': ['当前证券市值', ], 'cash_amount': ['当前资金余额', ]
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper, TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        extract_flag = True
        mp = MysqlProxy('jm_statement')
        for file_name in os.listdir(folder_path):
            GuoJun.log.debug_running(folder_name, file_name)
            if file_name.startswith('.') or file_name.startswith('~') or '副本' in file_name:
                continue
            elif file_name.endswith('xlsx'):
                some_id = re.search(r'(\d+)',file_name.split('_')[-2]).group(0)
                sql = 'SELECT product from account_information WHERE account = %s'
                product_name = mp.get_one(sql,[some_id])['product']
                if '稳健' in product_name or '双盈' in product_name or '稳利' in product_name or '收益' in product_name:
                    product_name = product_name.replace('久铭',"")
                #product_name, some_id = re.match(r'([^\d]+\d*[号指数信用]+)(\d+)', file_name).groups()
                assert product_name in PRODUCT_NAME_RANGE, product_name
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': GuoJun.folder_institution_map[folder_name],
                    'currency': 'RMB', 'offset': OFFSET_OPEN,
                }
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(GuoJun.normal_flow, identified_dict, )
                #matcher.set_end_line('证券市值')
                matcher.set_end_line('股份性质')
                flow_list = matcher.map(content.sheet_by_name('普通对账单'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(GuoJun.normal_pos, identified_dict, )    # 这个ExcelMapper类的设计暂未深究@waves
                matcher.set_start_line('证券余额').set_end_line('人民币当前证券市值')
                #matcher.ignore_line.update(['发生日期', ])
                matcher.ignore_line.update(['日期', ])
                # matcher.set_end_line('姓名上海久铭投资管理有限公司')
                matcher.set_duplicated_tolerance(True)
                pos_list = matcher.map(content.sheet_by_name('普通对账单'))
                # print(pos_list)
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(GuoJun.normal_acc, identified_dict)
                matcher.ignore_line.update(['美元', '港币'])
                matcher.map_horizontal(content.sheet_by_name('普通对账单'))
                acc_obj = matcher.form_new()
                if 'capital_sum' not in acc_obj:
                    acc_obj['capital_sum'] = float_check(acc_obj['market_sum']) + float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj
                # if acc_obj['product'] == '稳健1号' and acc_obj['institution'] == '国君':
                #     continue

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('txt'):
                product_id_name_map = {
                    '10258833': '专享5号', '31090001158699': '静康1号', '31090001158700': '静康全球1号',
                    '31090001158702': '静康稳健1号', '31090001128253': '稳健6号',
                    '31090001158076': '久铭5号','80121599':'专享25号',
                }
                #some_id, product_name, date_str = re.match(r'(\d+)(\D+\d+\D+)(\d+)', '31090001158699静康1号私募证券投资基金20210325.TXT').groups()
                #print(some_id, product_name, date_str,file_name)
                #80121599 久铭专享25号私募20211206.TXT
                some_id, product_name, date_str = re.match(r'(\d+)(\D+\d+\D+)(\d+)', file_name).groups() # 国君普通久铭专享25号没走通 @waves
                product_name = product_id_name_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, product_name
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': GuoJun.folder_institution_map[folder_name],
                    'currency': 'RMB', 'offset': OFFSET_OPEN,
                }
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()

                matcher = TextMapper(GuoJun.normal_flow, identified_dict)
                matcher.set_duplicated_tolerance(True)
                flow = re.search(r"对帐期间([\w\W]+)盈亏金额", content, re.M).group(1)
                flow = flow.replace('日    期', '日期').replace('价    格', '价格')
                flow_list = matcher.map(clear_str_content(flow))
                GuoJun.log.debug(flow_list)
                result_dict[product_name]['flow'] = flow_list

                matcher = TextMapper(GuoJun.normal_pos, identified_dict)
                matcher.ignore_line.update(['业务标志', ])
                # pos = re.findall(r"股票资料[^,]+(?=证券理财资料)", content, re.M)
                # assert len(pos) == 1, 'wrong re implication'
                # pos_list = matcher.map(clear_str_content(pos[0]))
                pos_list = matcher.map(clear_str_content(content))
                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(GuoJun.normal_acc, identified_dict)
                # matcher.set_duplicated_tolerance(True).set_right_align(True)
                matcher.map_horizontal(content)
                acc_obj = matcher.form_new()
                if 'capital_sum' not in acc_obj:
                    acc_obj['capital_sum'] = float_check(acc_obj['market_sum']) + float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('xls'):
                if '信用' in file_name:
                    target_path = folder_path.replace('普通', '两融')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                else:
                    raise NotImplementedError(file_name)

            elif file_name.endswith('zip'):
                raise RuntimeError(file_name)
               # bd = BatchDecompression(folder_path,folder_path,['xlsx'])
               # bd.batchExt()
                # from zipfile import ZipFile
                # with ZipFile(os.path.join(folder_path, file_name), mode='r') as z_file:
                #     for sub_file in z_file.namelist():
                #         if '信用' in sub_file:
                #             assert folder_path.count('普通') == 1, folder_path
                #             target_folder = folder_path.replace('普通', '两融')
                #             if not os.path.exists(target_folder):
                #                 os.makedirs(target_folder)
                #         else:
                #             target_folder = folder_path
                #         z_file.extract(sub_file, path=target_folder)
            elif file_name.lower().endswith('pdf'):
                if '期权' in file_name:
                    target_path = folder_path.replace('普通', '期权')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                else:
                    raise NotImplementedError(file_name)
            elif file_name.lower().endswith('zip') or file_name.lower().endswith('rar'):
                if extract_flag:
                #添加对rar或zip文件的处理@wavezhou
                    BatchDecompression(folder_path,folder_path,['.xlsx']).batchExt()
                extract_flag = False

        return result_dict, product_file_map

    margin_pos = {
        # 'product': [''], 'close_price': ['最新价格', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'hold_volume': ['当前余额', ],
        'total_cost': ['买入成本', ], 'close_price': ['最新价', ],
        'market_value': ['证券市值', ],
        'None': ['期初余额', '盈亏金额', ]
    }
    margin_flow = {
        'date': ['发生日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券简称', '证券名称' ],
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

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict = dict()
        product_file_map = dict()
        mp = MysqlProxy('jm_statement')
        for file_name in os.listdir(folder_path):
            GuoJun.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xls') or file_name.lower().endswith('xlsx'):
                capital_account = re.search(r'(\d+)', file_name.split('_')[-2]).group(0)
                sql = 'SELECT product from account_information WHERE account = %s'
                product_name = mp.get_one(sql, [capital_account])['product']
                #product_name, capital_account = re.match(r"([^\d]+\d*[号]*)信用(\d+)", file_name).groups()
                if re.match(r'久铭稳健\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                # if len(product_name) != 4:
                #     assert isinstance(product_name, str)
                #     product_name = product_name.replace('久铭', '')
                # product_name = loader.env.product_name_map[product_name]
                # assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                assert product_name in PRODUCT_NAME_RANGE, file_name
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
                continue
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

    @staticmethod
    def load_future(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        folder_result_dict, product_file_map = dict(), dict()
        id_product_map = {
            '26200289': '稳健12号', '26200290': '稳健16号', '26200291': '稳利2号', '26200292': '稳健8号',
            '26200293': '久铭3号', '26200295': '久铭2号', '26200296': '双盈1号', '26200297': '稳健2号',
            '26200298': '稳健15号', '26200299': '稳健6号', '26200300': '稳健11号', '26200301': '稳健10号',
            '26200302': '稳健9号', '26200303': '稳健17号', '26200305': '稳健5号', '26200306': '稳健19号',
            '26200307': '稳健3号', '26200308': '稳健7号', '26200310': '稳健18号', '26200338': '稳健21号'
        }



        for file_name in os.listdir(folder_path):
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('txt'):
                GuoJun.log.debug(file_name)
                # 20200310_26200295_交易结算单（Settlement Statement）
                if '交易' in file_name:
                    date_str, pro_id = re.match(r"(\d+)_(\d+)_交易", file_name).groups()
                else:
                    pro_id = re.match(r"(\d+)", file_name).group(1)
                try:
                    product_name = id_product_map[pro_id]
                    if product_name not in folder_result_dict:
                        # folder_result_dict[product_name] = dict()
                        folder_result_dict[product_name] = None
                    product_file_map[product_name] = file_name
                except:
                    os.remove(os.path.join(folder_path, file_name))
                # content = open(
                #     os.path.join(folder_path, file_name), mode='r', encoding='utf-8', errors='ignore'
                # ).read()
                # # GuoJun.log.debug(content)
                # identified_dict = {
                #     'date': date, 'product': product_name,
                #     'institution': GuoJun.folder_institution_map[folder_name],
                #     'currency': 'RMB', 'account_type': folder_name,
                # }
                #
                # matcher = TextMapper(GuoJun.future_acc, identified_dict)
                # matcher.set_line_sep('|')
                # check = re.search(r"资金状况([\w\W]*)货币质押变化金额", content, re.M)
                # if check:
                #     acc = check.group(1)
                # else:
                #     acc = re.search(r"资金状况([\w\W]*)", content, re.M).group(1)
                # acc = acc.replace('手 续 费', '手续费').replace('出 入 金', '出入金')
                # acc = re.sub(r'[a-zA-Z/]', '', acc)
                # matcher.map_horizontal(acc)
                # acc_obj = matcher.form_new()
                # folder_result_dict[product_name]['account'] = acc_obj
                #
                # matcher = TextMapper(GuoJun.future_pos, identified_dict)
                # matcher.set_line_sep('|')
                # matcher.ignore_line.update(['Product'])
                # check = re.search(r"持仓汇总([\w\W]*)共.*\d+.*条[\w\W]+委托人签字", content, re.M)
                # if check:
                #     pos = check.group(1)
                # else:
                #     pos = ''
                # pos_list = matcher.map(pos)
                # folder_result_dict[product_name]['position'] = pos_list
                #
                # matcher = TextMapper(GuoJun.future_flow, identified_dict)
                # matcher.set_line_sep('|')
                # matcher.ignore_line.update(['Product'])
                # check = re.search(r"成交记录([\w\W]*)共.*\d+条[\w\W]*本地强平", content, re.M)
                # if check:
                #     flow = check.group(1)
                # else:
                #     flow = ''
                # flow_list = matcher.map(flow)
                # folder_result_dict[product_name]['flow'] = flow_list
                #
                # confirm_future_flow_list(flow_list)
                # match_future_pos_acc(pos_list, acc_obj)
            elif file_name.lower().endswith('zip'):
                os.remove(os.path.join(folder_path, file_name))
                continue
            else:
                raise NotImplementedError(file_name)

        return folder_result_dict, product_file_map

    # option_acc = {
    #     'capital_account': ['资产账户', ],
    #     'market_sum': ['权利仓市值', ], 'cash_amount': ['期末结存', ],
    #     'currency': ['货币代码', ],
    #     'None': [
    #         '交易日期', '机构名称', '客户代码', '客户名称', '期初结存', '可用资金', '行权资金冻结金额', '行权冻结维持保证金',
    #         '占用保证金', '垫付资金', '预计垫资罚息', '归还垫资', '归还罚息', '减免罚息', '卖券收入', '利息归本',
    #         '利息税', '银衍入金', '银衍出金', '权利金收付', '行权收付', '手续费', '结算费', '经手费', '交易所经手费',
    #         '行权过户费', '行权结算费', '行权手续费', '浮动盈亏', '占用买入额度', '买入额度', '义务仓市值', '保证金风险率',
    #         '应追加保证金', '追保通知内容', '客户确认标志', '客户确认时间', '资金可用金额', '行权锁定保证金', '转入金额', '转出金额'
    #     ],
    # }
    # option_flow = {
    #     'customer_id': ['客户代码', ], 'trade_class': ['证券业务', ], 'offset': ['证券业务行为', ],
    #     'security_code': ['合约编码', ], 'security_name': ['合约简称', ], 'currency': ['货币代码', ],
    #     'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
    #     'cash_move': ['清算金额', ],
    #     'None': ['清算日期', '标的证券代码', '委托价格', '委托数量', '委托金额', '成交笔数', '印花税', '经手费', '证管费',
    #              '交易规费', '清算费', '行权过户费', '净收佣金', ''],
    # }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        # from jetend.structures import ExcelMapper
        # from structures import DataList
        # from sheets.raws.RawOption import RawOptionFlow, RawOptionPosition
        folder_name = folder_path.split(os.path.sep)[-1]
        if folder_name == '国君期权账户':
            result_dict, product_file_map = dict(), dict()
            id_product_map = {
                '8034622': '稳健12号', '8034623': '稳健16号', '8034629': '双盈1号', '8034630': '久铭3号',
                '8034631': '久铭2号', '8034632': '稳健15号', '8034648': '稳健9号', '8034649': '稳健5号',
                '8034651': '稳健10号', '8034652': '稳健11号', '8034666': '稳利2号', '8034670': '稳健3号',
                '8034671': '稳健6号', '8034672': '稳健7号', '8034701': '稳健19号', '8035770': '稳健21号',
                '8034543': '稳健1号', '8034702': '稳健18号','8034624':'稳健2号',
                '31090001128398': '稳健6号',
            }
            for file_name in os.listdir(folder_path):
                if file_name.startswith('.') or file_name.startswith('~'):
                    continue
                elif file_name.lower().endswith('xls'):
                    try:
                        pro_id = re.match(r"客户结算[^\d]+(\d+)", file_name).group(1)
                    except AttributeError:
                        pro_id = re.match(r"(\d+)客户结算", file_name).group(1)
                    product_name = id_product_map[pro_id]
                    if product_name not in result_dict:
                        result_dict[product_name] = dict()
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
                    raise NotImplementedError

                elif file_name.lower().endswith('pdf'):
                    pro_id = re.match(r"(\d+)", file_name).group(1)
                    product_name = id_product_map[pro_id]
                    if product_name not in result_dict:
                        result_dict[product_name] = None
                    product_file_map[product_name] = file_name

                elif file_name.lower().endswith('zip'):
                    # file = os.path.join(folder_path,file_name)
                    # rarfile.RarFile(file).extractall(folder_path)
                    # for f in os.listdir(folder_path):
                    #     if not f.endswith("pdf"):
                    #         os.remove(f)
                    BatchDecompression(folder_path,folder_path,['.pdf']).batchExt()
                    #raise RuntimeError(file_name)
                else:
                    raise NotImplementedError(file_name)

            return result_dict, product_file_map
        else:
            raise NotImplementedError(folder_name)

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
        GuoJun.log.debug_running('读取托管估值表', file_name)
        # 文件名：SJ9814_久铭稳健1号证券投资基金20190831
        product_code, product, date_str = re.search(
            r'([A-Za-z0-9]+)_(\w+)证券[^\d]+(\d+)', file_name
        ).groups()
        date = datetime.datetime.strptime(date_str, '%Y%m%d')
        product_name = PRODUCT_CODE_NAME_MAP[product_code]

        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '国君证券',
        }
        mapper = ExcelMapper(GuoJun.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)


if __name__ == '__main__':
    print(GuoJun.load_margin(
        r'D:\Documents\实习生 - 金融工程\Desktop\读取缓存\久铭产品交割单20200310\国君两融账户',
        datetime.date(2020, 3, 10)
    ))
    # print(GuoJun.load_normal(
    #     r'D:\Documents\久铭产品交割单20190621-sp\久铭产品交割单20190621-sp\国君两融账户',
    #     datetime.date(2019, 6, 21)
    # ))

    # print(GuoJun.load_future(r'C:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190603\国君期货账户', datetime.date(2019, 6, 3)))

# matcher = TextMapper(ChuRuJin, ChuRuJin.inout_flow, identified_dict)
# matcher.set_line_sep('|')
# check = re.search(r"出入金明细([\w\W]*)共.*\d+条[\w\W]*出入金", content, re.M)
# if check:
#     inoutflow = check.group(1)
# else:
#     inoutflow = ''
# inoutflow_list = matcher.map(inoutflow)

# # 检查数据匹配
# loader.future_flow.extend(flow_list)
# loader.future_position.extend(pos_list)
# loader.account_list.append(acc_obj)
# loader.check_flow_pos_match(folder, product_name, flow_list, pos_list)
# loader.check_flow_acc_match(folder, product_name, flow_list, acc_obj)
# loader.check_pos_acc_match(pos_list, acc_obj)


# if __name__ == '__main__':
#     print(GuoJun.load_normal(r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190603\国君普通账户', datetime.date(2019, 6, 3)))
# # 检查数据匹配
# loader.option_flow.extend(flow_list)
# loader.option_position.extend(pos_list)
# loader.account_list.append(acc_obj)
# loader.check_flow_acc_match(folder, product_name, flow_list, acc_obj)
# loader.check_flow_pos_match(folder, product_name, flow_list, pos_list)
# loader.check_pos_acc_match(pos_list, acc_obj)

# for xls_file in loader.list_dir(loader.__sub_folder__(folder), 'xls'):
#     from journal_load.Mapper import ExcelMapper
#     # from journal_load.raws.RawAccount import RawAccount
#     from journal_load.raws.RawOption import RawOptionFlow, RawOptionPosition
#     from journal_load.Loader import JournalLoader
#     assert isinstance(loader, JournalLoader), str(type(loader))
#     loader.log.info_running(folder, xls_file)
#     pro_id = re.match(r"历史交收[^\d]+(\d+)", xls_file).group(1)  # 历史交收明细查询8034671
#     product_name = id_product_map[pro_id]
#     # assert date_str == loader.date_str
#     identified_dict = {
#         'product': product_name, 'date': loader.__date__, 'account_type': folder,
#         'institution': loader.folder_institution_map[folder]['institution'],
#         'warehouse_class': '权利仓',
#     }
#     content = xlrd.open_workbook(loader.__sub_folder__(folder, xls_file))
#
#     matcher = ExcelMapper(RawOptionFlow, GuoJun.option_flow, identified_dict)
#     flow_list = matcher.map(content.sheet_by_name(xls_file.split('.')[0]))
#     loader.option_flow.extend(flow_list)
