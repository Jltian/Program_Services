# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import xlrd

from Abstracts import AbstractInstitution
from Checker import *


class XingYe(AbstractInstitution):
    """兴业"""
    folder_institution_map = {
        '兴业普通账户': '兴业', '兴业期权账户': '兴业期权',
    }

    normal_pos = {
        'shareholder_code': ['股东帐号', '股东账号', ], 'security_code': ['证券代码', ], 'security_name': ['股票名称', ],
        'hold_volume': ['当前数', ], 'market_value': ['市值', ], 'close_price': ['最新价', ],
        'weight_average_cost': ['成本价'], 'currency': ['币种', ],
        'None': ['盈亏金额', '市值价', ],
    }
    normal_flow = {
        'shareholder_code': ['股东帐号'],
        'security_code': ['证券代码', ], 'security_name': ['股票名称', ],
        'trade_class': ['业务标志', ], 'trade_volume': ['发生数量', ], 'trade_price': ['成交均价', ],
        'cash_move': ['收付金额', ],
        'None': ['日期', '佣金', '印花税', '其他费', '备注信息', '资金余额', '币种', '备注信息', '股东帐号']
    }
    normal_acc = {
        'capital_account': ['资金帐号', '资金账号', ], 'customer_id': ['客户编号', ],
        'capital_sum': ['资产总值', '市值', ], 'cash_amount': ['资金余额', ], 'currency': ['币种', ]
    }
    normal_id_product_map = {
        '1880000381': '久铭7号', '380064097': '稳健7号', '1633051223': '久铭2号', '1780006743': '久铭2号',
        '1780008557': '创新稳健1号', '1780010375': '创新稳健2号', '1780013239': '创新稳健5号', '1780011203': '久铭5号',
        '1780019591': '创新稳健6号', '1780019592': '全球丰收1号','2880005122': '专享17号','160083361':'创新稳禄1号','160083656':'专享29号'
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper, TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            XingYe.log.debug_running(file_name)
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.endswith('pdf'):
                # TODO: 暂时不读PDF
                continue
            elif '副本' in file_name:
                continue
            elif file_name.endswith('txt'):
                pro_id = re.match(r"(\d+)", file_name).group(1)
                product_name = XingYe.normal_id_product_map[pro_id]
                try:
                    content = open(
                        os.path.join(folder_path, file_name), mode='r', encoding='gb18030',
                    ).read()
                except UnicodeDecodeError:
                    content = open(
                        os.path.join(folder_path, file_name), mode='r', encoding='utf-8',
                    ).read()
                # XingYe.log.debug(content)
                identified_dict = {
                    'date': date, 'product': product_name,
                    'institution': XingYe.folder_institution_map[folder_name],
                    'account_type': folder_name, 'currency': 'RMB', 'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                matcher = TextMapper(XingYe.normal_flow, identified_dict)
                matcher.set_right_align(True)
                matcher.map_horizontal(content)
                matcher.ignore_line.update(['合计'])
                try:
                    flow = re.search(r"流水明细([\w\W]+)证券理财交割流水", content, re.M).group(1)
                except AttributeError:
                    try:
                        flow = re.search(r"流水明细([\w\W]+)汇总股票资料", content, re.M).group(1)
                    except AttributeError:
                        flow = ''
                flow_list = matcher.map(clear_str_content(flow))

                for flow_obj in flow_list:
                    if flow_obj['security_name'] == '大秦铁路':
                        flow_obj['security_code'] = '601006.SH'
                    elif flow_obj['security_name'] == '歌尔股份':
                        flow_obj['security_code'] = '002241.SZ'

                result_dict[product_name]['flow'] = flow_list

                matcher = TextMapper(XingYe.normal_pos, identified_dict)
                matcher.set_duplicated_tolerance(True).set_right_align(True)
                # matcher.map_horizontal(content)
                # TODO： 这三个日期怎么回事
                # 读持仓的时候。发现18年这三个对账单持仓内容下面字体内容不一样
                # if date < datetime.date(2018, 5, 8):
                #     pos = re.findall(r"股票资料[^，]+(?=证券理财资料)", content, re.M)
                # else:
                #     pos = re.findall(r"股票资料[^，]+(?=证券理财资料)", content, re.M)
                pos = re.findall(r"(?<!汇总)股票资料([\w\W]+)[^未回](?=流水明细)", content, re.M)
                # if len(pos) == 0:
                #     pos = re.findall(r"(?<!汇总)股票资料([\w\W]+)(?=人民币市值)", content, re.M)

                if len(pos) == 1:
                    XingYe.log.debug(pos[0])
                    pos_list = matcher.map(clear_str_content(pos[0]))
                elif len(pos) == 0:
                    pos_list = list()
                else:
                    raise RuntimeError('wrong re implication\n{}'.format(pos))

                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(XingYe.normal_acc, identified_dict)
                matcher.set_duplicated_tolerance(True).set_right_align(True)
                matcher.map_horizontal(content)
                try:
                    acc = re.search(r"资金信息:([\w\W]+)[^汇总]+股票资料:", content, re.M).group(1)
                except AttributeError:
                    try:
                        acc = re.search(r"客户风险等级:([\w\W]+)对帐日期:", content, re.M).group(1)
                    except AttributeError:
                        acc = re.search(r"资金信息:([\w\W]+)", content, re.M).group(1)
                acc_obj = matcher.map(acc)[0]
                if 'market_sum' not in acc_obj:
                    acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('xls'):
                product_name, date_str = re.match(r'(\w+)-(\d+)', file_name).groups()
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': XingYe.folder_institution_map[folder_name],
                    'account_type': folder_name, 'currency': 'RMB', 'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                matcher = ExcelMapper(XingYe.normal_flow, identified_dict, )
                try:
                    matcher.set_start_line('流水明细').set_end_line('汇总股票资料')
                    matcher.ignore_line.update(['合计'])
                    flow_list = matcher.map(content.sheet_by_name('对账单'))
                except RuntimeError:
                    # 解决当天无流水导致append数据类型出错的错误
                    flow_list = []
                result_dict[product_name]['flow'] = flow_list

                try:
                    matcher = ExcelMapper(XingYe.normal_pos, identified_dict, )
                    matcher.set_start_line('股票资料').set_end_line('流水明细')
                    pos_list = matcher.map(content.sheet_by_name('对账单'))
                except RuntimeWarning:
                    matcher = ExcelMapper(XingYe.normal_pos, identified_dict, )
                    matcher.set_start_line('股票资料').set_end_line('股票汇总资料')
                    pos_list = matcher.map(content.sheet_by_name('对账单'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(XingYe.normal_acc, identified_dict, )
                matcher.set_start_line('风险等级到期时间').set_end_line('股票资料')
                acc_obj = matcher.map(content.sheet_by_name('对账单'))[0]
                if 'market_sum' not in acc_obj:
                    acc_obj['market_sum'] = float_check(acc_obj['capital_sum']) - float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('.rar'):
                os.remove(os.path.join(folder_path, file_name))

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    option_pos = {
        'security_code': ['期权合约代码', ], 'security_name': ['期权合约名称', ],
        'warehouse_class': ['持仓类别', ], 'warehouse_volume': ['当前数量', ],  # 'warehouse_cost': ['', ],
        'settlement_price': ['结算价', ], 'hold_volume': ['当前数量', ],
        'market_value': ['持仓市值', ],
        'None': ['交易类别', '期权类别', '可用数量'],
    }
    option_acc = {
        'cash_amount': ['现金资产', ], 'market_sum': ['期权市值', ], 'capital_sum': ['总权益', ],
        'cash_available': ['当前余额', ],
        'None': ['冻结金额', '已用保证金', '可用保证金', '币种'],
    }
    option_flow = {
        'security_code': ['期权合约代码', ], 'security_name': ['期权合约名称', ],
        'warehouse_class': ['持仓类别', ], 'trade_class': ['买卖方向', ], 'offset': ['开平仓方向', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
        'trade_fee': ['手续费', ], 'cash_rest': ['当前余额', ], 'reserve_tag': ['备兑标志', ],
        'None': ['发生日期', '交易类别', '证券代码', '证券名称', ],
    }
    option_acc_flow = {
        'trade_class': ['业务标志', ], 'cash_move': ['发生金额', ], 'cash_rest': ['后资金额', ],
        'None': ['发生日期', '当前时间', '币种类别', ]
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        id_product_map = {
            '1888400002': '久铭7号', '1788400145': '创新稳健5号', '1788400153': '全球丰收1号',
            '1788400155': '创新稳健6号', '1788400157': '创新稳健2号',
        }
        for file_name in os.listdir(folder_path):
            XingYe.log.debug(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('txt'):
                pro_id = re.search(r"(\d+)", file_name).group(1)
                product_name = id_product_map[pro_id]

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                identified_dict = {
                    'date': date, 'product': product_name, 'currency': 'RMB', 'account_type': folder_name,
                    'institution': XingYe.folder_institution_map[folder_name],
                }

                matcher = TextMapper(XingYe.option_acc, identified_dict)
                acc = re.search(r"资金信息([\w\W]*)资金变动清单", content, re.M).group(1)
                acc_obj = matcher.map(acc)[0]
                result_dict[product_name]['account'] = acc_obj

                matcher = TextMapper(XingYe.option_pos, identified_dict)
                matcher.ignore_cell.update(['成本价'])
                matcher.ignore_line.update(['合计'])
                pos = re.search(r"合约持仓清单([\w\W]*)获取对账单", content, re.M).group(1)
                pos_list = matcher.map(pos)
                for pos_obj in pos_list:
                    pos_obj['average_cost'] = pos_obj['settlement_price']
                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(XingYe.option_flow, identified_dict)
                flow = re.search(r"获取对账单([\w\W]*)组合持仓清单", content, re.M).group(1)
                matcher.ignore_line.update(['合计'])
                flow_list = matcher.map(flow)
                for flow_obj in flow_list:
                    assert 'trade_class' in flow_obj, flow_obj
                    if str_check(flow_obj['trade_class']) in ('买',) and str_check(flow_obj['offset']) in ('开仓',):
                        flow_obj['cash_move'] = - abs(
                            float_check(flow_obj['trade_amount'])
                        ) - abs(float_check(flow_obj['trade_fee']))
                    else:
                        flow_obj['cash_move'] = abs(
                            float_check(flow_obj['trade_amount'])
                        ) - abs(float_check(flow_obj['trade_fee']))
                result_dict[product_name]['flow'] = flow_list

                # matcher = TextMapper(XingYe.option_acc_flow, identified_dict)
                # flow = re.search(r"资金变动清单([\w\W]*)合约持仓清单", content, re.M).group(1)
                # matcher.ignore_line.update(['合计'])
                # # for acc_flow in matcher.map(flow):
                # #     assert isinstance(acc_flow, RawOptionFlow)
                # #     acc_flow.trade_price = acc_flow.cash_move
                # #     acc_flow.trade_volume = 1
                # #     flow_list.append(acc_flow)
                # #
                # # pos_list = DataList(RawOptionPosition)

                confirm_option_flow_list(flow_list)
                # match_option_pos_acc(pos_list, acc_obj)
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
        from jetend.Constants import PRODUCT_CODE_NAME_MAP
        from jetend.structures import ExcelMapper
        from utils import identify_valuation_records
        file_name = file_path.split(os.path.sep)[-1]
        XingYe.log.debug_running('读取托管估值表', file_name)
        # 文件名：2019-08-31_(XY0886)久铭7号私募证券投资基金_证券投资基金估值表
        product_id_code_map = {
            'XY0886': 'ST6278', 'XY6305': 'SQS949', 'XY6307': 'SQS945', 'XY6308': 'SQS948', 'XY6309': 'SQS941',
            'SQS941': 'SQS941', 'SQS949':'SQS949',
            'XY6306': 'SQS944','SLN700':'SLN700',
        }
        try:
            date_str, pro_id, product = re.match(
                r'(\d+-\d+-\d+)_\(([A-Za-z0-9]+)\)(\w+)私募证券投资基金', file_name
            ).groups()
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except AttributeError:
            try:
                date_str, pro_id, product = re.match(
                    r'(\d+)_\(([A-Za-z0-9]+)\)(\w+)私募证券投资基金', file_name
                ).groups()
                date = datetime.datetime.strptime(date_str, '%Y%m%d')
            except AttributeError:
                try:
                    pro_id, product, date_str = re.search(r'([A-Za-z0-9]+)_久铭(\w+)私募[^\d]+(\d+)', file_name).groups()
                    date = datetime.datetime.strptime(date_str, '%Y%m%d')  # @waves
                except Exception:
                    code, name, date = re.search(r'([A-Za-z0-9]+)_(\w+)私募\w+_(\d+-\d+-\d+)', file_name).groups()
                    date = "".join(str(date).split('-'))
                    date = datetime.datetime.strptime(date, '%Y%m%d')
        product_code = product_id_code_map[pro_id]
        product_name = PRODUCT_CODE_NAME_MAP[product_code]

        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '兴业证券',
        }
        mapper = ExcelMapper(XingYe.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)


if __name__ == '__main__':
    print(XingYe.load_normal(r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190626\兴业普通账户', datetime.date(2019, 6, 26)))
