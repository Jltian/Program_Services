# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import xlrd

from trade.Interface import AbstractLoader
from trade.Checker import *


class ChangAn(AbstractLoader):

    normal_flow = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'trade_class': ['委托方向', ],
        'trade_time': ['成交时间', ], 'trade_volume': ['成交数量', ], 'trade_price': ['成交均价', ],
        'trade_amount': ['成交金额', ], 'cash_move': ['清算金额', ],
        # 'trade_name': ['业务名称', ], 'trade_status': ['状态说明', ],
        'currency': ['币种', ],
        None: [
            '成交序号', '基金名称', '单元', '组合编号', '组合名称', '交易员编号', '交易员姓名', '是否备兑', '业务分类',
            '投资类型', '业务日期', '成交均价全价', '成本价', '佣金', '印花税', '过户费', '全额过户费', '交易费',
            '经手费', '证管费', '结算费', '交割费', '其他费', '委托序号', '下达人编号', '下达人姓名', '委托来源',
        ]
    }
    currency_map = {'人民币': 'RMB', '港币（深）': 'HKD', }

    @staticmethod
    def load_normal_excel(file_path: str, product: str, date: datetime.date, institution: str):
        from jetend.structures import ExcelMapper
        hand_dict = {
            'product': '浦睿1号', 'date': date, 'institution': '长安',
            'account_type': '普通账户',
        }
        xls_content = xlrd.open_workbook(file_path, encoding_override='gb18030')
        mapper = ExcelMapper(ChangAn.normal_flow, hand_dict)
        flow_list = list()

        for flow in mapper.map(xls_content.sheet_by_index(0)):
            trade_class = str_check(flow['trade_class'])
            if trade_class == '':
                continue
            currency = str_check(flow['currency'])
            try:
                flow['currency'] = ChangAn.currency_map[currency]
            except KeyError as key_error:
                print(flow)
                raise key_error
            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
            flow['trade_time'] = trade_time
            flow['trade_name'] = str_check(flow['trade_class'])
            # trade_status = str_check(flow['trade_status'])
            # assert trade_status == '成交', str(flow)
            flow['trade_status'] = trade_class
            if trade_class in ('买入', '证券买入', '债券买入', ):
                flow['trade_direction'] = TRADE_DIRECTION_BUY
            elif trade_class in ('卖出', '证券卖出', '债券卖出', ):
                flow['trade_direction'] = TRADE_DIRECTION_SELL
            else:
                raise NotImplementedError(flow)
            flow_list.append(flow)
        confirm_normal_trade_flow_list(flow_list)
        return flow_list
