# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import xlrd

from Abstracts import AbstractInstitution
from Checker import *


class ShenWan(AbstractInstitution):
    """申万"""
    folder_institution_map = {
        '申万普通账户': '申万', '申万期权账户': '申万期权', '申万两融账户': '申万两融'
    }

    # =================================== =================================== #
    normal_pos = {
        'shareholder_code': ['证券账户', ], 'security_code_name': ['证券代码简称', ], 'security_code': ['证券代码', ],
        'security_name': ['简称', ], 'hold_volume': ['库存数', ], 'total_cost': ['参考成本', ],
        'close_price': ['最新价', ], 'market_value': ['当前市值', ],
        'None': ['今买入价', '今买入数', '今卖出价', '今卖出数', '可用数量', '盈亏', ]
    }
    normal_flow = {
        'shareholder_code': ['证券账户', ], 'currency': ['币种', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_class': ['摘要', ], 'trade_volume': ['成交数', ],
        'trade_price': ['成交均价', ], 'cash_move': ['变动金额', ],
        # 'customer_id': ['客户号', ],
        'None': {'发生日期', '市场', '库存数', '资金余额', '佣金', '印花税', '其他费用', '交易费', '交易系统使用费', '股份交收费','财汇局征费',
                 '交易所交易规费', '交易证费', '操作站点',
                 }
    }
    normal_acc = {
        'market_sum': ['市值合计', ], 'cash_amount': ['资金余额', ], 'capital_sum': ['资产合计', ],
        'None': ['可用资金', '买入未过户金额', '卖出未过户金额', '总负债'],
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        # id_product_map = {
        #     '1812106537': '中证500指数', '1812106339': '沪深300指数', '1633051223': '久铭2号', '163305jm33890': '稳健2号',
        #     '1633051507': '稳健10号',
        # }
        for file_name in os.listdir(folder_path):
            ShenWan.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif '副本' in file_name:
                continue
            # elif file_name.endswith('txt'):
            #     pro_id, product_name, date_str = re.match(r"(\d+)([^\d]+\d+[号指数]+)[^\d]+(\d+)", file_name).groups()
            #     assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
            #     product_name = id_product_map[pro_id]
            #     content = open(
            #        os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
            #     ).read()
            #     identified_dict = {
            #        'date': date, 'product': product_name, 'currency': 'RMB',
            #        'institution': ShenWan.folder_institution_map[folder_name],
            #        'account_type': folder_name,
            #     }
            #
            #     if product_name not in result_dict:
            #         result_dict[product_name] = dict()
            #
            #     matcher = TextMapper(ShenWan.normal_acc, identified_dict)
            #     matcher.map_horizontal(content.replace('\u3000', ' '))
            #     acc_obj = matcher.form_new()
            #     result_dict[product_name]['account'] = acc_obj
            #
            #     matcher = TextMapper(ShenWan.normal_pos, identified_dict)
            #
            #     # TODO: 读取了三段？？
            #     try:
            #         pos = re.search(
            #             r"以下为\W+沪A\W+市场的股票余额([\w\W]+)以下为\W+深A\W+市场的股票余额", content, re.M
            #         ).group(1)
            #         pos_list = matcher.map(pos.replace('\u3000', ' '))
            #     except AttributeError:
            #         try:
            #             pos = re.search(r"以下为\W+深A\W+市场的股票余额([\w\W]+)以下为\W+港股\W+市场的股票余额", content, re.M
            #             ).group(1)
            #             pos = '\n'.join(pos.split("\n")[2:])
            #             matcher.map(pos.replace('\u3000', ' '))
            #         except AttributeError:
            #             try:
            #                 pos = re.search(r"以下为\W+港股\W+市场的股票余额([\w\W]+)注意：股票库存数为", content, re.M
            #                 ).group(1)
            #                 pos = '\n'.join(pos.split("\n")[2:])
            #                 pos_list = matcher.map(pos.replace('\u3000', ' '))
            #             except AttributeError:
            #                 pos = ''
            #     result_dict[product_name]['position'] = pos_list
            #
            #     try:
            #         pos = re.search(r"以下为\W+深A\W+市场的股票余额([\w\W]+)以下为\W+港股\W+市场的股票余额", content, re.M).group(1)
            #     except AttributeError:
            #         pos = ''
            #
            #
            #     try:
            #         pos = re.search(r"以下为\W+港股\W+市场的股票余额([\w\W]+)注意：股票库存数为", content, re.M).group(1)
            #     except AttributeError:
            #         pos = ''
            #     pos = '\n'.join(pos.split("\n")[2:])
            #     pos_list = matcher.map(pos.replace('\u3000', ' '))
            #     result_dict[product_name]['position'] = pos_list
            #
            #     matcher = TextMapper(ShenWan.normal_flow, identified_dict)
            #     try:
            #         flow = re.search(r"客户帐务明细([\w\W]+)注意：交易类资金变动的", content, re.M).group(1)
            #     except AttributeError:
            #         flow = ''
            #         flow = re.sub(r"摘[ ]*要", '摘要', flow)
            #     flow_list = matcher.map(flow.replace('\u3000', ''))
            #     result_dict[product_name]['fow'] = flow_list

            elif file_name.lower().endswith('xlsx'):
                if re.search(r'2号',file_name):
                    print("匹配到2")
                    os.remove(os.path.join(folder_path,file_name))
                    continue
                if re.search(r'10号',file_name):
                    print("匹配到10")
                    os.remove(os.path.join(folder_path, file_name))
                    continue
                if re.search(r'久铭稳健',file_name):
                    print("匹配到稳健")
                    os.remove(os.path.join(folder_path, file_name))
                    continue

                # 6.28之前都是申万普通账户手动增加2号
                if date >= datetime.date(2019, 6, 28):
                    # 解决每天文件名字只有久铭稳健没有几号的问题(不用每次都要手动加2号)
                    if '久铭稳健' in file_name:
                        product_name = '稳健2号'
                        date_str = re.search(r'(\d+)', file_name).group(1)
                    else:
                        product_name, date_str = re.match(r'\w+-\w+-([^\d]+\d+[号指数]*)(\d+)', file_name).groups()
                else:
                    product_name, date_str = re.match(r'\w+-\w+-([^\d]+\d+[号指数]*)(\d+)', file_name).groups()
                    if len(product_name) == 6:
                        assert isinstance(product_name, str)
                        product_name = product_name.replace('久铭', '')
                # print(product_name, date_str)
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'product': product_name, 'date': date, 'offset': OFFSET_OPEN,
                    'institution': ShenWan.folder_institution_map[folder_name],
                    'account_type': folder_name, 'currency': 'RMB',
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ShenWan.normal_flow, identified_dict, )
                matcher.set_start_line('客户账务明细')
                matcher.set_end_line('注意交易类资金变动的变动金额为成交金额含费用如印花税手续费过户费等')
                # matcher.set_end_line('融资负债明细')
                flow_list = matcher.map(content.sheet_by_name('客户普通对账单'))
                sub_map = {
                    '利息结转': ['利息结转', '', ''],
                    '|': ['|', '', ''], '撤销指定撤消指定': ['|', '', ''],
                    '天邦股份证券买入': ['证券买入', '002124.SZ', '天邦股份'],
                    '港股待交收卖出': ['港股待交收卖出', '0700.HK', '腾讯控股', ],
                    '建设银行证券买入': ['证券买入', '601939.SH', '建设银行'],
                    '港股待交收买入': ['港股待交收买入', '0939.HK', '建设银行'],
                    '建设银行证券卖出': ['证券卖出', '601939.SH', '建设银行', ], '组合费': ['组合费', '', ''],
                    '港股卖出资金预交收': ['港股卖出资金预交收', '0700.HK', '腾讯控股', ],
                    '港股卖出资金交收': ['港股卖出资金交收', '0700.HK', '腾讯控股', ],
                    '济川药业证券卖出': ['证券卖出', '600566.SH', '济川药业', ],
                    '港股买入资金预交收': ['港股买入资金预交收', '0939.HK', '建设银行', ],
                    '港股买入资金交收': ['港股买入资金交收', '0939.HK', '建设银行', ],
                    '天邦股份证券卖出': ['证券卖出', '002124.SZ', '天邦股份', ],
                    '贵州茅台证券买入': ['证券买入', '600519.SH', '贵州茅台'],
                    '工商银行证券买入': ['证券买入', '601398.SH', '工商银行'],
                    '五粮液证券买入': ['证券买入', '000858.SZ', '五粮液']
                }

                for flow in flow_list:
                    if flow['trade_class'] == '利息结转[0.003500]' or '结息' in flow['trade_class']:
                        flow['trade_class'] = '利息结转'
                    elif '组合费' in flow['trade_class']:
                        flow['trade_class'] = '组合费'
                    elif '港股待交收卖出' in flow['trade_class']:
                        flow['trade_class'] = '港股待交收卖出'
                    elif '港股卖出资金预交收' in flow['trade_class']:
                        flow['trade_class'] = '港股卖出资金预交收'
                    elif '港股卖出资金交收' in flow['trade_class']:
                        flow['trade_class'] = '港股卖出资金交收'
                    elif '港股待交收买入' in flow['trade_class']:
                        flow['trade_class'] = '港股待交收买入'
                    elif flow['trade_class'] == '|jm33894567890AB':
                        flow['trade_class'] = '|'
                    elif '港股买入资金预交收' in flow['trade_class']:
                        flow['trade_class'] = '港股买入资金预交收'
                    elif '港股买入资金交收' in flow['trade_class']:
                        flow['trade_class'] = '港股买入资金交收'
                    elif '非交易过户' in flow['trade_class']:
                        flow['trade_class'] = '非交易过户'
                    elif '卖出' in flow['trade_class']:
                        pass
                    else:
                        if flow['trade_class'] in sub_map:
                            continue
                        elif flow['trade_class'] in NORMAL_DIRECTION_BUY_TRADE_CLASS \
                                or flow['trade_class'] in NORMAL_DIRECTION_SELL_TRADE_CLASS:
                            # raise NotImplementedError(flow)
                            continue
                        elif flow['trade_class'] == '撤销指定':
                            continue
                        else:
                            raise NotImplementedError(flow)
                # for flow in flow_list:
                #   if flow['trade_class'] in sub_map:
                #        flow['security_code'] = sub_map[flow['trade_class']][1]
                #       flow['security_name'] = sub_map[flow['trade_class']][2]
                #        flow['trade_class'] = sub_map[flow['trade_class']][0]
                #    elif '卖出' in flow['trade_class']:
                #        pass

                #    else:
                #       raise NotImplementedError(flow)

                # for flow in flow_list:
                #     if flow['trade_class'] == '利息结转[0.003500]':
                #         flow['trade_class'] = '利息结转'
                #     if '组合费' in flow['trade_class']:
                #         flow['trade_class'] = '组合费'
                #     elif flow['trade_class'] == '建设银行证券卖出':
                #         flow['security_code'] = '601939'
                #         flow['security_name'] = '建设银行'
                #     elif '港股待交收卖出' in flow['trade_class']:
                #         flow['trade_class'] = '港股待交收卖出'
                #     elif '港股卖出资金预交收' in flow['trade_class']:
                #         flow['trade_class'] = '港股卖出资金预交收'
                #         flow['security_code'] = '00700'
                #         flow['security_name'] = '腾讯控股'
                #     # 解决20190718久铭2号trade_class复杂的问题
                #     elif '港股卖出资金交收' in flow['trade_class']:
                #         flow['trade_class'] = '港股卖出资金交收'
                #         flow['security_code'] = '00700'
                #         flow['security_name'] = '腾讯控股'
                #     # 解决20190731 久铭5号trade_class复杂的问题
                #     elif flow['trade_class'] == '天邦股份证券买入':
                #         flow['trade_class'] = '证券买入'
                #         flow['security_code'] = '002124.SZ'
                #         flow['security_name'] = '天邦股份'
                #     elif flow['trade_class'] == '建设银行证券买入':
                #         flow['trade_class'] = '证券买入'
                #         flow['security_code'] = '601939.SH'
                #         flow['security_name'] = '建设银行'
                #     elif '港股待交收买入' in flow['trade_class']:
                #         flow['trade_class'] = '港股待交收买入'
                #         flow['security_code'] = '00939'
                #         flow['security_name'] = '建设银行'
                #     elif flow['trade_class'] == '|jm33894567890AB':
                #         flow['trade_class'] = '|'

                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ShenWan.normal_acc, identified_dict, )
                matcher.set_start_line('以下为人民币的资金情况')
                acc_obj = matcher.map(content.sheet_by_name('客户普通对账单'))[0]
                result_dict[product_name]['account'] = acc_obj

                matcher = ExcelMapper(ShenWan.normal_pos, identified_dict, )
                matcher.set_duplicated_tolerance(True)
                matcher.set_start_line('客户持股清单').set_end_line('注意股票库存数为昨日余额当日买卖和市值仅供参考具体数')
                try:
                    pos_list = matcher.map(content.sheet_by_name('客户普通对账单'))
                except RuntimeError as r_e:
                    if abs(float_check(acc_obj['market_sum'])) < 0.1:
                        pos_list = list()
                    else:
                        raise r_e
                result_dict[product_name]['position'] = pos_list

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xlsx'):
                if '久铭5号' in file_name:
                    product_name = '久铭5号'
                else:
                    raise NotImplementedError(file_name)

                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name

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
        'cash_amount': ['资金余额', ], 'market_sum': ['证券市值', ], 'capital_sum': ['总资产', ],
        # 'cash_available': ['当前余额', ],
        'None': ['日期', '资金账号', '盈亏', '币种'],
    }
    option_flow = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'warehouse_class': ['持仓类别', ], 'trade_class': ['摘要', ], 'offset': ['开平仓方向', ],
        'trade_price': ['成交均价', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['交易金额', ],
        'trade_fee': ['实收佣金', ], 'cash_rest': ['资金余额', ], 'reserve_tag': ['备兑标志', ],
        'None': [
            '交易市场', '资金余额', '印花税', '过户费', '交易规费', '结算费', '经手费', '日期', '流水号',
            '资金账号',
        ],
    }
    option_acc_flow = {
        'trade_class': ['业务标志', ], 'cash_move': ['发生金额', ], 'cash_rest': ['后资金额', ],
        'None': ['发生日期', '当前时间', '币种类别', ]
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            ShenWan.log.debug(file_name)
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xlsx'):
                # 申万宏源-上海陆家嘴环路-久铭5号（期权）20200415
                product_name, date_str = re.match(r'\w+-\w+-(\w+)（期权）(\d+)', file_name).groups()
                assert product_name in PRODUCT_NAME_RANGE, file_name
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date, file_name)
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
                continue

                identified_dict = {
                    'date': date, 'product': product_name, 'currency': 'RMB', 'account_type': folder_name,
                    'institution': ShenWan.folder_institution_map[folder_name],
                }
                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ShenWan.option_acc, identified_dict)
                matcher.set_start_line('期末资产').set_end_line('持仓明细')
                acc_obj = matcher.map(content.sheet_by_index(0))[0]
                result_dict[product_name]['account'] = acc_obj

                matcher = ExcelMapper(ShenWan.option_pos, identified_dict)
                matcher.set_start_line('持仓明细').set_end_line('资金明细')
                matcher.ignore_line.update(['合计'])
                pos_list = matcher.map(content.sheet_by_index(0))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ShenWan.option_flow, identified_dict)
                matcher.set_start_line('资金明细')
                flow_list = matcher.map(content.sheet_by_index(0))
                for flow_obj in flow_list:
                    # assert 'trade_class' in flow_obj, flow_obj
                    # if str_check(flow_obj['trade_class']) in ('买',) and str_check(flow_obj['offset']) in ('开仓',):
                    #     flow_obj['cash_move'] = - abs(
                    #         float_check(flow_obj['trade_amount'])
                    #     ) - abs(float_check(flow_obj['trade_fee']))
                    # else:
                    #     pass
                    flow_obj['cash_move'] = float_check(flow_obj['trade_amount'])
                    # flow_obj['trade_amount'] = 0.0
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

                # confirm_option_flow_list(flow_list)
                match_option_pos_acc(pos_list, acc_obj)
            elif file_name.lower().endswith('pdf'):
                # 久铭5号20200415
                product_name, date_str = re.match(r'([久铭]+\d+[\D]+)(\d+)', file_name).groups()
                assert product_name in PRODUCT_NAME_RANGE, file_name
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date, file_name)
                if product_name not in result_dict:
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
            elif file_name.lower().endswith('txt'):
                try:
                    product_name, date_str = re.match(r'([久铭]+\d+[号指数]+)[\D]*(\d+)', file_name).groups()
                except AttributeError:
                    product_name, date_str = re.match(r'[\d]+([久铭]+\d+[号指数]+)[\D]*(\d+)', file_name).groups()
                assert product_name in PRODUCT_NAME_RANGE, file_name
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date, file_name)
                if product_name not in result_dict:
                    result_dict[product_name] = None
                    product_file_map[product_name] = file_name
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map


