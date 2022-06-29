# -*- encoding: UTF-8 -*-
import os
import re
import xlrd
import datetime


from Abstracts import AbstractInstitution
from Checker import *

# TODO: 读取出入境
# class ChuRuJin(LoadObject):
#     # 期货出入金
#     inout_flow = {
#         'in_cash': ['入金', ], 'out_cash': ['出金', ], 'trade_class': ['业务类型', ],
#         'None': ['流水号', '交易所', '银行', '发生日期']
#     }
#     def __init__(self, trade_class: str = '', in_cash: float = None, out_cash: float = None, **kwargs):
#         LoadObject.__init__(self)
#         self.trade_class = str_check(trade_class)
#         self.in_cash = float_check(in_cash)
#         self.out_cash = float_check(out_cash)
#
#     def __repr__(self):
#         str_list = list()
#         for key in self.inner2outer_map.keys():
#             str_list.append('{}={}'.format(key, getattr(self, key)))
#         return self.__class__.__name__ + ': ' + ', '.join(str_list) + '; '
#
#     def check_loaded(self):
#         if not is_valid_float(self.in_cash):
#             return CheckResult(False, '入金信息遗失！')
#         if not is_valid_float(self.out_cash):
#             return CheckResult(False, '出金信息遗失！')
#         if not is_valid_str(self.trade_class):
#             return CheckResult(False, '类型信息遗失！')
#
#         return CheckResult(True, '')


