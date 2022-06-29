# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import xlrd

from core.Interface import AbstractLoader
from modules.Checker import *


class GuoJun(AbstractLoader):
    normal_flow = {
        'trade_class': ['方向', ],'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_name': ['成交类型', ], 'trade_status': ['成交状态', ],
        'trade_volume': ['成交数量', ], 'trade_price': ['成交价格', ], 'trade_amount': ['成交金额', ],
        'trade_time': ['成交时间', ],
        None: ['流水号', '股东代码', '委托数量', '委托价格', ]
    }

    @staticmethod
    def load_normal_excel(file_path: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import ExcelMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        xls_content = xlrd.open_workbook(file_path, encoding_override='gb18030')
        mapper = ExcelMapper(GuoJun.normal_flow, hand_dict)
        flow_list = mapper.map(xls_content.sheet_by_index(0))

        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S.%f').time()
            flow['trade_time'] = trade_time
            flow['trade_name'] = str_check(flow['trade_class'])
            trade_status = str_check(flow['trade_status'])
            assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            if trade_class in ('买入', '证券买入', ):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出', '证券卖出', ):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list

