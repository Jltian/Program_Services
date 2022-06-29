# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import xlrd
import shutil
import zipfile

# from unrar import rarfile

from Abstracts import AbstractInstitution
from Checker import *


class ZhongJinCaiFu(AbstractInstitution):
    """中金财富"""
    folder_institution_map = {
        '中金财富普通账户': '中金财富普通',
        '中金财富两融账户': '中金财富两融',
        '中金财富期权账户': '中金财富期权',
    }
    normal_pos = {
        'shareholder_code': ['股东帐号', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'hold_volume': ['股份余额', ], 'weight_average_cost': ['参考成本价', ], 'close_price': ['参考市价', ],
        'market_value': ['参考市值', ],
        # 'cash_account': ['资金帐号', ], 'currency': ['币种', ],
        'None': ['股份可用', '交易冻结', '参考盈亏', ],
    }
    normal_flow = {
        'trade_class': ['摘要', ], 'shareholder_code': ['股东帐号', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'capital_account': ['资金帐号', ], 'currency': ['成交币种', ],
        'trade_volume': ['成交股数', ], 'trade_price': ['成交价格', ],  # 'trade_amount': ['成交金额', ],
        'cash_move': ['发生金额', ],
        'None': ['发生日期', '港股汇率', '发生币种', '资金余额', '所得税', '净手续费', '经手证管费', '印花税', '过户费']
    }
    normal_acc = {
        'capital_account': ['资产账户', ], 'currency': ['币种', ],
        'cash_amount': ['资金余额', ], 'cash_available': ['可用余额', ],
        'market_sum': ['资产市值', ], 'capital_sum': ['总资产', ],
        'None': ['客户代码', '客户姓名', '港股通资金可用'],
    }
    hk_pos = {
        'cash_account': ['资金帐号', ], 'shareholder_code': ['证券账号', ], 'security_code': ['证券代码', ],
        'security_name': ['证券名称', ], 'hold_volume': ['证券余额', ], 'weight_average_cost': ['参考成本'],
        'close_price': ['收盘价', ], 'market_value': ['参考市值', ], 'currency': ['币种', ],
        'None': ['日期', '客户姓名', '交易市场', '可用数量', '未回买入数量', '未回卖出数量', ]
    }
    normal_id_product_map = {
        '12928637': '全球丰收1号',
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            ZhongJinCaiFu.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or '副本' in file_name:
                continue
            # elif file_name.lower().endswith('pdf'):
            #     continue
            elif file_name.lower().endswith('xls'):
                some_id = re.match(r'(\d+)', file_name).group(1)
                product_name = ZhongJinCaiFu.normal_id_product_map[some_id]
                assert date.strftime('%Y%m%d') in file_name, '{} {}'.format(date, file_name)
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': ZhongJinCaiFu.folder_institution_map[folder_name],
                    'offset': OFFSET_OPEN, 'currency': 'RMB',
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                # 初始化result_dict
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ZhongJinCaiFu.normal_flow, identified_dict, )
                flow_list = matcher.map(content.sheet_by_name('对帐单'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhongJinCaiFu.normal_pos, identified_dict, )
                pos_list = matcher.map(content.sheet_by_name('持仓清单'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongJinCaiFu.normal_acc, identified_dict, )
                acc_obj = matcher.map(content.sheet_by_name('资金情况'))[0]
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            # elif file_name.lower().endswith('rar'):
            #     if '交易数据' in file_name:
            #         os.remove(os.path.join(folder_path, file_name))
            #     elif '对账单' in file_name:
            #         pass
            #     else:
            #         raise NotImplementedError
            # elif file_name.lower().endswith('dbf'):
            #     os.remove(os.path.join(folder_path, file_name))
            #     continue
            #
            # elif file_name.lower().endswith('xlsx'):
            #     continue

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    margin_pos = {
        'shareholder_code': ['股东帐号', ],
        # 'product': [''], 'close_price': ['最新价格', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'hold_volume': ['股份余额', ],
        'weight_average_cost': ['参考成本价', ], 'market_value': ['参考市值', ],  # 'close_price': ['收盘价'],
        'total_cost': ['参考成本', ],
        'None': ['股份可用', '交易冻结', '参考盈亏',]
    }
    margin_flow = {
        'trade_class': ['摘要代码', ],
        'security_code': ['证券代码', ], 'security_name': ['证券简称', ],
        # 'shareholder_code': ['股东代码', ],
        'trade_volume': ['数量', ], 'trade_price': ['成交价格', ],
        'cash_move': ['发生金额', ],  # 'trade_amount': ['成交金额', ],
        'None': ['发生日期', '业务类型', '资金余额', '手续费', '印花税', '过户费', '其他费', '备注信息', ],
    }
    margin_acc = {
        'capital_account': ['资金帐号', ], 'cash_available': ['资金可用', ],
        'cash_amount': ['资金余额', ], 'capital_sum': ['资产总值', ], 'market_sum': ['证券市值', ],
        'total_liability': ['负债合计', ], 'liability_principal': ['融资余额', ],
        'liability_amount_interest': ['未了结融资利息', ], 'liability_amount_for_pay': ['已结未付融资利息', ],
        'liability_amount_fee': ['融资费用', ],
        None: [
            '异常冻结', '交易冻结', '在途资金', '在途可用', '货币代码', '融资保证金', '融券市值', '融券费用', '净资产',
            '上一日未了结融资利息', '未了结融券利息', '上一日未了结融券利息', '融券保证金',
        ]
    }
    margin_liability = {
        'contract_date': ['合约日期', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'contract_type': ['合约类型', ], 'contract_volume': ['合约数量', ], 'contract_amount': ['合约金额', ],
        'interest_payable': ['剩余利息', ], 'payback_date': ['合约到期日', ],
        'fee_payable': ['合约费用', ],
        None: [
            '市场', '合约序号', '已偿还金额', '剩余金额', '已偿还数量', '剩余数量', '委托价格', '委托数量', '委托金额'
        ]
    }
    margin_id_product_map = {
        '12988681': '全球丰收1号',
    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            ZhongJinCaiFu.log.debug(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().split('.')[-1] in ('xls', 'xlsx'):
                some_id = re.match(r'(\d+)', file_name).group(1)
                product_name = ZhongJinCaiFu.margin_id_product_map[some_id]
                assert date.strftime('%Y%m%d') in file_name, '{} {}'.format(date, file_name)
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': ZhongJinCaiFu.folder_institution_map[folder_name],
                    'offset': OFFSET_OPEN, 'currency': 'RMB',
                }
                content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                matcher = ExcelMapper(ZhongJinCaiFu.margin_flow, identified_dict, )
                matcher.ignore_line.update(['合计'])
                flow_list = matcher.map(content.sheet_by_name('业务流水'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhongJinCaiFu.margin_pos, identified_dict, )
                matcher.ignore_line.update(['合计'])
                pos_list = matcher.map(content.sheet_by_name('当前资产'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongJinCaiFu.margin_liability, identified_dict, )
                matcher.ignore_line.update(['合计'])
                liability_list = matcher.map(content.sheet_by_name('负债明细'))
                # for obj in liability_list:
                #     obj['fee_payable'] = 0.0
                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(ZhongJinCaiFu.margin_acc, identified_dict)
                matcher.ignore_line.update(['合计'])
                acc_obj = matcher.map(content.sheet_by_name('资产负债情况'))[0]
                matcher = ExcelMapper(ZhongJinCaiFu.margin_acc, identified_dict)
                matcher.ignore_line.update(['合计'])
                acc_obj_part = matcher.map(content.sheet_by_name('负债情况'))[0]
                acc_obj_part['liability_amount_for_pay'] = 0.0
                acc_obj.update(acc_obj_part)
                result_dict[product_name]['account'] = acc_obj

                match_margin_pos_acc(pos_list, acc_obj)
                match_margin_liability_acc(liability_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map

    option_acc = {
        'capital_account': ['资产账户', ],
        'market_sum': ['权利仓市值', ], 'cash_amount': ['资金可用金额', ], 'capital_sum': ['期末结存', ],
        'None': [
            '交易日期', '机构名称', '客户代码', '客户名称', '期初结存', '可用资金', '行权资金冻结金额', '行权冻结维持保证金',
            '占用保证金', '垫付资金', '预计垫资罚息', '归还垫资', '归还罚息', '减免罚息', '卖券收入', '利息归本',
            '利息税', '银衍入金', '银衍出金', '权利金收付', '行权收付', '手续费', '结算费', '经手费', '交易所经手费',
            '行权过户费', '行权结算费', '行权手续费', '浮动盈亏', '占用买入额度', '买入额度', '义务仓市值', '保证金风险率',
            '应追加保证金', '追保通知内容', '客户确认标志', '客户确认时间', '行权锁定保证金', '转入金额', '转出金额',
            '货币代码',
        ],
    }
    option_id_product_map = {
        '12985075': '全球丰收1号',
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        # from structures import DataList
        # from sheets.raws.RawOption import RawOptionFlow, RawOptionPosition
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xls'):
                some_id = re.match(r'(\d+)', file_name).group(1)
                product_name = ZhongJinCaiFu.option_id_product_map[some_id]
                assert date.strftime('%Y%m%d') in file_name, '{} {}'.format(date, file_name)
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_path, 'currency': 'RMB',
                    'institution': ZhongJinCaiFu.folder_institution_map[folder_name],
                    'warehouse_class': '权利仓',
                }
                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ZhongJinCaiFu.option_acc, identified_dict)
                acc_obj = matcher.map(content.sheet_by_name('客户结算单查询'))[0]
                result_dict[product_name]['account'] = acc_obj

                # option_flow_filename = '历史交收明细查询{}.xls'.format(pro_id)
                # if os.path.exists(os.listdir(folder_path, option_flow_filename)):
                #     content = xlrd.open_workbook(os.listdir(folder, option_flow_filename))
                #     matcher = ExcelMapper(GuoJun.option_flow, identified_dict)
                #     flow_list = matcher.map(content.sheet_by_name(option_flow_filename.split('.')[0]))
                # else:
                #     flow_list = DataList(RawOptionFlow)
                flow_list = list()
                result_dict[product_name]['flow'] = flow_list

                pos_list = list()
                result_dict[product_name]['position'] = pos_list

                confirm_option_flow_list(flow_list)
                match_option_pos_acc(pos_list, acc_obj)
            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map
