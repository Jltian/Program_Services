# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import os
import re
import xlrd

import pandas as pd

from trade.Interface import AbstractLoader
from trade.Checker import *


class ChangJiang(AbstractLoader):

    normal_flow = {
        'trade_time': ['成交时间', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['买卖标志', ], 'trade_status': ['状态说明', '成交状态', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
        # 'trade_name': ['业务名称', ],
        None: ['委托类别', '成交编号', '委托编号', '股东代码', ]
    }

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import TextMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        mapper = TextMapper(ChangJiang.normal_flow, hand_dict)
        mapper.set_line_sep('|')
        flow_list = mapper.map(content_text)
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            flow['trade_name'] = str_check(flow['trade_class'])
            trade_status = str_check(flow['trade_status'])
            assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            if trade_class in ('买入',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            # elif trade_class in ('卖出撤单', ):
            #     flow['trade_direction'] =
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list

    margin_flow = {
        'trade_time': ['成交时间', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['买卖标志', ], 'trade_status': ['状态说明', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
        # 'trade_name': ['业务名称', ],
        None: ['委托类别', '成交编号', '委托编号', '股东代码', ]
    }

    @staticmethod
    def load_simple_margin(file_path: str, product: str, date: datetime.date, institution: str, ):
        from jetend.structures import TextMapper
        content_list = list()
        content_file = open(file_path, mode='r', ).read()
        for content_line in content_file.split('\n'):
            line_list = list()
            for content_cell in content_line.split('\t'):
                if re.match(r'=\"([\w\W]*)\"', content_cell):
                    line_list.append(re.search(r'=\"([^\"=]*)\"', content_cell.replace(' ', '')).groups()[0])
                    # print(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
                elif len(re.sub(r'[:\d.,]', '', content_cell)) == 0:
                    line_list.append(content_cell)
                elif len(re.sub(r'\W', '', content_cell)) == 0:
                    continue
                elif len(re.sub(r'\w', '', content_cell.replace(' ', ''))) == 0:
                    line_list.append(content_cell.replace(' ', ''))
                # elif len(re.sub(r'\w', '', content_cell)) == 0:
                #     continue
                else:
                    raise NotImplementedError('{}\n{}'.format(content_cell, content_line))
            content_list.append(' '.join(line_list))
        content_list = '\n'.join(content_list)

        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '两融账户',
        }
        mapper = TextMapper(ChangJiang.margin_flow, hand_dict)
        flow_list = mapper.map(content_list)
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            trade_status = str_check(flow['trade_status'])
            assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            flow['trade_name'] = trade_class
            if trade_class in ('买入',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
                flow['trade_class'] = '担保'
            elif trade_class in ('卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
                flow['trade_class'] = '担保'
            else:
                raise NotImplementedError(flow)
        confirm_margin_trade_flow_list(flow_list)
        return flow_list

    future_flow = {
        'security_code': ['合约', ], 'trade_class': ['买卖', ], 'trade_offset': ['开平', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交手数', ],
        'trade_time': ['成交时间', ], 'trade_name': ['成交类型', ], 'trade_tag': ['投保', ],
        None: ['成交编号', '报单编号', '交易所', ],
    }

    @staticmethod
    def load_future_excel(file_path: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import ExcelMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '期货账户',
        }
        xls_book = xlrd.open_workbook(file_path)
        mapper = ExcelMapper(ChangJiang.future_flow, hand_dict)
        flow_list = mapper.map(xls_book.sheet_by_index(0))
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            trade_class = str_check(flow['trade_class'])
            if trade_class in ('买',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_future_trade_flow_list(flow_list)
        return flow_list

    @staticmethod
    def load_future_csv(file_path: str, product: str, date: datetime.date, institution: str):
        file_name = file_path.split(os.path.sep)[-1].split('.')[0]
        temp_folder = os.path.join(AbstractLoader.root_path(), 'temp', date.strftime('%Y%m%d'))
        os.makedirs(temp_folder, exist_ok=True)
        pd_csv = pd.read_csv(file_path, encoding='gb18030')
        pd_csv.to_excel(os.path.join(temp_folder, '{}.xls'.format(file_name)), )
        return ChangJiang.load_future_excel(
            os.path.join(temp_folder, '{}.xls'.format(file_name)),
            product, date, institution,
        )
