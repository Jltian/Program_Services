# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import re
import xlrd

from core.Interface import AbstractLoader
from modules.Checker import *


class ZhongXin(AbstractLoader):

    normal_flow = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['买卖', ], 'trade_time': ['成交时间', ], 'trade_name': ['业务名称', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ],
        'trade_amount': ['成交金额', ], 'trade_status': ['成交状态', ],
        None: ['委托类型', '申请编号', '成交类型', '股东代码', '委托编号', '成交编号', ]
    }

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import TextMapper
        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '普通账户',
        }
        mapper = TextMapper(ZhongXin.normal_flow, hand_dict)
        mapper.set_line_sep('|')
        flow_list = mapper.map(content_text)
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            trade_status = str_check(flow['trade_status'])
            assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            if trade_class in ('买入',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list

    swap_normal_flow = {
        'security_code': ['标的代码', ], 'security_name': ['标的简称', ],
        'trade_class': ['买卖方向', ], 'trade_name': ['业务名称', ],
        'trade_volume': ['成交数量', ], 'trade_price': ['成交均价', ],
        'trade_amount': ['成交金额', ], 'trade_status': ['成交状态', ],
        'market_type': ['市场类型', ],
        None: ['委托数量', '委托金额', '委托次数', '撤单数量', '撤单次数', '操作人', ],
    }

    @staticmethod
    def load_swap_excel(file_path: str, product: str, date: datetime.date, account_type: str, ):
        from jetend.structures import ExcelMapper
        if account_type == '美股收益互换':
            institution, currency = '中信美股', 'USD'
        elif account_type == '港股收益互换':
            institution, currency = '中信港股', 'HKD'
        else:
            raise NotImplementedError(account_type)

        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': currency, 'account_type': '收益互换',
        }
        xls_content = xlrd.open_workbook(file_path, )

        mapper = ExcelMapper(ZhongXin.swap_normal_flow, hand_dict, )
        flow_list = mapper.map(xls_content.sheet_by_name('当日汇总'))
        for flow in flow_list:
            market_type = str_check(flow['market_type'])
            security_code = str_check(flow['security_code'])
            if market_type == '纳斯达克交易所':
                security_code = '.'.join([security_code.split(' ')[0], 'N'])
            elif market_type == '港交所':
                security_code = '.'.join([security_code.split(' ')[0], 'HK'])
            else:
                raise NotImplementedError(flow)
            flow['security_code'] = security_code
            trade_class = str_check(flow['trade_class'])
            if trade_class in ('买入',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
            flow['trade_name'] = trade_class
        confirm_normal_trade_flow_list(flow_list)
        return flow_list

    # @staticmethod
    # def load_simple_normal(file_path: str, product: str, date: datetime.date, institution: str, ):
    #     from jetend.structures import TextMapper
    #     content_list = list()
    #     content_file = open(file_path, mode='r', ).read()
    #     for content_line in content_file.split('\n'):
    #         line_list = list()
    #         for content_cell in content_line.split('\t'):
    #             if re.match(r'=\"([\w\W]*)\"', content_cell):
    #                 line_list.append(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
    #                 # print(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
    #             elif len(re.sub(r'[\d.,]', '', content_cell)) == 0:
    #                 line_list.append(content_cell)
    #             elif len(re.sub(r'\W', '', content_cell)) == 0:
    #                 continue
    #             else:
    #                 raise NotImplementedError('{}\n{}'.format(content_cell, content_line))
    #         content_list.append(' '.join(line_list))
    #     content_list = '\n'.join(content_list)
    #
    #     hand_dict = {
    #         'product': product, 'date': date, 'institution': institution,
    #         'currency': 'RMB', 'account_type': '普通账户',
    #     }
    #     mapper = TextMapper(ZhongXin.normal_flow, hand_dict)
    #     flow_list = mapper.map(content_list)
    #     for flow in flow_list:
    #         trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
    #         flow['trade_time'] = trade_time
    #         trade_status = str_check(flow['trade_status'])
    #         assert trade_status == '成交', str(flow)
    #         trade_class = str_check(flow['trade_class'])
    #         if trade_class in ('买入', ):
    #             flow['trade_direction'] = TRADE_DIRECTION_BUY
    #         elif trade_class in ('卖出', ):
    #             flow['trade_direction'] = TRADE_DIRECTION_SELL
    #         else:
    #             raise NotImplementedError(flow)
    #     confirm_normal_trade_flow_list(flow_list)
    #     return flow_list

    # swap_normal_flow = {
    #     'security_code': ['标的代码', ], 'security_name': ['标的简称', ],
    #     'trade_class': ['买卖方向', ], 'trade_name': ['业务名称', ],
    #     'trade_volume': ['成交数量', ], 'trade_price': ['成交均价', ],
    #     'trade_amount': ['成交金额', ], 'trade_status': ['成交状态', ],
    #     'market_type': ['市场类型', ],
    #     None: ['委托数量', '委托金额', '委托次数', '撤单数量', '撤单次数', '操作人', ],
    # }
    #
    # @staticmethod
    # def load_swap_normal(file_path: str, product: str, date: datetime.date, account_type: str, ):
    #     from jetend.structures import ExcelMapper
    #     if account_type == '美股收益互换':
    #         institution, currency = '中信美股', 'USD'
    #     elif account_type == '港股收益互换':
    #         institution, currency = '中信港股', 'HKD'
    #     else:
    #         raise NotImplementedError(account_type)
    #
    #     hand_dict = {
    #         'product': product, 'date': date, 'institution': institution,
    #         'currency': currency, 'account_type': '收益互换',
    #     }
    #     xls_content = xlrd.open_workbook(file_path, )
    #
    #     mapper = ExcelMapper(ZhongXin.swap_normal_flow, hand_dict, )
    #     flow_list = mapper.map(xls_content.sheet_by_name('当日汇总'))
    #     for flow in flow_list:
    #         market_type = str_check(flow['market_type'])
    #         security_code = str_check(flow['security_code'])
    #         if market_type == '纳斯达克交易所':
    #             security_code = '.'.join([security_code.split(' ')[0], 'N'])
    #         else:
    #             raise NotImplementedError(flow)
    #         flow['security_code'] = security_code
    #         trade_class = str_check(flow['trade_class'])
    #         if trade_class in ('买入',):
    #             flow['trade_direction'] = TRADE_DIRECTION_BUY
    #         elif trade_class in ('卖出',):
    #             flow['trade_direction'] = TRADE_DIRECTION_SELL
    #         else:
    #             raise NotImplementedError(flow)
    #         flow['trade_name'] = trade_class
    #     confirm_normal_trade_flow_list(flow_list)
    #     return flow_list

    margin_flow = {
        'trade_time': ['成交时间', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['买卖', ], 'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ],
        'trade_amount': ['成交金额', ], 'trade_name': ['业务名称', ], 'trade_status': ['成交状态', ],
        None: ['申请编号', '委托类型', '成交类型', '股东代码', '委托编号', '成交编号', ]
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
                    line_list.append(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
                    # print(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
                elif len(re.sub(r'[\d.,]', '', content_cell)) == 0:
                    line_list.append(content_cell)
                elif len(re.sub(r'\W', '', content_cell)) == 0:
                    continue
                else:
                    raise NotImplementedError('{}\n{}'.format(content_cell, content_line))
            content_list.append(' '.join(line_list))
        content_list = '\n'.join(content_list)

        hand_dict = {
            'product': product, 'date': date, 'institution': institution,
            'currency': 'RMB', 'account_type': '两融账户',
        }
        mapper = TextMapper(ZhongXin.normal_flow, hand_dict)
        flow_list = mapper.map(content_list)
        for flow in flow_list:
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            trade_status = str_check(flow['trade_status'])
            assert trade_status == '成交', str(flow)
            trade_class = str_check(flow['trade_class'])
            if trade_class in ('买入',):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出',):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list


if __name__ == '__main__':
    ZhongXin.load_simple_normal(
        r'C:\NutStore\我的坚果云\持仓资金工作流程\当日成交\当日成交20190305\久铭2号股票中信证券.xls',
        '久铭2号', datetime.date(2019, 3, 5), '中信',
    )
