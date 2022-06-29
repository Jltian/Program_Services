# -*- encoding: UTF-8 -*-
import os
import re
import datetime
import xlrd
import shutil

from Abstracts import AbstractInstitution

from Checker import *


class GuangFa(AbstractInstitution):
    valuation_line = {
        # 'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['币种', ],
        # 'exchange_rate': ['汇率', ], 'hold_volume': ['数量', ], 'average_cost': ['单位成本', ],
        # 'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价', '收市价', ],
        # 'market_value': ['市值-本币', '市值', '市值本币'], 'value_changed': ['估值增值-本币', '估值增值本币', '估值增值'],
        # 'suspension_info': ['停牌信息', ],
        # 'None': [
        #     '成本占比', '市值占比', '权益信息', '市值占净值', '成本占净值',
        #     ],
        'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['数量', ],
        'exchange_rate': ['单位成本', ], 'hold_volume': ['成本', ], 'average_cost': ['单位成本', ],
        'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价', '收市价', ],
        'total_market_value': ['市值-本币', '市值', '市值本币'],
        'None': [
            '成本占比', '市值占比', '估值增值-本币', '停牌信息', '权益信息', '市值占净值', '成本占净值', '估值增值', '估值增值本币',
        ]
    }

    @staticmethod
    def load_valuation_table(file_path: str):
        from jetend.Constants import PRODUCT_CODE_NAME_MAP
        from jetend.structures import ExcelMapper
        from utils import identify_valuation_records
        file_name = file_path.split(os.path.sep)[-1]
        GuangFa.log.debug_running('读取托管估值表', file_name)
        # 文件名：SY0689久铭10号私募证券投资基金委托资产资产估值表20190831 SCJ125久铭50指数私募基金委托资产资产估值表20190831
        product_id, product, date_str = code, name, date = re.search(r'(STV732)-(静久康铭2号)私募\w+-4-(\d+)',
                                                                     file_name).groups()
        product_code, product_name = product_id, PRODUCT_CODE_NAME_MAP[product_id]
        date = datetime.datetime.strptime(date_str, '%Y%m%d')
        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '广发证券',
        }
        mapper = ExcelMapper(GuangFa.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)
