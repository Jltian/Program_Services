# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import xlrd

from trade.Interface import AbstractLoader
from trade.Checker import *


class GuoXin(AbstractLoader):

    normal_flow = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['买卖标志', ], 'trade_volume': ['成交数量', ],
        'trade_price': ['成交价格', '成交价格港元'], 'trade_amount': ['成交金额', '成交金额港元'],
        'trade_name': ['摘要', '成交类型'],  'trade_time': ['成交时间', ],
        # 'trade_status': ['成交类型', ],
        'UNKNOWN': ['备注', ],
        None: ['委托编号', '成交编号', '股东代码', '交易所名称', ]
    }

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import TextMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        mapper = TextMapper(GuoXin.normal_flow, hand_dict)
        mapper.set_line_sep('|')
        mapper.ignore_cell.update(['备注', ])
        flow_list = list()
        for flow in mapper.map(content_text):
            # trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            # flow['trade_time'] = trade_time
            # trade_status = str_check(flow['trade_status'])
            trade_class = str_check(flow['trade_class'])
            # flow['trade_name'] = trade_class
            flow['trade_status'] = str_check(flow['trade_name'])
            if '撤单' in flow['trade_status']:
                continue
            if trade_class in ('买入', '限价买入', '增强限价买入', ):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出', '限价卖出'):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
            flow_list.append(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list
