# -*- encoding: UTF-8 -*-
import xlrd

from jetend.structures import ExcelMapper

valuation_line = {
    'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['币种', ],
    'exchange_rate': ['汇率', ], 'hold_volume': ['数量', ], 'average_cost': ['单位成本', ],
    'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价'],
    'total_market_value': ['市值-本币', '市值', '市值本币'],
    'None': [
        '成本占比', '市值占比', '估值增值-本币', '停牌信息', '权益信息', '市值占净值', '成本占净值', '估值增值', '估值增值本币',
    ]}

hand_dict = {
            'product_code': 'SL0768', 'product_name': '稳健5号', 'date': '20220420',
            'file_name': 'SL0768_久铭稳健5号私募证券投资基金资产估值表_2022-04-20.xlsx', 'institution': '久铭机构',
        }
file_path = r'D:\Users\my_python_workspace\MailAndJournal\JournalLoader\interface\SL0768_久铭稳健5号私募证券投资基金资产估值表_2022-04-20.xlsx'
mapper = ExcelMapper(valuation_line, hand_dict, )
mapper.set_duplicated_tolerance(True).set_force_vertical(True)
m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
for  m in m_list:
    print(m)