if __name__ == '__main__':
    print(ShenWan.load_normal(
        r'D:\Documents\久铭产品交割单20190809\申万普通账户', datetime.date(2019, 8, 9)))

    # option_pos = {
    #     'underlying': ['标的', ], 'security_code': ['合约代码', ], 'security_name': ['合约简称', ],
    #     'rights_warehouse': ['权利仓数量', ], 'voluntary_warehouse': ['义务仓数量', ],
    #     'buy_average_cost': ['买均价', ], 'sell_average_cost': ['卖均价', ],
    #     'settlement_price': ['合约结算价', ], 'underlying_close_price': ['标的物收盘价', ],
    #     'maintenance_margin': ['维持保证金', ], 'market_value': ['期权市值', ],
    #     'reserve_tag': ['备兑标识', ],  # 'currency': ['', ],
    #     'None': ['交易所', ],
    # }
    # option_acc = {
    #     'cash_amount': ['现金资产', ], 'market_sum': ['期权市值', ], 'capital_sum': ['总资产', ],
    #     'None': ['可用资金', ],
    # }
    # option_flow = {
    #     'security_code': ['合约代码', ], 'security_name': ['合约简称', ], 'warehouse_class': ['合约类型', ],
    #     'trade_class': ['买卖', ], 'offset': ['开平', ], 'reserve_tag': ['备兑标识', ],
    #     'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'cash_move': ['权利金收支', ],
    #     'trade_fee': ['手续费', ],  # currency  trade_amount
    #     'None': ['成交日期', '成交编号', '交易所'],
    # }
    # @staticmethod
    # def load_option(folder_path: str, date: datetime.date):
    #     from jetend.structures import TextMapper
    #     folder_name = folder_path.split(os.path.sep)[-1]
    #     result_dict = dict()
    #     id_product_map = {
    #         '1812106339': '沪深300指数', '1812106537': '中证500指数',
    #     }
    #     for file_name in os.listdir(folder_path):
    #         # loader.log.info_running(folder, text_file)
    #         if file_name.startswith('.'):
    #             continue
    #         elif file_name.endswith('txt'):
    #             pro_id, product_name, date_str = re.search(r"[^\d]+(\d+)([^\d]+\d+[号指数]+)[^\d]*(\d+)", file_name) \
    #                 .groups()
    #             product_name = id_product_map[pro_id]
    #             assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
    #             content = open(
    #                 os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
    #             ).read()
    #             identified_dict = {
    #                 'date': date, 'product': product_name, 'currency': 'RMB',
    #                 'institution': ShenWan.folder_institution_map[folder_name],
    #                 'account_type': folder_path,
    #             }
    #
    #             if product_name not in result_dict:
    #                 result_dict[product_name] = dict()
    #
    #             matcher = TextMapper(ShenWan.option_acc, identified_dict)
    #             matcher.set_line_sep('|')
    #             acc = re.search(r"资金状况([\w\W]*)资金明细", content, re.M).group(1)
    #             matcher.map_horizontal(acc)
    #             acc_obj = matcher.form_new()
    #             result_dict[product_name]['account'] = acc_obj
    #
    #             matcher = TextMapper(ShenWan.option_flow, identified_dict)
    #             matcher.set_line_sep('|')
    #             flow = re.search(r"成交明细([\w\W]*)共[\d]+条[\w\W]*持仓汇总", content, re.M).group(1)
    #             flow_list = matcher.map(flow)
    #             result_dict[product_name]['fow'] = flow_list
    #
    #             matcher = TextMapper(ShenWan.option_pos, identified_dict)
    #             matcher.set_line_sep('|')
    #             pos = re.search(r"持仓汇总([\w\W]*)共[\d]+条[\w\W]*行权指派信息", content, re.M).group(1)
    #             pos_list = matcher.map(pos)
    #             result_dict[product_name]['position'] = pos_list

