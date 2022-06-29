# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import re

from pandas import DataFrame

from jetend import get_logger


class AbstractLoader:
    # __log__ = None
    log = get_logger('LoaderPart', )
    normal_flow = {}
    future_flow = {}
    option_flow = {}

    # @staticmethod
    # def load_simple_normal(file_path: str, product: str, date: datetime.date, institution: str, ):
    #     raise NotImplementedError

    @staticmethod
    def root_path():
        from os import path
        file_path = path.abspath(path.dirname(__file__)).split(path.sep)
        file_path.pop(-1)
        file_path = path.sep.join(file_path)
        return file_path

    # normal_flow = {
    #     'trade_time': ['成交时间', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
    #     'trade_class': ['买卖标志', ], 'trade_status': ['状态说明', '成交状态', ],
    #     'trade_price': ['成交价格', '成交价格港币', ], 'trade_volume': ['成交数量', ],
    #     'trade_amount': ['成交金额', ],
    #     # 'trade_name': ['业务名称', ],
    #     None: ['成交编号', '委托编号', '股东代码', ]
    # }

    @staticmethod
    def convert_column_map(dict_list: list, column_flow_map: dict):
        """
        dict_list: 需要转换的数据列
        normal_flow: 匹配列名的规则
        """
        convert_map = dict()
        for k, v in column_flow_map.items():
            assert isinstance(v, list), '{}\n{}'.format(v, column_flow_map)
            for item in v:
                convert_map[item] = k
        converted_list = list()
        for flow in dict_list:
            new_flow = dict()
            for k in flow.keys():
                cleaned_key = re.sub('\W', '', k)
                if cleaned_key in convert_map:
                    new_flow[convert_map[cleaned_key]] = flow[k]
                else:
                    raise KeyError('Key {} origin: {} NOT FOUND'.format(cleaned_key, k))
            converted_list.append(new_flow)
        return converted_list

    @staticmethod
    def load_swap_excel(file_path: str, product: str, date: datetime.date, account_type: str, ):
        raise NotImplementedError

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        raise NotImplementedError

    @staticmethod
    def load_normal_excel(file_path: str, product: str, date: datetime.date, institution: str):
        raise NotImplementedError

    @staticmethod
    def load_simple_margin(file_path: str, product: str, date: datetime.date, institution: str, ):
        raise NotImplementedError

    @staticmethod
    def load_margin_excel(file_path: str, product: str, date: datetime.date, institution: str):
        raise NotImplementedError

    @staticmethod
    def load_future_excel(file_path: str, product: str, date: datetime.date, institution: str):
        raise NotImplementedError

    @staticmethod
    def load_future_csv(file_path: str, product: str, date: datetime.date, institution: str):
        raise NotImplementedError

    # @property
    # def log(self):
    #     from jetend.structures import LogWrapper
    #     if not isinstance(AbstractLoader.__log__, LogWrapper):
    #         from jetend import get_logger
    #         AbstractLoader.__log__ = get_logger('LoaderPart', )
    #     logger = AbstractLoader.__log__
    #     assert isinstance(logger, LogWrapper)
    #     return logger
