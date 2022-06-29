# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import re
import xlrd

from trade.Interface import AbstractLoader
from trade.Checker import *


class HuaChuang(AbstractLoader):
    normal_flow = {
        'trade_time': ['成交时间', ],
        'security_code': ['证券代码', ],
        'security_name': ['证券名称', ],
        'trade_class': ['操作', ],
        'trade_volume': ['成交数量', ],
        'trade_price': ['成交均价', ],
        'trade_amount': ['成交金额', ],
        # 'trade_name': ['成交类型', ], 'trade_status': ['成交状态', ],
        None: ['合同编号', '成交编号', '撤单数量', '申报编号', ]
    }
