# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import os
import xlrd

import pandas as pd

from core.Interface import AbstractLoader
from modules.Checker import *


class AnXin(AbstractLoader):

    normal_flow = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'trade_class': ['买卖标志', '方向'],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
        'trade_time': ['成交时间', ],
        # 'trade_name': ['业务名称', ], 'trade_status': ['状态说明', ],
        None: [
            '委托时间', '委托编号', '委托类型', '委托价格', '委托数量', '股东代码', '资金帐号', '客户代码',
            '股东姓名', '市场', '委托号', '实时清算金额', '委托冻结金额', '成交日期', '成交编号', '账户名'
        ]
    }

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import TextMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        mapper = TextMapper(AnXin.normal_flow, hand_dict)
        mapper.set_line_sep('|')
        mapper.ignore_cell.update(['委托类型', ])
        flow_list = mapper.map(content_text)
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            flow['trade_name'] = str_check(flow['trade_class'])
            # trade_status = str_check(flow['trade_status'])
            # assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            if trade_class in ('买入',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list

    @staticmethod
    def load_normal_excel(file_path: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import ExcelMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        xls_content = xlrd.open_workbook(file_path, encoding_override='gb18030')
        mapper = ExcelMapper(AnXin.normal_flow, hand_dict)
        flow_list = mapper.map(xls_content.sheet_by_index(0))

        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            flow['trade_name'] = str_check(flow['trade_class'])
            # trade_status = str_check(flow['trade_status'])
            # assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            flow['trade_status'] = trade_class
            if trade_class in ('买入', '证券买入',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出', '证券卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list

    future_flow = {
        'security_code': ['合约', ], 'trade_class': ['买卖', ], 'trade_offset': ['开平', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交手数', ],
        'trade_time': ['成交时间', ], 'trade_name': ['成交类型', ], 'trade_tag': ['投保', ],
        None: ['报单编号', '成交编号', '交易所', ],
    }

    @staticmethod
    def load_future_excel(file_path: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import ExcelMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '期货账户',
        }
        xls_book = xlrd.open_workbook(file_path)
        mapper = ExcelMapper(AnXin.future_flow, hand_dict)
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
        return AnXin.load_future_excel(
            os.path.join(temp_folder, '{}.xls'.format(file_name)),
            product, date, institution,
        )
