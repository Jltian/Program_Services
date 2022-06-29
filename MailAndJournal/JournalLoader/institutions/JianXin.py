# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import zipfile


from Abstracts import AbstractInstitution
from Checker import *


class JianXin(AbstractInstitution):
    """建信"""
    folder_institution_map = {
        '建信期货账户': '建信期货',
    }

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

    @staticmethod
    def load_future(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        id_product_map = {
            '30000072': '久铭1号',
        }
        for file_name in os.listdir(folder_path):
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('zip'):
                with zipfile.ZipFile(os.path.join(folder_path, file_name), mode='r') as z_file:
                    for sub_file in z_file.namelist():
                        assert isinstance(sub_file, str)
                        if os.path.sep in file_name or '/' in sub_file:
                            continue
                        if sub_file.endswith('.txt'):
                            z_file.extract(sub_file, path=folder_path)
                os.remove(os.path.join(folder_path, file_name))

            elif file_name.lower().endswith('txt'):
                try:
                    pro_id = re.match(r"(\d+)", file_name).group(1)
                except AttributeError:
                    pro_id = re.match(r"(\d+)客户结算", file_name).group(1)
                product_name = id_product_map[pro_id]
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': JianXin.folder_institution_map[folder_name],
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

                matcher = TextMapper(JianXin.future_acc, identified_dict, )
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
