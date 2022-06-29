import datetime
import os
import re
import xlrd

from Abstracts import AbstractInstitution
from Checker import *


class GuoXin(AbstractInstitution):
    folder_institution_map = {
        '国信普通账户': '国信',

    }

    # =================================== =================================== #
    normal_flow = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],  # 'trade_direction': '交易方向',
        'trade_class': ['操作摘要', ], 'trade_price': ['成交均价', ],
        'trade_volume': ['成交股数', ], 'trade_amount': ['成交金额', ], 'cash_move': ['资金发生数', ],
        'None': [
            '发生日期', '手续费', '过户费', '印花税', '本次余额',
        ]
    }
    normal_pos = {
        'shareholder_code': ['证券帐号', ],
        'security_name': ['证券名称'], 'security_code': ['证券代码'],
        'hold_volume': ['证券余额'], 'close_price': ['最新价'], 'market_value': ['市值',],
        'None': ['股份可用', '交易冻结', '参考盈亏', '港股在途数量', '市场' ],
    }
    normal_acc = {
        'market_sum': ['股票市值', ], 'capital_sum': ['总资产', ], 'cash_amount': ['资金余额', ],
        'None': ['资金余额', '港股通资金可用', '客户姓名', ],
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        """
        读取普通账户对账单
        返回读取到的数据结果：
        {
            product: {
                'account': dict()  # 账户信息，单个包含信息的字典对象
                'flow': list(dict, )   # 流水信息，包含信息的流水字典对象组成的列表
                'position': list(dict, )   # 持仓信息
            }
        }
        :return:
        """
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        product_id_map = {
            '416600007759':'久铭1号',  '416600009389':'收益2号',
        }

        # 全目录文件扫描
        for file_name in os.listdir(folder_path):
            GuoXin.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or '手动备份' in file_name:
                continue
            elif '副本' in file_name:
                continue
            elif file_name.lower().endswith('xls'):
                try:
                    product_id = re.search(r'(\d+)[(]', file_name).group(1)
                    product_name = product_id_map[product_id]
                except AttributeError:
                    raise  NotImplementedError(file_name)
                #print(product_name)
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': GuoXin.folder_institution_map[folder_name], 'currency': 'RMB',
                    'offset': OFFSET_OPEN,
                }
                # 初始化result_dict
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                #持仓
                matcher = ExcelMapper(GuoXin.normal_pos, identified_dict)
                matcher.ignore_line.update(['合计'])
                matcher.set_start_line('股份余额汇总')
                pos_list = matcher.map(content.sheet_by_name('合并对账单'))
                result_dict[product_name]['position'] = pos_list

                #流水
                matcher = ExcelMapper(GuoXin.normal_flow, identified_dict)
                matcher.set_start_line('资金流水明细').set_end_line('股份余额汇总')
                matcher.ignore_line.update(['合计'])
                # matcher.ignore_cell.update(['市值'])
                flow_list = matcher.map(content.sheet_by_name('合并对账单'))
                for flow in flow_list:
                    if flow['trade_volume'] == '0':
                        flow['trade_amount'] = 0
                    else:
                        flow['trade_price'] = float_check(flow['trade_amount'])/ float_check(flow['trade_volume'])
                result_dict[product_name]['flow'] = flow_list

                #账户资金
                matcher = ExcelMapper(GuoXin.normal_acc, identified_dict)
                matcher.map_horizontal(content.sheet_by_name('合并对账单'))
                acc_obj = matcher.form_new()
                #print(acc_obj)
                # matcher.set_start_line('资金情况')
                # acc_obj = matcher.map(content.sheet_by_name('资金情况'))[0]
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('.rar'):
                os.remove(os.path.join(folder_path, file_name))

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
        GuoXin.log.debug_running('读取托管估值表', file_name)
        # 文件名：2019-08-31_SL0795_久铭稳健22号私募证券投资基金_估值表
        # 文件名：SL0795_久铭稳健22号私募证券投资基金估值表_20191105
        try:
            date_str, product_code, product_name = re.match(
                r'(\d+-\d+-\d+)_([A-Za-z0-9]+)_(\w+)私募证券', file_name
            ).groups()
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except AttributeError:
            try:
                product_code, product_name, date_str = re.match(
                    r'([A-Za-z0-9]+)_(\w+)私募证券投资基金估值表_(\d+)', file_name
                ).groups()
                date = datetime.datetime.strptime(date_str, '%Y%m%d')
            except AttributeError:
                product_code, product_name, date_str = re.match(
                    r'([A-Za-z0-9]+)久铭(\w+)私募证券投资基金估值表(\d+)', file_name
                ).groups()
                date = datetime.datetime.strptime(date_str, '%Y%m%d')
        product_name = PRODUCT_CODE_NAME_MAP[product_code]
        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '国信证券',
        }
        mapper = ExcelMapper(GuoXin.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)


if __name__ == '__main__':
    print(GuoXin.load_normal(
        r'D:\Documents\久铭产品交割单20190822\国信普通账户',
        datetime.date(2019, 8, 22)
    ))