# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import xlrd

from trade.Interface import AbstractLoader
from trade.Checker import *


class HuaTai(AbstractLoader):

    normal_flow = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['操作', ], 'trade_volume': ['成交数量', ], 'trade_price': ['成交均价', ],
        'trade_amount': ['成交金额', ],
        # 'trade_name': ['成交类型', ], 'trade_status': ['成交状态', ],
        # 'trade_time': ['成交时间', ],
        None: ['成交日期', '合同编号', '交易市场', '股东帐户', '成交编号']
        # None: ['流水号', '股东代码', '委托数量', '委托价格', ]
    }

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import TextMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        mapper = TextMapper(HuaTai.normal_flow, hand_dict)
        mapper.set_line_sep('|')
        flow_list = mapper.map(content_text)
        for flow in flow_list:
            # trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            # flow['trade_time'] = trade_time
            # trade_status = str_check(flow['trade_status'])
            trade_class = str_check(flow['trade_class'])
            flow['trade_name'] = trade_class
            if trade_class in ('买入',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list
