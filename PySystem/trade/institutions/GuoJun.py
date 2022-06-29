# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import re
import xlrd

from trade.Interface import AbstractLoader
from trade.Checker import *


class GuoJun(AbstractLoader):
    normal_flow = {
        'trade_class': ['方向', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_name': ['成交类型', ], 'trade_status': ['成交状态', ],
        'trade_volume': ['成交数量', ], 'trade_price': ['成交价格', '委托价格港币'],
        'trade_amount': ['成交金额', ], 'trade_time': ['成交时间', ],
        None: ['流水号', '股东代码', '委托数量', '委托价格', '委托序号', '交易市场']
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
            # flow['trade_name'] = str_check(flow['trade_class'])
            trade_status = str_check(flow['trade_status'])
            assert trade_status == '成交', str(flow)
            if str_check(flow['trade_name']) == '撤单':
                flow['trade_amount'] = float_check(flow['trade_price']) * float_check(flow['trade_volume'])
            trade_class = str_check(flow['trade_class'])
            if '港股通' in institution:
                flow['trade_amount'] = float_check(flow['trade_price']) * float_check(flow['trade_volume'])
            if trade_class in ('买入', '证券买入', '增强限价买入'):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出', '证券卖出', '增强限价卖出'):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list

    margin_flow = {
        'trade_class': ['方向', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_name': ['成交类型', ], 'trade_status': ['成交状态', ],
        'trade_volume': ['成交数量', ], 'trade_price': ['成交价格', ], 'trade_amount': ['成交金额', ],
        'trade_time': ['成交时间', ],
        None: ['流水号', '股东代码', '委托数量', '委托价格', ]
    }

    @staticmethod
    def load_margin_excel(file_path: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import ExcelMapper
        # content_list = list()
        # content_file = open(file_path, mode='r', ).read()
        # for content_line in content_file.split('\n'):
        #     line_list = list()
        #     for content_cell in content_line.split('\t'):
        #         if re.match(r'=\"([\w\W]*)\"', content_cell):
        #             line_list.append(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
        #             # print(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
        #         elif len(re.sub(r'[:\d.,]', '', content_cell)) == 0:
        #             line_list.append(content_cell)
        #         elif len(re.sub(r'\W', '', content_cell)) == 0:
        #             continue
        #         elif len(re.sub(r'\w', '', content_cell)) == 0:
        #             continue
        #         else:
        #             raise NotImplementedError('{}\n{}'.format(content_cell, content_line))
        #     content_list.append(' '.join(line_list))
        # content_list = '\n'.join(content_list)
        content = xlrd.open_workbook(file_path, encoding_override='gb18030')

        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '两融账户',
        }
        mapper = ExcelMapper(GuoJun.normal_flow, hand_dict)
        flow_list = mapper.map(content.sheet_by_index(0))
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S.%f').time()
            flow['trade_time'] = trade_time
            trade_status = str_check(flow['trade_status'])
            assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            if str_check(flow['trade_name']) == '撤单':
                flow['trade_amount'] = float_check(flow['trade_price']) * float_check(flow['trade_volume'])
            # flow['trade_name'] = trade_class
            trade_name = str_check(flow['trade_name'])
            assert trade_name == '买卖', flow
            flow['trade_name'] = trade_class
            if trade_class in ('买入', '普通买入', ):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出', '普通卖出', ):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
            if trade_class in ('买入', '普通买入', '卖出', '普通卖出',):
                flow['trade_class'] = '担保'
            elif trade_class in ():
                flow['trade_class'] = '融资'
            else:
                raise NotImplementedError(flow)
        confirm_margin_trade_flow_list(flow_list)
        return flow_list

    future_flow = {
        'security_code': ['合约', ], 'trade_class': ['买卖', ], 'trade_offset': ['开平', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交手数', ],
        'trade_time': ['成交时间', ], 'trade_name': ['成交类型', ], 'trade_tag': ['投保', ],
        None: ['报单编号', '成交编号', '交易所', ],
    }

