# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import xlrd

from core.Interface import AbstractLoader
from modules.Checker import *


class XingYe(AbstractLoader):

    normal_flow = {
        'trade_time': ['成交时间', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['买卖标志', '委托类型', '买卖'],
        'trade_price': ['成交价格', '成交均价', '成交均价港币'], 'trade_volume': ['成交数量', ],
        'trade_amount': ['成交金额', '成交金额港币'],
        # 'trade_name': ['业务名称', ], 'trade_status': ['成交状态', ],
        None: ['成交编号', '委托编号', '股东代码', '合同编号', '申报编号', '交易市场', ]
    }

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import TextMapper
        if '港股通' in institution:
            currency = 'HKD'
        else:
            currency = 'RMB'
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': currency, 'account_type': '普通账户',
        }
        mapper = TextMapper(XingYe.normal_flow, hand_dict)
        mapper.set_line_sep('|')
        mapper.ignore_cell.update(['备注', ])
        flow_list = mapper.map(content_text)
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            # trade_status = str_check(flow['trade_status'])
            # assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            flow['trade_name'] = trade_class
            if trade_class in ('买入', '证券买入', '买'):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出', '证券卖出', '卖'):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list
