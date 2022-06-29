# -*- encoding: UTF-8 -*-
import datetime
import os
import re

from Abstracts import AbstractInstitution
from Checker import *


class CaiTong(AbstractInstitution):
    """财通"""
    folder_institution_map = {
        '财通普通账户': '财通',
    }

    # =================================== =================================== #
    normal_pos = {
        'shareholder_code': ['股东帐号', ], 'security_code': ['证券代码', ], 'security_name': ['股票名称', ],
        'hold_volume': ['当前数', ], 'market_value': ['市值', ], 'close_price': ['最新价', ],
        'weight_average_cost': ['成本价'], 'currency': ['币种', ],
        'None': ['盈亏金额', ],
    }
    normal_flow = {
        'currency': ['币种', ], 'shareholder_code': ['股东帐号', '股东账号'],
        'security_code': ['股票代码', ], 'security_name': ['股票名称', ],
        'trade_class': ['业务标志', ], 'trade_volume': ['发生数量', ],
        'trade_price': ['成交均价', ],  'cash_move': ['收付金额', ],
        'None': ['日期', '佣金', '印花税', '其他费', '资金余额', '备注信息']

    }
    hk_flow = {
        'currency': ['币种', ], 'shareholder_code': ['股东帐号', '股东账号'],
        'security_name': ['股票名称', ], 'trade_class': ['业务标志', ],
        'trade_volume': ['发生数量', ], 'trade_price': ['成交均价', ], 'cash_move': ['收付金额', ],
        'None': ['日期', '佣金', '印花税', '其他费', '资金余额', '备注信息']
    }

    normal_acc = {
        'currency': ['币种', ], 'cash_amount': ['资金余额', ], 'capital_sum': ['资产总值', ],
        'market_sum': ['资产市值', ],
        # 'None': ['当前可用', '实时余额'],
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        """
            读取普通账户对账单
            返回读取到的数据结果：
            {
                product: {
                    'account': dict()  # 账户信息，单个包含信息的字典对象
                    'flow': list(dict, )   # 流水信息，包含信息的流水字典对象组成的列表
                    'position': list(dict, )   # 持仓信息
                }
            }
        :return:
        """
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            CaiTong.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.endswith('txt'):
                try:
                    product_name, date_str = re.match(r"\d+([^\d]+\d+号[指数]*)[对账单]*(\d+)", file_name).groups()
                    print(date_str)
                # product_name = loader.env.product_name_map[product_name]
                except AttributeError:
                    try:
                        product_name, date_str = re.match(r"([^\d]+\d+号[指数]*)[对账单]*(\d+)", file_name).groups()
                    except AttributeError:
                        product_name, date_str,= re.match(r"\d+([^\d]+\d+号[指数]*)[对账单]*-\d+-[账户对账单]+-(\d+)", file_name).groups()
                if len(product_name) != 4:
                    assert isinstance(product_name, str)
                    product_name = product_name.replace('-久铭', '')
                assert product_name in PRODUCT_NAME_RANGE, product_name
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                identified_dict = {
                    'date': date, 'product': product_name, 'account_type': folder_name,
                    'institution': CaiTong.folder_institution_map[folder_name],
                }
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                # 流水
                matcher = TextMapper(CaiTong.normal_flow, identified_dict, )
                matcher.ignore_line.update(['合计'])
                try:
                    flow = re.search(r"流水明细([\w\W]*)未回业务流水明细:", content, re.M).group(1)
                    flow_list = matcher.map(flow)
                    matcher = TextMapper(CaiTong.hk_flow, identified_dict, )
                    matcher.ignore_line.update(['合计'])
                    flow = re.search(r"未回业务流水明细:([\w\W]*)汇总股票资料:", content, re.M).group(1)
                    flow_list.extend(matcher.map(flow.replace(':', '-').replace('：', '-')))
                except AttributeError:
                    try:
                        flow = re.search(r"流水明细([\w\W]*)汇总股票资料:", content, re.M).group(1)
                        flow_list = matcher.map(flow)
                    except AttributeError:
                        try:
                            flow = re.search(r"流水明细([\w\W]*)流水汇总", content, re.M).group(1)
                            flow_list = matcher.map(flow)
                        except AttributeError:
                            flow_list = matcher.map('')
                result_dict[product_name]['flow'] = flow_list

                # 持仓
                matcher = TextMapper(CaiTong.normal_pos, identified_dict)
                try:
                    pos = re.search(r"股票资料([\w\W]*)港币市值[\w\W]*汇总股票资料", content, re.M).group(1)
                except AttributeError:
                    pos = ''
                pos_list = matcher.map(pos)
                result_dict[product_name]['position'] = pos_list

                # 资金
                matcher = TextMapper(CaiTong.normal_acc, identified_dict, )
                try:
                    acc = re.search(r"风险等级到期时间([\w\W]+)[^汇总]+股票资料", content, re.M).group(1)
                except AttributeError:
                    try:
                        acc = re.search(r"风险等级到期时间([\w\W]+)流水明细", content, re.M).group(1)
                    except AttributeError:
                        try:
                            acc = re.search(r"风险等级到期时间([\w\W]+)", content, re.M).group(1)
                        except AttributeError:
                            acc = re.search(r"04月17日([\w\W]+)", content, re.M).group(1)
                acc_obj = matcher.map(acc)[0]
                if 'market_sum' not in acc_obj:
                    acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('rar'):
                os.remove(os.path.join(folder_path, file_name))

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map


if __name__ == '__main__':
    print(CaiTong.load_normal(
        r'D:\Documents\久铭产品交割单20190621-sp\久铭产品交割单20190621-sp\财通普通账户',
        datetime.date(2019, 6, 21)
    ))
