# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import re
import datetime
import xlrd

from trade.Interface import AbstractLoader
from trade.Checker import *


class HuaJing(AbstractLoader):

    normal_flow = {
        'security_code': ['股票代码', ], 'security_name': ['股票名称', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_class': ['买卖方向', ],
        'trade_time': ['成交时间', ],
        'trade_amount': ['成交金额', '成交金额港币', ],
        'trade_name': ['委托属性', ], 'trade_status': ['成交类别', ],
        None: ['序号', '股东帐号', '成交编号', '证券市场', ]
    }

    @staticmethod
    def load_normal_excel(file_path: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import ExcelMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        xls_content = xlrd.open_workbook(file_path, encoding_override='gb18030')
        mapper = ExcelMapper(HuaJing.normal_flow, hand_dict)
        mapper.ignore_line.update(['制作完成于', ])
        flow_list = mapper.map(xls_content.sheet_by_index(0))

        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'].split(' ')[-1], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            # flow['trade_name'] = str_check(flow['trade_class'])
            trade_status = str_check(flow['trade_status'])
            assert trade_status == '买卖', str(flow)
            # if str_check(flow['trade_name']) == '撤单':
            #     flow['trade_amount'] = float_check(flow['trade_price']) * float_check(flow['trade_volume'])
            trade_class = str_check(flow['trade_class'])
            if trade_class in ('买入', '证券买入',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出', '证券卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list

    # margin_flow = {
    #     'trade_time': ['成交时间', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
    #     'trade_class': ['操作', ], 'trade_price': ['成交均价', ], 'trade_volume': ['成交数量', ],
    #     'trade_amount': ['成交金额', ],
    #     # 'trade_name': ['业务名称', ], 'trade_status': ['成交状态', ],
    #     None: ['股东帐户', '交易市场', '合同编号', '成交编号', ]
    # }
    #
    # @staticmethod
    # def load_simple_margin(file_path: str, product: str, date: datetime.date, institution: str, ):
    #     from jetend.structures import TextMapper
    #     content_list = list()
    #     content_file = open(file_path, mode='r', ).read()
    #     for content_line in content_file.split('\n'):
    #         line_list = list()
    #         for content_cell in content_line.split('\t'):
    #             if re.match(r'=\"([\w\W]*)\"', content_cell):
    #                 line_list.append(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
    #                 # print(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
    #             elif len(re.sub(r'[:\d.,]', '', content_cell)) == 0:
    #                 line_list.append(content_cell)
    #             elif len(re.sub(r'\W', '', content_cell)) == 0:
    #                 continue
    #             elif len(re.sub(r'\w', '', content_cell)) == 0:
    #                 continue
    #             else:
    #                 raise NotImplementedError('{}\n{}'.format(content_cell, content_line))
    #         content_list.append(' '.join(line_list))
    #     content_list = '\n'.join(content_list)
    #
    #     hand_dict = {
    #         'product': product, 'date': date, 'institution': institution,
    #         'currency': 'RMB', 'account_type': '两融账户',
    #     }
    #     mapper = TextMapper(DeBang.normal_flow, hand_dict)
    #     flow_list = mapper.map(content_list)
    #     for flow in flow_list:
    #         trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
    #         flow['trade_time'] = trade_time
    #         # trade_status = str_check(flow['trade_status'])
    #         # assert trade_status == '成交', str(flow)
    #         trade_class = str_check(flow['trade_class'])
    #         flow['trade_name'] = trade_class
    #         if trade_class in ('买入',):
    #             flow['trade_direction'] = TRADE_DIRECTION_BUY
    #         elif trade_class in ('卖出',):
    #             flow['trade_direction'] = TRADE_DIRECTION_SELL
    #         else:
    #             raise NotImplementedError(flow)
    #     confirm_margin_trade_flow_list(flow_list)
    #     return flow_list
