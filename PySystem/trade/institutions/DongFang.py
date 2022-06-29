# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import re
import xlrd

from trade.Interface import AbstractLoader
from trade.Checker import *


class DongFang(AbstractLoader):

    normal_flow = {
        'security_name': ['证券名称', ],  'trade_time': ['成交时间', ], 'trade_class': ['买卖标志', ],
        'trade_price': ['成交价格', '成交价格HK'], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
        'security_code': ['证券代码', ],
        # 'trade_name': ['业务名称', ],
        'trade_status': ['成交状态', ],
        'UNKNOWN': ['委托属性', ],
        None: ['成交编号', '委托编号', '股东代码', ]
    }

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import TextMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        mapper = TextMapper(DongFang.normal_flow, hand_dict)
        mapper.set_line_sep('|')
        mapper.ignore_cell.update(['委托属性', ])
        flow_list = mapper.map(content_text)
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            if str_check(flow['security_code']) in ('00939', ):
                flow['trade_amount'] = float_check(flow['trade_price']) * float_check(flow['trade_volume'])
            if '港股通' in institution or 'HK' in str_check(flow['security_code']):
                flow['trade_amount'] = float_check(flow['trade_price']) * float_check(flow['trade_volume'])
            # trade_status = str_check(flow['trade_status'])
            # assert trade_status == '成交', str(flow)
            if str_check(flow['security_code'])[:3] in ('132', '110', ):
                flow['trade_volume'] = 10 * float_check(flow['trade_volume'])
            trade_class = str_check(flow['trade_class'])
            flow['trade_name'] = trade_class
            if trade_class in ('买入', '买'):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出', '卖'):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        for flow in flow_list:
            check_basic_info(flow)
            check_security_info(flow)
            try:
                check_basic_trade_info(flow)
            except AssertionError:
                check_float_element(flow, 'trade_price', '交易价格')
                check_float_element(flow, 'trade_volume', '交易数量')
                check_float_element(flow, 'trade_amount', '交易额')
        return flow_list
