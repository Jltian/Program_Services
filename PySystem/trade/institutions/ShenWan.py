# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import re
import xlrd

from trade.Interface import AbstractLoader
from trade.Checker import *


class ShenWan(AbstractLoader):

    normal_flow = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'trade_class': ['买卖标志', '买卖'],
        'trade_volume': ['成交数量', ],
        'trade_price': ['成交价格', ],
        'trade_amount': ['成交金额', ],
        'trade_time': ['成交时间', ],
        # 'trade_status': ['状态说明', ],
        # 'trade_name': ['业务名称', ],
        None: ['股东代码', '成交编号', '席位代码', '申报序号', '委托编号', '解冻证券数量', '解冻资金金额', '流水号', '报价方式', ]
    }

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import TextMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        mapper = TextMapper(ShenWan.normal_flow, hand_dict)
        mapper.set_line_sep('|')
        flow_list = mapper.map(content_text)
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            # trade_status = str_check(flow['trade_status'])
            # assert trade_status == '成交', str(flow)
            # if '港股通' in institution:
            #     pass
            # else:
            if '港股通' in institution:
                flow['trade_amount'] = float_check(flow['trade_price']) * float_check(flow['trade_volume'])
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

    margin_flow = {
        'trade_time': ['成交时间', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['描述', ], 'trade_status': ['成交类型', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
        # 'trade_name': ['业务名称', ],
        None: ['委托类别', '成交编号', '委托编号', '股东代码', '申报合同序号', '买卖标志', '委托价格', '委托数量', '交易市场', ]
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
        mapper = TextMapper(ShenWan.margin_flow, hand_dict)
        flow_list = mapper.map(content_list)
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            trade_status = str_check(flow['trade_status'])
            assert '成交' in trade_status, str(flow)
            # assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            flow['trade_name'] = trade_class
            if trade_class in ('买入', '融资买入'):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
                flow['trade_class'] = '担保'
            elif trade_class in ('卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
                flow['trade_class'] = '担保'
            else:
                raise NotImplementedError(flow)
        confirm_margin_trade_flow_list(flow_list)
        return flow_list
