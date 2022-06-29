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
from BatchDecompression import *


class YongAn(AbstractInstitution):
    folder_institution_map = {
        '永安期货账户': '永安期货',
    }

    future_acc = {
        'currency': ['币种', ], 'customer_id': ['客户号', ], 'market_sum': ['保证金占用', ],
        'last_capital_sum': ['期初权益', ], 'market_pl': ['持仓盯市盈亏', ], 'realized_pl': ['平仓盈亏', ],
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
            '207180320': '静康1号', '257188928': '久铭7号', '207180321': '久铭10号',
            '257188925': '收益1号', '257188926': '收益2号', '207180323': '稳健23号',
            '207180166': '久铭久盈2号', '207180502':'久铭专享23号' # @waves'
        }
        for fd in os.listdir(folder_path):
            target_file = os.path.join(folder_path, fd)
            if os.path.isfile(target_file) and target_file.endswith('.rar'):
                BatchDecompression(folder_path, folder_path, ['盯市']).batchExt()
                break

        for file_name in os.listdir(folder_path):
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('txt'):
                YongAn.log.debug(file_name)
                if '盯市' not in file_name:
                    os.remove(os.path.join(folder_path, file_name))
                    continue
                # 207180320账单(盯市)
                pro_id = re.match(r"(\d+)账单", file_name).group(1)
                product_name = id_product_map[pro_id]
                if product_name not in folder_result_dict:
                    folder_result_dict[product_name] = None
                product_file_map[product_name] = file_name
                # content = open(
                #     os.path.join(folder_path, file_name), mode='r', encoding='utf-8', errors='ignore'
                # ).read()
                # # GuoJun.log.debug(content)
                # identified_dict = {
                #     'date': date, 'product': product_name,
                #     'institution': YongAn.folder_institution_map[folder_name],
                #     'currency': 'RMB', 'account_type': folder_name,
                # }
                #
                # matcher = TextMapper(YongAn.future_acc, identified_dict)
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
                # matcher = TextMapper(YongAn.future_pos, identified_dict)
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
                # matcher = TextMapper(YongAn.future_flow, identified_dict)
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
            elif file_name.lower().endswith('dbf'):
                os.remove(os.path.join(folder_path, file_name))
                continue
            elif file_name.lower().endswith('rar'):
                continue
            else:
                raise NotImplementedError(file_name)

        return folder_result_dict, product_file_map
