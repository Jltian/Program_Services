# -*- encoding: UTF-8 -*-
import os
import re
import xlrd
import datetime

from Abstracts import AbstractInstitution
from Checker import *


class HuaJing(AbstractInstitution):
    """海通"""
    folder_institution_map = {
        '华菁普通账户': '华菁',
    }

    # =================================== =================================== #
    normal_pos = {
        'shareholder_code': ['股东帐号', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'hold_volume': ['股份余额', ], 'weight_average_cost': ['参考成本价', ], 'close_price': ['参考市价', ],
        'market_value': ['参考市值', ],
        # 'security_code_name': ['证券代码简称', '股东代码证券代码简称', ],
        'None': ['交易类别', '股份可用', '交易冻结', '参考成本', '参考盈亏']
    }
    normal_flow = {
        'trade_class': ['摘要', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_volume': ['成交股数', ], 'trade_price': ['成交价格', ], 'cash_move': ['清算金额', ],
        'trade_amount': ['成交金额', ],
        # 'shareholder_code': ['股东代码', ], 'security_code_name': ['证券代码简称', ],
        # 'total_fee': ['交易费', ], 'customer_id': ['客户号', ],
        'None': ['发生日期', '交易类别', '佣金', '印花税', '过户费', '资金余额', '净佣金', ]
    }
    normal_acc = {
        'cash_amount': ['资金余额', ], 'market_sum': ['资产市值', ],
        'capital_sum': ['总资产', ], 'cash_available': ['可用余额', ],
        'None': ['客户代码', '资产账户', ]
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            HuaJing.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.endswith('xls'):
                assert date.strftime('%Y%m%d') in file_name, '对账单日期有误 {}'.format(file_name)
                product_name = derive_product_name(file_name)
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                identified_dict = {
                    'date': date, 'product': product_name, 'currency': 'RMB',
                    'institution': HuaJing.folder_institution_map[folder_name],
                    'account_type': folder_name, 'offset': OFFSET_OPEN,
                }

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                # 流水
                matcher = ExcelMapper(HuaJing.normal_flow, identified_dict, )
                matcher.set_start_line('对账单').set_end_line('拥股情况')
                matcher.ignore_line.update(['合计', '期初余额'])
                flow_list = matcher.map(content.sheet_by_name('合并对帐单'))
                if flow_list[0]['security_code'] == '' and flow_list[0]['trade_volume'] == '':
                    flow_list = []
                result_dict[product_name]['flow'] = flow_list
                # @waves
                # 持仓
                matcher = ExcelMapper(HuaJing.normal_pos, identified_dict)
                matcher.set_start_line('拥股情况').set_end_line('新股配号')
                matcher.ignore_line.update(['合计', ])
                pos_list = matcher.map(content.sheet_by_name('合并对帐单'))
                if pos_list[0]['security_code'] == '' and pos_list[0]['hold_volume'] == '':
                    pos_list = []
                result_dict[product_name]['position'] = pos_list
                # @waves
                # 资金
                matcher = ExcelMapper(HuaJing.normal_acc, identified_dict)
                matcher.set_start_line('资金情况').set_end_line('对帐单')
                acc_obj = matcher.map(content.sheet_by_name('合并对帐单'))[0]
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map
