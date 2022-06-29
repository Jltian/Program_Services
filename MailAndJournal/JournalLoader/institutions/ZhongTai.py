# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import xlrd

from Abstracts import AbstractInstitution
from Checker import *


class ZhongTai(AbstractInstitution):
    """中泰"""
    folder_institution_map = {
        '中泰普通账户': '中泰', '中泰期权账户': '中泰',
    }
    normal_pos = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'hold_volume': ['当前余额', ],
        'market_value': ['证券市值', ],  'close_price': ['最新价', ], 'total_cost': ['参考成本', ],
        'None': ['可用数量', '参考盈亏', '参考成本价格', '盈亏金额', '实时余额', ],
    }

    normal_flow = {
        'date': ['日期', ], 'trade_class': ['业务标志', ],  'security_code': ['证券代码', ],
        'security_name': ['证券名称', ], 'trade_price': ['价格', ], 'trade_volume': ['发生数', ],
        'cash_move': ['发生金额', ],
        'None': ['银行', '资金余额', '手续费', '印花税', '过户费', '备注', ],
    }
    normal_acc = {
        'cash_amount': ['当前余额', ], 'market_sum': ['当前市值', ], 'capital_sum': ['总资产', ],
        'None': ['当前可用', '实时余额', '币种', ],
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            ZhongTai.log.info_running(folder_name, file_name)
            # loader.log.info_running(folder, text_file)
            if file_name.startswith('.'):
                continue

            elif file_name.endswith('TXT'):
                product_name, date_str = re.match(r'\d*(\w+\d+[号指数]+)[^\d]*(\d+)', file_name).groups()
                # print(product_name)
                if len(product_name) != 2:
                    assert isinstance(product_name, str)
                    product_name = product_name.replace('久铭', '')
                if product_name == '稳健10号':
                    product_name = '久铭10号'
                    date_str = ''.join([date_str[:6], date_str[-2:]])

                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date.strftime('%Y%m%d'))
                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                identified_dict = {
                    'date': date, 'product': product_name,
                    'institution': ZhongTai.folder_institution_map[folder_name],
                    'account_type': folder_name, 'currency': 'RMB', 'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                matcher = TextMapper(ZhongTai.normal_flow, identified_dict)
                matcher.set_line_sep('│')
                matcher.ignore_line.update(['合计'])
                flow = re.search(r"资产交割([\w\W]*)证券资产", content, re.M).groups()
                assert len(flow) == 1, 'wrong re implication'
                flow_list = matcher.map(flow[0])
                result_dict[product_name]['flow'] = flow_list

                matcher = TextMapper(ZhongTai.normal_pos, identified_dict)
                matcher.set_line_sep('│')
                pos = re.search(r"证券资产([\w\W]*)质押券", content, re.M).groups()
                assert len(pos) == 1, 'wrong re implication'
                pos_list = matcher.map(pos[0])
                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(ZhongTai.normal_acc, identified_dict)
                matcher.set_line_sep('│')
                acc = re.search(r"资产信息([\w\W]*)│美", content, re.M).groups()
                assert len(pos) == 1, 'wrong re implication'
                acc_obj = matcher.map(acc[0])[0]
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.endswith('pdf'):
                os.remove(os.path.join(folder_path, file_name))
            elif file_name.endswith('xlsx'):
                os.remove(os.path.join(folder_path, file_name))
            elif file_name.lower().endswith('rar'):
                if '招商证券' in file_name and '久铭10号' in file_name:
                    os.remove(os.path.join(folder_path, file_name))
                else:
                    raise NotImplementedError('存在压缩文件 {} 请确认内容已解压缩'.format(file_name))

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('txt'):
                product_name = re.match(r"([久铭稳健]+\d+[号指数]+)期权", file_name).group(1)
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name

            elif file_name.lower().endswith('rar'):
                os.remove(os.path.join(folder_path, file_name))

            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map

    valuation_line = {
        'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['币种', ],
        'exchange_rate': ['汇率', ], 'hold_volume': ['数量', ], 'average_cost': ['单位成本', ],
        'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价'],
        'total_market_value': ['市值-本币', '市值', '市值本币'],
        'None': [
            '成本占比', '市值占比', '估值增值-本币', '停牌信息', '权益信息', '市值占净值', '成本占净值', '估值增值', '估值增值本币',
        ]
    }

    @staticmethod
    def load_valuation_table(file_path: str):
        from jetend.structures import ExcelMapper
        from utils import identify_valuation_records
        file_name = file_path.split(os.path.sep)[-1]
        ZhongTai.log.debug_running('读取托管估值表', file_name)
        # 文件名：估值表_久铭8号私募证券投资基金_20190831
        if '久铭8号' not in file_name:
            raise NotImplementedError(file_name)
        if file_name.count('-') > 1:
            product, date_str = re.search(r'\w+_(\w+)_(\d+-\d+-\d+)', file_name).groups()
        else:
            product, date_str = re.search(r'\w+_(\w+)_(\d+)', file_name).groups()
        if '-' in date_str:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date = datetime.datetime.strptime(date_str, '%Y%m%d')
        product_code, product_name = 'SX4199', '久铭8号'

        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '中泰证券',
        }
        mapper = ExcelMapper(ZhongTai.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)


if __name__ == '__main__':
    from jetend.jmSheets import RawTrusteeshipValuation
    from jetend.structures import List

    folder = r'C:\Users\Administrator.SC-201606081350\Downloads\test\久铭8号'

    result_list = List()
    for file_name in os.listdir(folder):
        if file_name.startswith('.') or file_name.startswith('~'):
            continue
        # try:
        result_list.append(RawTrusteeshipValuation.from_dict(
            ZhongTai.load_valuation_table(os.path.join(folder, file_name))
        ))
        # except AssertionError:
        #     pass

    result_list.to_pd().to_csv('久铭8号 估值表提取页.csv', encoding='gb18030')
    # print(ZhongTai.load_normal(r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190627\中泰普通账户', datetime.date(2019, 6, 27)))