class HaiTong(AbstractInstitution):
    """海通"""
    folder_institution_map = {
        '海通普通账户': '海通',
        '海通期货账户': '海通期货',
        '海通期权账户': '海通期权',
    }

    # =================================== =================================== #
    normal_pos = {
        'shareholder_code': ['股东代码', ],
        'security_code_name': ['证券代码简称', '股东代码证券代码简称', ], 'hold_volume': ['库存数', '持有数量', ],
        'security_code': ['证券代码', ], 'security_name': ['证券简称', ],
        'weight_average_cost': ['参考成本', ], 'close_price': ['最新价', ],
        'market_value': ['最新市值', ],
        'None': ['今买入价', '今买入数', '今卖出价', '今卖出数', '可用数量', '盈亏', '待交收数量', '市场', ]
    }
    normal_flow = {
        'shareholder_code': ['股东代码', ], 'security_code_name': ['证券代码简称', ],
        'security_code': ['证券代码'], 'trade_class': ['摘要', ],
        'trade_volume': ['成交数', ], 'trade_price': ['成交均价', ], 'cash_move': ['变动金额', ],
        'total_fee': ['交易费', ],
        'customer_id': ['客户号', ],
        'None': ['发生日期', '市场', '库存数', '资金余额', '过户费', '佣金', '印花税', ]
    }
    normal_acc = {
        'cash_amount': ['资金余额', '资产余额'], 'market_sum': ['市值合计', '参考总市值'],
        'capital_sum': ['资产合计', '总资产', ],
        'None': ['可用资金', '买入未过户金额', '卖出未过户金额', ]
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        # from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        id_product_map = {
            '173340': '收益2号', '177051': '久铭6号', '176871': '久铭1号',
            '0040173340': '收益2号', '0040177051': '久铭6号', '0040176871': '久铭1号',
        }
        for file_name in os.listdir(folder_path):
            HaiTong.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.endswith('txt'):
                if '期权' in file_name:
                    raise RuntimeError('{} 放错文件夹 {}'.format(file_name, folder_name))
                some_id = re.match(r'(\d+)', file_name).group(1)
                product_name = id_product_map[some_id]
                date_str = date.strftime('%Y%m%d')
                content = open(
                   os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                identified_dict = {
                   'date': date, 'product': product_name, 'currency': 'RMB',
                   'institution': HaiTong.folder_institution_map[folder_name],
                   'account_type': folder_name, 'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                # 流水
                matcher = TextMapper(HaiTong.normal_flow, identified_dict, )
                matcher.set_right_align(True)
                # matcher.ignore_cell.update([date_str, '沪A', '深A', '港股'])

                # 解决海通普通账户在这两日对账单格式变化的问题,if条件日期摘要里面有个空格
                if date_str in ['20190408', '20190401','20190816']:
                    try:
                        flow = re.search(r"变动明细([\w\W]+)", content).group(1)
                        if re.search(r"摘[ ]*要", flow):
                            flow = re.sub(r"摘[ ]*要", '摘要', flow)
                    except AttributeError:
                        flow = ''
                else:
                    try:
                        flow = re.search(r"承上日资金余额([\w\W]+)请注意：交易类资金变动的变动", content, re.M).group(1)
                    except AttributeError:
                        flow = ''
                flow_list = matcher.map(flow.replace('\u3000', ' '))
                result_dict[product_name]['flow'] = flow_list

                # 持仓
                matcher = TextMapper(HaiTong.normal_pos, identified_dict)
                matcher.set_right_align(True)
                # if os.path.exists(os.path.join(folder_path, '{}.xlsx'.format(some_id))):
                #      contentexcel = xlrd.open_workbook(os.path.join(folder_path, '{}.xlsx'.format(some_id)))
                #     matcher = ExcelMapper(HaiTong.normal_pos, identified_dict)
                #     position_sheet = 'Sheet1'
                #     pos_list = matcher.map(contentexcel.sheet_by_name(position_sheet))
                # else:
                #     matcher = TextMapper(HaiTong.normal_pos, identified_dict)
                #     matcher.set_duplicated_tolerance(True).set_right_align(True)

                # matcher.ignore_cell.update(['股东代码', ])
                # if loader.__date__ == datetime.date(2018, 1, 11):
                #     matcher.ignore_cell.update(['参考成本', ])
                if date_str in ['20190401', '20190408']:
                    try:
                        pos = re.search(r"持仓情况([\w\W]+)变动明细", content, re.M).group(1)
                        # pos_list = matcher.map(pos.replace('-', ' ').replace('\u3000', ' '))
                        # matcher = TextMapper(HaiTong.normal_pos, identified_dict)
                        # matcher.set_duplicated_tolerance(True).set_right_align(True)
                    except AttributeError:
                        try:
                            pos = re.search(r"持仓情况([\w\W]+)", content, re.M).group(1)
                            # pos_list = matcher.map(pos.replace('-', ' ').replace('\u3000', ' '))
                        except AttributeError:
                            pos = ''
                            # pos_list = matcher.map(pos.replace('-', ' ').replace('\u3000', ' '))
                else:
                    pos = ''
                pos_list = matcher.map(pos.replace('-', ' ').replace('\u3000', ' '))
                result_dict[product_name]['position'] = pos_list

                # 资金
                matcher = TextMapper(HaiTong.normal_acc, identified_dict)
                matcher.set_right_align(True)
                if date_str in['20190408', '20190401']:
                    acc = re.search(r"资产情况([\w\W]+参考总市值[\w\W]+)\t$", content, re.M).group(1)
                    matcher.map_horizontal(acc)
                    acc_obj = matcher.form_new()
                else:
                    try:
                        acc = re.search(r"以下为[^，]*人民币[^，]*资金情况([\w\W]+)注意：股票库存数为", content, re.M).group(1)
                    except AttributeError:
                        try:
                            acc = re.search(r"以下为人民币的资金情况([\w\W]+)注意：股票库存数为", content, re.M).group(1)
                        except AttributeError:
                            acc = re.search(r"注意：股票库存数为([\w\W]+)打印日期", content, re.M).group(1)
                    acc_obj = matcher.map(acc)[0]

                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    # =================================== =================================== #
    margin_acc = {
        'cash_amount': ['资金余额', ], 'market_sum': ['市值合计', ], 'capital_sum': ['资产合计', ],
        'None': ['可用资金', '买入未过户金额', '卖出未过户金额', ]
    }
    # @staticmethod
    # def load_margin(folder_path: str, date: datetime.date):
    #     from jetend.structures import TextMapper
    #     folder_name = folder_path.split(os.path.sep)[-1]
    #     result_dict = dict()
    #
    #     for file_name in os.listdir(folder_path):
    #         # loader.log.info_running(folder, text_file)
    #         if file_name.startswith('.'):
    #             continue
    #         elif file_name.endswith('txt'):
    #             product_name = re.match(r"([^\d]+\d+[号指数]+)", file_name).group(1)
    #             # product_name = loader.env.product_name_map[product_name]
    #             content = open(
    #                 os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
    #             ).read()
    #             identified_dict = {
    #                 'date': date, 'product': product_name,
    #                 'institution': HaiTong.folder_institution_map[folder_name],
    #                 'currency': 'RMB', 'account_type': folder_path,
    #             }
    #
    #             if product_name not in result_dict:
    #                 result_dict[product_name] = dict()
    #
    #             matcher = TextMapper(HaiTong.normal_flow, identified_dict)
    #             matcher.set_right_align(True)
    #             matcher.ignore_cell.update([loader.date_str, '沪A', '深A', '港股'])
    #             flow = re.search(r"承上日资金余额([\w\W]+)请注意：交易类资金变动的变动", content, re.M).group(1)
    #             if re.search(r"摘[ ]*要", flow):
    #                 flow = re.sub(r"摘[ ]*要", '摘要', flow)
    #             flow_list = matcher.map(flow.replace('\u3000', ' '))
    #             result_dict[product_name]['fow'] = flow_list
    #
    #             matcher = TextMapper(HaiTong.normal_pos, identified_dict)
    #             matcher.set_duplicated_tolerance(True).set_right_align(True)
    #             # matcher.ignore_cell.update(['股东代码', ])
    #             try:
    #                 pos = re.search(r"请注意：交易类资金变动[（）、!.\w]+([\w\W]+)以下为以上市场的股票金额", content, re.M).group(1)
    #             except AttributeError:
    #                 pos = ''
    #             # pos = re.sub(r'-', '  ', pos)
    #             pos_list = matcher.map(pos.replace('-', ' ').replace('\u3000', ' '))
    #             result_dict[product_name]['position'] = pos_list
    #
    #             matcher = TextMapper(HaiTong.margin_acc, identified_dict)
    #             acc = re.search(r"以下为[^，]*人民币[^，]*资金情况([\w\W]+)", content, re.M).group(1)
    #             acc_obj = matcher.map(acc)[0]
    #             result_dict[product_name]['account'] = acc_obj
    #
    #         else:
    #             raise NotImplementedError(file_name)
    #
    #     return result_dict
    #

    # =================================== =================================== #
    future_acc = {
        'currency': ['币种', ], 'customer_id': ['客户号', ], 'market_sum': ['保证金占用', ],
        'last_capital_sum': ['期初结存', ], 'market_pl': ['持仓盯市盈亏', ], 'realized_pl': ['平仓盈亏', ],
        'trade_fee': ['手续费', ], 'out_in_cash': ['出入金', ],
        'capital_sum': ['客户权益', ], 'cash_amount': ['可用资金', ],
    }
    future_flow = {
        'date': ['成交日期', ], 'security_name': ['品种', ], 'security_code': ['合约', ],
        'trade_class': ['买卖', ], 'trade_price': ['成交价', ], 'trade_volume': ['手数', ],
        'trade_amount': ['成交额', ], 'offset': ['开平', ], 'trade_fee': ['手续费', ], 'realize_pl': ['平仓盈亏', ],
        'investment_tag': ['投保', ], 'cash_move': ['权利金收支', ],
        'None': ['交易所', '投保', '权利金收支', '成交序号', ]
    }
    future_pos = {
        'security_code': ['合约', ], 'security_name': ['品种', ],
        'long_position': ['买持', ], 'short_position': ['卖持', ],
        'buy_average_cost': ['买均价', ], 'sell_average_cost': ['卖均价', ],
        'prev_settlement': ['昨结算', ], 'settlement_price': ['今结算', ],
        'market_pl': ['持仓盯市盈亏', ], 'margin': ['保证金占用', ], 'investment_tag': ['投保', ],
        'long_mkv': ['多头期权市值', ], 'short_mkv': ['空头期权市值', ],
        'None': ['多头期权市值'],
    }
    future_id_product_map = {
        '85011002': '久铭6号',
    }

    @staticmethod
    def load_future(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        folder_result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('txt'):
                HaiTong.log.debug(file_name)
                # 20200310_26200295_交易结算单（Settlement Statement）
                date_str, pro_id = re.match(r"(\d+)_(\d+)_交易", file_name).groups()
                product_name = HaiTong.future_id_product_map[pro_id]
                if product_name not in folder_result_dict:
                    folder_result_dict[product_name] = dict()
                product_file_map[product_name] = file_name
                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                HaiTong.log.debug(content)
                identified_dict = {
                    'date': date, 'product': product_name,
                    'institution': HaiTong.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                }

                matcher = TextMapper(HaiTong.future_acc, identified_dict)
                matcher.set_line_sep('|')
                check = re.search(r"资金状况([\w\W]*)出入金明细", content, re.M)
                if check:
                    acc = check.group(1)
                else:
                    acc = re.search(r"资金状况([\w\W]*)", content, re.M).group(1)
                acc = acc.replace('手 续 费', '手续费').replace('出 入 金', '出入金')
                acc = re.sub(r'[a-zA-Z/]', '', acc)
                matcher.map_horizontal(acc)
                acc_obj = matcher.form_new()
                folder_result_dict[product_name]['account'] = acc_obj

                matcher = TextMapper(HaiTong.future_pos, identified_dict)
                matcher.set_line_sep('|')
                matcher.ignore_line.update(['Product', ])
                check = re.search(r"持仓汇总([\w\W]*)共.*\d+条", content, re.M)
                if check:
                    pos = check.group(1)
                else:
                    pos = ''
                pos_list = matcher.map(pos)
                folder_result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(HaiTong.future_flow, identified_dict)
                matcher.set_line_sep('|')
                matcher.ignore_line.update(['Product'])
                check = re.search(r"成交记录([\w\W]*)共.*\d+条[\w\W]*本地强平", content, re.M)
                if check:
                    flow = check.group(1)
                else:
                    flow = ''
                flow_list = matcher.map(flow)
                folder_result_dict[product_name]['flow'] = flow_list

                confirm_future_flow_list(flow_list)
                match_future_pos_acc(pos_list, acc_obj)
            else:
                raise NotImplementedError(file_name)

        return folder_result_dict, product_file_map

    # =================================== =================================== #
    option_pos = {
        'underlying': ['标的', ], 'security_code': ['合约代码', ], 'security_name': ['合约简称', ],
        'rights_warehouse': ['总权利仓数量', ], 'voluntary_warehouse': ['总义务仓数量', ],
        'buy_average_cost': ['买均价', ], 'sell_average_cost': ['卖均价', ],
        'settlement_price': ['结算价', ], 'underlying_close_price': ['标的物收盘价', ],
        'maintenance_margin': ['维持保证金', ], 'market_value': ['期权市值', ],
        'reserve_tag': ['非备兑备兑', ],  # 'currency': ['', ],
        'None': [
            '交易所', '非组合权利仓数量', '组合权利仓数量', '非组合义务仓数量', '组合义务仓数量',
            '非组合持仓维持保证金', '组合持仓维持保证金'
        ],
    }
    option_acc = {
        'cash_amount': ['今保证金余额', ], 'market_sum': ['市值权益', ],  # 'capital_sum': ['资产合计', ],
        # 'None': ['可用资金', '买入未过户金额', '卖出未过户金额', ]
    }
    option_flow = {
        'date': ['成交日期', ], 'security_code': ['合约代码', ], 'security_name': ['合约简称', ],
        'trade_class': ['合约类型', ], 'warehouse_class': ['买卖', ],
        'offset': ['开平', ], 'reserve_tag': ['备兑标志', '备兑标识', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ],
        'trade_fee': ['手续费', ], 'cash_move': ['权利金额收支', ],
        'None': ['成交编号', '交易所', '经手费', '结算费', '佣金', ],
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        # from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            # loader.log.info_running(folder, text_file)
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('txt'):
                product_name = re.match(r"([^\d]+\d+[号指数]+)", file_name).group(1)
                if product_name not in result_dict:
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
                # content = open(
                #     os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                # ).read()
                # identified_dict = {
                #     'date': date, 'product': product_name,
                #     'institution': HaiTong.folder_institution_map_02[folder_name],
                #     'currency': 'RMB', 'account_type': folder_path,
                # }
                # if product_name not in result_dict:
                #     result_dict[product_name] = dict()
                #
                # matcher = TextMapper(HaiTong.option_pos, identified_dict, )
                # matcher.set_line_sep('|')
                # try:
                #     pos = re.search(r"持仓汇总([\w\W]*)共[\d]+条[\w\W]*出入金明细", content, re.M).group(1)
                # except AttributeError:
                #     try:
                #         pos = re.search(r"持仓汇总([\w\W]*)共[\d]+条", content, re.M).group(1)
                #     except AttributeError:
                #         pos = ''
                # pos_list = matcher.map(pos)
                # result_dict[product_name]['position'] = pos_list
                #
                # matcher = TextMapper(HaiTong.option_acc, identified_dict, )
                # matcher.set_line_sep('|')
                # try:
                #     acc = re.search(r"资金状况([\w\W]*)持仓汇总", content, re.M).group(1)
                # except AttributeError:
                #     try:
                #         acc = re.search(r"资金状况([\w\W]*)成交明细", content, re.M).group(1)
                #     except AttributeError:
                #         acc = re.search(r"资金状况([\w\W]*)ETF回购额度：", content, re.M).group(1)
                # matcher.map_horizontal(acc)
                # acc_obj = matcher.form_new()
                # result_dict[product_name]['account'] = acc_obj
                #
                # matcher = TextMapper(HaiTong.option_flow, identified_dict, )
                # matcher.set_line_sep('|')
                # try:
                #     flow = re.search(r"成交明细([\w\W]*)共[\d]+条[\w\W]*持仓汇总", content, re.M).group(1)
                #     flow_list = matcher.map(flow)
                # except AttributeError:
                #     flow_list = DataList(RawOptionFlow)
                # result_dict[product_name]['fow'] = flow_list
                #
                # matcher = TextMapper(ChuRuJin, ChuRuJin.inout_flow, {})
                # matcher.set_line_sep('|')
                # try:
                #     inout = re.search(r"出入金([\w\W]+)共[\d]+条", content, re.M).group(1)
                #     inout_list = matcher.map(inout.replace('\u3000', ''))
                #     for crj_obj in inout_list:
                #         assert isinstance(crj_obj, ChuRuJin)
                #         if crj_obj.in_cash > 0.01:
                #             cash_move, trade_class = crj_obj.in_cash, '入金'
                #         elif crj_obj.out_cash > 0.01:
                #             cash_move, trade_class = crj_obj.out_cash, '出金'
                #         else:
                #             raise RuntimeError('未知出入金 {}'.format(crj_obj))
                #         new_flow_obj = RawOptionFlow(
                #             trade_volume=0, cash_move=cash_move, trade_class=trade_class, trade_price=0,
                #             **identified_dict)
                #         flow_list.append(new_flow_obj)
                #         check = new_flow_obj.check_loaded()
                #         loader.log.debug_if(check.status is False, check.text)
                # except AttributeError:
                #     continue
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
        HaiTong.log.debug_running('读取托管估值表', file_name)
        # 文件名： SW8251_久铭6号私募证券投资基金_2019-08-22估值表
        if file_name.startswith('证券'):
            assert '_久铭6号' in file_name, file_name
            product_code = 'SW8251'
            date_str = re.search(r'\w+_\w+_(\d+-\d+-\d+)', file_name).group(1)
        else:
            product_code, product_name, date_str = re.search(
                r'([A-Z\d]+)_(\w+)私募证券投资基金_(\d+-\d+-\d+)', file_name).groups()
        product_name = PRODUCT_CODE_NAME_MAP[product_code]
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d')

        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '海通证券',
        }
        mapper = ExcelMapper(HaiTong.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)


if __name__ == '__main__':
    from jetend.jmSheets import RawTrusteeshipValuation
    from jetend.structures import List

    folder = r'C:\Users\Administrator.SC-201606081350\Downloads\test\久铭6号'

    result_list = List()
    for file_name in os.listdir(folder):
        if file_name.startswith('.') or file_name.startswith('~'):
            continue
        try:
            result_list.append(RawTrusteeshipValuation.from_dict(
                HaiTong.load_valuation_table(os.path.join(folder, file_name))
            ))
        except AssertionError:
            pass

    result_list.to_pd().to_csv('久铭6号 估值表提取页.csv', encoding='gb18030')
    # print(HaiTong.load_normal(
    #     r'D:\Documents\久铭产品交割单20190830\海通普通账户',
    #     datetime.date(2019, 8, 30)
    # ))