# for file_name in os.listdir(folder_path):
#     if file_name.startswith('.'):
#         continue
#     elif file_name.lower().endswith('xls'):
#         product_name, date_str = re.match(r'\w+-\w+-([^\d]+\d*[号指数]*)(\d+)', file_name).groups()
#         print(product_name)
#         #product_name = loader.env.product_name_map[product_name]
#         assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
#         identified_dict = {
#            'product': product_name, 'date': date,
#            'institution': folder_institution_map_01[folder_name],
#            'account_type': folder_path, 'currency':'RMB'
#         }
#         content = xlrd.open_workbook(os.path.join(folder_path, file_name))
#
#         matcher = ExcelMapper( ShenWan.normal_flow, identified_dict, ShenWan.normal_pos)
#         matcher.set_start_line('客户账务明细').set_end_line('注意交易类资金变动的变动金额为成交金额含费用如印花税手续费过户费等')
#         flow_list = matcher.map(content.sheet_by_name('客户普通对账单'))
#
#         matcher = ExcelMapper( ShenWan.normal_pos, identified_dict, ShenWan.normal_acc)
#         try:
#            matcher.set_start_line('客户持股清单以下为沪A市场的股票余额').set_end_line('客户持股清单以下为深A市场的股票余额')
#         except AttributeError:
#            matcher.set_start_line('客户持股清单以下为沪A市场的股票余额')
#         try:
#            pos_list = matcher.map(content.sheet_by_name('客户普通对账单'))
#         except RuntimeWarning:
#            #pos_list = DataList(RawNormalPosition)
#            continue
#
#         matcher = ExcelMapper( ShenWan.normal_pos, identified_dict, ShenWan.normal_acc)
#         try:
#            matcher.set_start_line('客户持股清单以下为深A市场的股票余额').set_end_line('客户持股清单以下为港股市场的股票余额')
#         except AttributeError:
#            matcher.set_start_line('客户持股清单以下为深A市场的股票余额')
#         try:
#            pos_list.extend(matcher.map(content.sheet_by_name('客户普通对账单')))
#         except RuntimeWarning:
#            continue
#
#         matcher = ExcelMapper( ShenWan.normal_pos, identified_dict, ShenWan.normal_acc)
#         matcher.set_start_line('客户持股清单以下为港股市场的股票余额')
#         try:
#            pos_list.extend(matcher.map(content.sheet_by_name('客户普通对账单')))
#         except RuntimeWarning:
#            continue
#         result_dict[product_name]['position'] = pos_list
#
#     # try:
#     #     pos_list = matcher.map(content.sheet_by_name('客户普通对账单'))
#     #
#     # except RuntimeError as run_error:
#     #     if product_name not in loader.env.product_name_map:
#     #         pass
#     #     else:
#     #         raise run_error
#
#         matcher = ExcelMapper( ShenWan.normal_acc,identified_dict,)
#         matcher.set_start_line('以下为人民币的资金情况')
#         acc_obj = matcher.map(content.sheet_by_name('客户普通对账单'))[0]
#         result_dict[product_name]['account'] = acc_obj
#     else:
#         raise NotImplementedError(file_name)
