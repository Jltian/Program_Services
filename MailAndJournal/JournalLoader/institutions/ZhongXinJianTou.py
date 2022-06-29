# -*- encoding: UTF-8 -*-
import datetime
import os
import xlrd
import re

from Abstracts import AbstractInstitution
from Checker import *

class ZhongXinJianTou(AbstractInstitution):
    """中信建投"""
    folder_institution_map = {
        '中信建投普通账户': '中信建投',
    }

    normal_pos = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'hold_volume': ['当前余额', ],
        'market_value': ['证券市值', ], 'close_price': ['最新价', ], 'total_cost': ['参考成本', ],
        'weight_average_cost': ['参考成本价格'],
        'None': ['可用数量', '盈亏金额', '实时余额'],
    }
    normal_flow = {
        'trade_class': ['业务标志', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_price': ['价格', ], 'trade_volume': ['发生数', ], 'cash_move': ['发生金额', ],
        'shareholder_code': ['股东帐号', '股东账号'],
        'None': ['日期', '银行', '资金余额', '手续费', '印花税', '过户费', '备注']
    }
    normal_acc = {
        'currency': ['币种', ], 'cash_amount': ['当前余额', ], 'market_sum': ['当前市值', '场内证券资产', ],
        'capital_sum': ['总资产', ],
        'None': ['当前可用', '实时余额'],
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper, TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        id_product_map = {
            '55816988': '收益1号', '56569303': '创新稳健1号', '56611841': '创新稳健2号',
            '99148740': '收益1号','23003943':'收益1号'
        }

        for file_name in os.listdir(folder_path):
            ZhongXinJianTou.log.debug_running(file_name)
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('pdf'):
                continue
            elif '副本' in file_name:
                continue
            elif file_name.upper().endswith('TXT'):
                if '-' in file_name:
                    # cash_account, date_str = re.match(r'(\d+)-(\d\d\d\d*)', file_name).groups()
                    cash_account = re.match(r'(\d+)[\D]', file_name).group(1)
                elif '\xa0' in file_name:
                    cash_account = file_name.split('\xa0')[0]
                    date_str = file_name.split('\xa0')[-1]
                    date_str = date_str.split('.')[0]
                    # cash_account = re.match(r'(\d+)\W[^\d]+', file_name).group(0)
                else:
                    try:
                        cash_account,date_str = re.match(r'(\d+)[^\d]+\d[号指数]+[^\d]+(\d+)', file_name).groups()
                    except AttributeError:
                        raise NotImplementedError(file_name)
                # if len(date_str) == 4:
                #     assert date_str == date.strftime('%m%d'), '{} {}'.format(date, file_name)
                # else:
                #     assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date, date_str)

                product_name = id_product_map[cash_account]

                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                identified_dict = {
                    'date': date, 'product': product_name, 'account_type': folder_name,
                    'institution': ZhongXinJianTou.folder_institution_map[folder_name], 'currency': 'RMB',
                    'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                matcher = TextMapper(ZhongXinJianTou.normal_flow, identified_dict)
                matcher.set_line_sep('│')
                matcher.ignore_line.update(['合计'])
                if re.search(r"资产交割([\W\w]*)证券资产",content,re.M):
                    flow = re.search(r"资产交割([\W\w]*)证券资产", content, re.M).groups()
                else:
                    os.remove(os.path.join(folder_path,file_name))
                    del result_dict[product_name]   # @ waves
                    continue
                # flow = re.search(r"资金流水明细([\W\w]*)股份余额汇总", content, re.M).groups()
                assert len(flow) == 1, 'wrong re implication'
                flow_list = matcher.map(flow[0])
                result_dict[product_name]['flow'] = flow_list

                matcher = TextMapper( ZhongXinJianTou.normal_pos, identified_dict)
                matcher.set_line_sep('│')
                matcher.ignore_line.update(['合计'])
                try:
                    pos = re.search(r"([^场内]证券资产[\W\w]*)质押券", content, re.M).group(0)
                except AttributeError:
                    pos = re.search(r"([^场内]证券资产[\W\w]*)", content, re.M).group(0)
                pos_list = matcher.map(pos)
                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(ZhongXinJianTou.normal_acc, identified_dict)
                matcher.set_line_sep('│')
                pos = re.search(r"(资产信息[\W\w]*资产明细)", content, re.M).groups()
                assert len(pos) == 1, 'wrong re implication'
                acc_obj = matcher.map(pos[0])[0]
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            elif file_name.lower().endswith('xls'):
                try:
                    cash_account, date_str = re.match(r'(\d+)[^\d]+\d[号指数]+[^\d]+(\d+)', file_name).groups()
                except AttributeError:
                    raise NotImplementedError(file_name)
                if len(date_str) == 4:
                    assert date_str == date.strftime('%m%d'), '{} {}'.format(date, file_name)
                else:
                    assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date, date_str)

                product_name = id_product_map[cash_account]

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                identified_dict = {
                    'date': date, 'product': product_name, 'account_type': folder_name,
                    'institution': ZhongXinJianTou.folder_institution_map[folder_name], 'currency': 'RMB',
                    'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                matcher = ExcelMapper(ZhongXinJianTou.normal_flow, identified_dict)
                matcher.set_start_line('资产交割').set_end_line('证券资产')
                matcher.ignore_line.update(['合计'])
                flow_list = matcher.map(content.sheet_by_index(0))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhongXinJianTou.normal_pos, identified_dict)
                matcher.set_start_line('证券资产').set_end_line('质押券余额明细数据')
                matcher.ignore_line.update(['合计'])
                pos_list = matcher.map(content.sheet_by_index(0))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongXinJianTou.normal_acc, identified_dict)
                matcher.set_start_line('资产信息').set_end_line('资产交割')
                acc_obj = matcher.map(content.sheet_by_index(0))[0]
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map


if __name__ == '__main__':
    print(ZhongXinJianTou.load_normal(
        r'D:\Documents\久铭产品交割单20190821\中信建投普通账户',
        datetime.date(2019, 8, 21),
    ))
