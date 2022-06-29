# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import shutil

from Abstracts import AbstractInstitution
from Checker import *

from JournalLoader.Move import Move


class DongFang(AbstractInstitution):
    """东方"""
    folder_institution_map = {
        '东方普通账户': '东方',
        '东方两融账户': '东方两融',
        '东方期权账户': '东方期权'
    }

    normal_pos = {
        # 'shareholder_code': ['股东代码', ],
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
    normal_id_product_map = {
        '01125828': '稳健1号', '01125880': '稳健23号', '01127500': '专享6号',
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        # id_product_map = {
        #     '01125828': '稳健1号',
        # }
        for file_name in os.listdir(folder_path):
            DongFang.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.endswith('txt'):
                # if '期权' in file_name:
                #     raise RuntimeError('{} 放错文件夹 {}'.format(file_name, folder_name))
                some_id = re.match(r'(\d+)', file_name).group(1)
                if some_id in DongFang.normal_id_product_map:
                    pass
                elif some_id in DongFang.option_id_product_map:
                    target_path = folder_path.replace('东方普通账户', '东方期权账户')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                else:
                    raise NotImplementedError(file_name)
                product_name = re.search(r'[^\d]+\d+[号]', file_name).group()
                if product_name[:4] == '久铭稳健':
                    product_name = product_name.replace('久铭', '')
                if product_name[:4] == '久铭专享':
                    product_name = product_name.replace('久铭', '')
                date_str = date.strftime('%Y%m%d')
                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                identified_dict = {
                    'date': date, 'product': product_name, 'currency': 'RMB',
                    'institution': DongFang.folder_institution_map[folder_name],
                    'account_type': folder_name, 'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                # 流水
                matcher = TextMapper(DongFang.normal_flow, identified_dict, )
                matcher.set_right_align(True)
                # matcher.ignore_cell.update([date_str, '沪A', '深A', '港股'])

                # 解决海通普通账户在这两日对账单格式变化的问题
                # # if date_str in ['20190408', '20190401']:
                # try:
                #     flow = re.search(r"变动明细([\w\W]+)", content).group(1)
                #     if re.search(r"摘[ ]*要", flow):
                #         flow = re.sub(r"摘[ ]*要", '摘要', flow)
                # except AttributeError:
                #     flow = ''
                # else:
                # 解决20190829证券名称缺失的情况
                code_map_security = {
                    '601939': '建设银行', '799998': '撤销指定', '601288': '农业银行', '601398': '工商银行', '601668': '中国建筑',
                    '601006': '大秦铁路', '601128': '常熟银行', '000858': '五粮液', '600519': '贵州茅台', '110053': '苏银转债',
                    '132020': '19蓝星EB', '132018': 'G三峡EB', '00939': '建设银行', '688599': '新增证券',
                    '688566': 'N吉贝尔', '688516': 'N奥特维', '601778': '晶科科技', '688004': '新增证券',
                    '688505': 'N复旦', '688518': 'N联赢',
                }
                try:
                    flow = re.search(r"以下为[^，]*人民币[^，]*的对账单([\w\W]+)请注意：交易类资金变动", content, re.M).group(1)
                    if re.search(r"摘[ ]*要", flow):
                        flow = re.sub(r"摘[ ]*要", '摘要', flow)
                    flow_list = matcher.map(flow.replace('\u3000', ' '))
                    for flow in flow_list:
                        if '证券卖出' in flow['trade_class']:
                            flow['security_name'] = flow['trade_class'].replace('证券卖出', '')
                        elif '证券买入' in flow['trade_class']:
                            flow['security_name'] = flow['trade_class'].replace('证券买入', '')
                        else:
                            if flow['security_code'] in code_map_security:
                                flow['security_name'] = code_map_security[flow['security_code']]
                            # if flow['security_code'] == '601939':
                            #     flow['security_name'] = '建设银行'
                            #     flow['trade_class'] = '股息入帐'
                            # elif flow['security_code'] == '799998':
                            #     flow['security_name'] = '撤销指定'
                            #     flow['trade_class'] = '撤销指定'
                            elif '新增证券' in flow['trade_class']:
                                flow['security_name'] = '新增证券'
                            elif flow['security_code'] in ('、',):
                                pass
                            elif flow['trade_class'] in ('批量利息归本交行三方', '银行转取交行三方存管', '银行转存交行三方存管'
                                                         , '批量利息归本招行三方', '港股通证券组合费'):
                                pass
                            else:  # 这个宁行A1配的交易类型该咋整 @ waves
                                # acc = re.search(r"以下为[^，]*人民币[^，]*的资金情况([\w\W]+)", content, re.M).group(1)
                                # acc_obj = matcher.map(acc)[0]
                                # result_dict[product_name]['account'] = acc_obj
                                # match_normal_pos_acc([], acc_obj)
                                # confirm_normal_flow_list(flow_list)
                                # return 0
                                m = Move(os.path.join(folder_path, file_name))
                                m.output_log(str(flow) + "未匹配到已设定的交易类型（摘要）")
                                continue
                except AttributeError:
                    flow_list = matcher.map('')
                # print(flow_list)
                result_dict[product_name]['flow'] = flow_list

                # 持仓
                matcher = TextMapper(DongFang.normal_pos, identified_dict)
                matcher.set_right_align(True)
                matcher.set_duplicated_tolerance(True)
                matcher.ignore_line.update(['金额小计', ])
                matcher.ignore_cell.update(['股东代码', ])
                code_security = [
                    '601939建设银行', '601939XD建设银', '601006大秦铁路', '601128常熟银行', '601288农业银行',
                    '601398工商银行', '601668中国建筑', '601939建设银行', '600519贵州茅台', '000858五粮液',
                    '110053苏银转债', '132018G三峡EB1', '13202019蓝星EB', '00939建设银行', '688566新增证券'
                                                                               '603087甘李药业'
                ]
                try:
                    pos = re.search(
                        r'以下为沪A[ ]*市场的股票余额([\w\W]+)注意：股票库存数', content, re.M
                    ).group(1)
                    pos_list = matcher.map(clear_str_content(pos.replace('\u3000', ' ')))
                except AttributeError:
                    try:
                        pos = re.search(
                            r'以下为深A[ ]*市场的股票余额([\w\W]+)注意：股票库存数', content, re.M
                        ).group(1)
                        pos_list = matcher.map(clear_str_content(pos.replace('\u3000', ' ')))
                    except AttributeError:
                        pos_list = list()
                        assert '以下为沪A' not in content, content
                        assert '以下为深A' not in content, content
                for pos in pos_list:
                    DongFang.log.debug(pos)
                    # if pos['security_code_name'] in code_security:
                    try:
                        pos['security_code'] = re.match(r'(\d+)', pos['security_code_name']).group(1)
                        pos['security_name'] = re.search(r'(\D+)', pos['security_code_name']).group(1)
                    except:
                        pos['security_code'] = re.search('[\x00-\xff]+', pos['security_code_name']).group(0)
                        pos['security_name'] = re.search('[\u4e00-\u9fa5]+', pos['security_code_name']).group(0)
                    if pos['security_code_name'] in ('13202019蓝星EB',):
                        pos['security_code'] = pos['security_code_name'][:6]
                    # else:
                    #     raise NotImplementedError(pos)
                result_dict[product_name]['position'] = pos_list

                # 资金
                matcher = TextMapper(DongFang.normal_acc, identified_dict)
                matcher.set_right_align(True)
                # if date_str in ['20190408', '20190401']:
                #     acc = re.search(r"资产情况([\w\W]+参考总市值[\w\W]+)\t$", content, re.M).group(1)
                #     matcher.map_horizontal(acc)
                #     acc_obj = matcher.form_new()

                acc = re.search(r"以下为[^，]*人民币[^，]*的资金情况([\w\W]+)", content, re.M).group(1)
                acc_obj = matcher.map(acc)[0]

                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('.rar'):
                os.remove(os.path.join(folder_path, file_name))

            elif file_name.endswith('xlsx'):
                if file_name.startswith('98831808'):
                    target_path = folder_path.replace('东方普通', '东方两融')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                continue
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    margin_id_product_map = {
        '98831808': '专享6号',
    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            DongFang.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~') or '副本' in file_name:
                continue
            elif file_name.lower().endswith('xlsx'):
                # 98831808久铭专享6号20200401
                some_id = re.match(r'(\d+)', file_name).group(1)
                assert date.strftime('%Y%m%d') in file_name, '{} {}'.format(date, file_name)
                product_name = DongFang.margin_id_product_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, file_name
                identified_dict = {
                    'product': product_name, 'date': date,
                    'institution': DongFang.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name,
                    'offset': OFFSET_OPEN,
                }
                # 初始化result_dict
                if product_name not in result_dict:
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name

                # content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                #
                # matcher = ExcelMapper(ZhongXin.margin_pos, identified_dict, )
                # matcher.ignore_line.update(['合计', ])
                # matcher.set_start_line('12证券余额').set_end_line('2负债情况')
                # # 解决6.28工作簿中没有sheet1只有sheet0的情况
                # pos_list = matcher.map(content.sheet_by_index(0))
                # result_dict[product_name]['position'] = pos_list
                #
                # matcher = ExcelMapper(ZhongXin.margin_flow, identified_dict)
                # matcher.ignore_line.update(['合计', ])
                # matcher.set_start_line('三业务流水合并对账单')
                # flow_list = matcher.map(content.sheet_by_index(0))
                # result_dict[product_name]['flow'] = flow_list
                #
                # matcher = ExcelMapper(ZhongXin.margin_liability, identified_dict, )
                # matcher.set_start_line('3融资融券负债明细合并对账单').set_end_line('三业务流水合并对账单')
                # matcher.ignore_line.update(['合计', ])
                # liability_list = matcher.map(content.sheet_by_index(0))
                # result_dict[product_name]['liabilities'] = liability_list
                #
                # matcher = ExcelMapper(ZhongXin.margin_acc, identified_dict)
                # matcher.set_start_line('11当前资产情况').set_end_line('12证券余额')
                # matcher.map_horizontal(content.sheet_by_index(0))
                # acc_obj_01 = matcher.map(content.sheet_by_index(0))[0]
                #
                # matcher = ExcelMapper(ZhongXin.margin_acc, identified_dict, )
                # matcher.set_start_line('2负债情况').set_end_line('3融资融券负债明细合并对账单')
                # try:
                #     acc_obj_02 = matcher.map(content.sheet_by_index(0))[0]
                # except IndexError as i_e:
                #     if len(liability_list) == 0:
                #         acc_obj_02 = {
                #             'total_liability': 0.0, 'liability_principal': 0.0, 'liability_amount_interest': 0.0,
                #             'liability_amount_fee': 0.0, 'liability_amount_for_pay': 0.0,
                #         }
                #     else:
                #         raise i_e
                # assert isinstance(acc_obj_01, dict) and isinstance(acc_obj_02, dict)
                # acc_obj = acc_obj_01.copy()
                # acc_obj.update(acc_obj_02)
                # acc_obj['cash_available'] = acc_obj['cash_amount']
                # result_dict[product_name]['account'] = acc_obj
                #
                # match_margin_pos_acc(pos_list, acc_obj)
                # # match_margin_liability_acc(liability_list, acc_obj)
                # confirm_normal_flow_list(flow_list)
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    option_pos = {
        'security_code': ['合约代码', ], 'security_name': ['合约简称', ],
        'warehouse_class': ['持仓类别', ], 'warehouse_volume': ['权利仓数量', ],  # 'warehouse_cost': ['', ],
        'settlement_price': ['合约结算价', ], 'hold_volume': ['权利仓数量', ],
        'market_value': ['期权市值', ],
        'None': ['交易所', '标的', '可用数量'],
    }
    option_acc = {
        'cash_amount': ['现金资产', ], 'market_sum': ['期权市值', ], 'capital_sum': ['总资产', ],
        'cash_available': ['可用资金', ],
        'None': ['冻结金额', '已用保证金', '可用保证金', '币种'],
    }
    option_flow = {
        'security_code': ['合约代码', ], 'security_name': ['合约简称', ],
        'warehouse_class': ['持仓类别', ], 'trade_class': ['买卖', ], 'offset': ['开平', ],
        'trade_price': ['成交价格', ], 'trade_volume': ['成交数量', ], 'trade_amount': ['成交金额', ],
        'trade_fee': ['手续费', ], 'cash_rest': ['当前余额', ], 'reserve_tag': ['备兑标志', ],
        'cash_move': ['权利金收支'],
        'None': ['发生日期', '交易类别', '证券代码', '证券名称', ],
    }
    option_acc_flow = {
        'trade_class': ['业务标志', ], 'cash_move': ['发生金额', ], 'cash_rest': ['后资金额', ],
        'None': ['发生日期', '当前时间', '币种类别', ]
    }
    option_id_product_map = {
        '0011000048': '专享6号',
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            DongFang.log.debug(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('txt'):
                pro_id = re.search(r"(\d+)", file_name).group(1)
                product_name = DongFang.option_id_product_map[pro_id]

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = open(
                    os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                ).read()
                identified_dict = {
                    'date': date, 'product': product_name, 'currency': 'RMB', 'account_type': folder_name,
                    'institution': DongFang.folder_institution_map[folder_name],
                }

                matcher = TextMapper(DongFang.option_acc, identified_dict)
                acc = re.search(r"资金状况([\w\W]*)资金明细", content, re.M).group(1)
                matcher.map_horizontal(acc)
                acc_obj = matcher.form_new()
                result_dict[product_name]['account'] = acc_obj

                matcher = TextMapper(DongFang.option_pos, identified_dict)
                matcher.set_line_sep('|')
                # matcher.ignore_cell.update(['成本价'])
                # matcher.ignore_line.update(['合计'])
                pos = re.search(r"持仓汇总([\w\W]*)共\d+条[\w\W]*行权指派信息", content, re.M).group(1)
                pos_list = matcher.map(pos)
                for pos in pos_list:
                    pos['warehouse_class'] = '权利方'
                result_dict[product_name]['position'] = pos_list

                matcher = TextMapper(DongFang.option_flow, identified_dict)
                matcher.set_line_sep('|')
                flow = re.search(r"成交明细([\w\W]*)共\d+条[\w\W]*持仓汇总", content, re.M).group(1)
                matcher.ignore_line.update(['合计'])
                flow_list = matcher.map(flow)
                for flow_obj in flow_list:
                    flow_obj['warehouse_class'] = '权利方'
                    flow_obj['reserve_tag'] = '投'
                    flow_obj['trade_amount'] = float_check(flow_obj['cash_move']) + float_check(flow_obj['trade_fee'])

                #     assert 'trade_class' in flow_obj, flow_obj
                #     if str_check(flow_obj['trade_class']) in ('买',) and str_check(flow_obj['offset']) in ('开仓',):
                #         flow_obj['cash_move'] = - abs(
                #             float_check(flow_obj['trade_amount'])
                #         ) - abs(float_check(flow_obj['trade_fee']))
                #     else:
                #         raise NotImplementedError(flow_obj)
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
                match_option_pos_acc(pos_list, acc_obj)
            elif file_name.lower().endswith('rar'):
                os.remove(os.path.join(folder_path, file_name))
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map


if __name__ == '__main__':
    print(DongFang.load_normal(
        r'D:\Documents\久铭产品交割单20190829\东方普通账户',
        datetime.date(2019, 8, 29)
    ))
