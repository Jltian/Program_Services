# -*- encoding: UTF-8 -*-
import datetime
import os
# import re
import xlrd
import shutil
import utils
import zipfile
from BatchDecompression import *
from xlrd.biffh import XLRDError

from Abstracts import AbstractInstitution
from Checker import *


# from utils import normal


class AnXin(AbstractInstitution):
    folder_institution_map = {
        '安信普通账户': '安信',
        '安信两融账户': '安信两融',
        '安信期货账户': '安信期货',
        '安信期权账户': '安信期权',
    }

    # =================================== =================================== #
    normal_flow = {
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ],  # 'trade_direction': '交易方向',
        'trade_class': ['摘要', ], 'trade_price': ['成交价格', ],
        'cash_move': ['清算金额', '发生金额'], 'trade_volume': ['成交股数', ],
        'None': [
            '发生日期', '资金余额', '所得税', '手续费', '过户费', '印花税', '清算费', '交易规费', '交易单费', '交易所过户费',
            '尾差修正', '股东帐号', '成交价格币种', '港股汇率', '发生金额币种',
        ]
    }
    normal_pos = {
        'shareholder_code': ['股东帐号', '股东账户'],
        'security_name': ['证券名称'], 'security_code': ['证券代码'],
        'hold_volume': ['股份余额'], 'weight_average_cost': ['参考成本价'], 'total_cost': ['参考成本'],
        'close_price': ['参考市价'], 'market_value': ['参考市值'],
        'None': ['股份可用', '交易冻结', '参考盈亏', '港股在途数量', '股东账号', '市场', '在途数量'],
    }
    normal_acc = {
        'capital_account': ['资产账户', ], 'customer_id': ['客户代码', ],
        'market_sum': ['资产市值', ], 'capital_sum': ['总资产', ], 'cash_amount': ['可用余额', '资金余额'],
        'None': ['港股通资金可用', '客户姓名', '资产账号', '资金可用'],
    }
    normal_id_product_map = {
        '104453357': '久铭1号', '104508010': '久铭50指数', '104509863': '静康1号', '105038753': '久铭创新稳禄1号',
        '105056011': '收益2号', '105127088': '专享1号',
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
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        result_list = list()
        return_type = 'dict'

        # 全目录文件扫描
        for file_name in os.listdir(folder_path):
            AnXin.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or '手动备份' in file_name:
                continue
            # elif '副本' in file_name:
            #     continue
            elif file_name.lower().endswith('xls'):
                # 解决6.28安信普通账户增加了创新稳禄1号的情况
                if 'rzrq229' in file_name or '888821600227' in file_name:
                    os.remove(os.path.join(folder_path, file_name))
                    continue
                if '1262账户合并对帐单' in file_name:
                    os.rename(
                        os.path.join(folder_path, file_name),
                        os.path.join(folder_path, '专享1号{}账户合并对帐单.xls'.format(date.strftime('%Y%m%d')))
                    )
                    continue
                if '信用账户' in file_name:
                    target_path = folder_path.replace('安信普通', '安信两融')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                try:
                    identify_code = re.match(r'(\d+)', file_name).group(1)
                    if identify_code.startswith('88'):
                        pass
                    else:
                        assert identify_code in AnXin.normal_id_product_map, file_name
                        product_name = AnXin.normal_id_product_map[identify_code]
                        if product_name not in result_dict:
                            result_dict[product_name] = None
                        product_file_map[product_name] = file_name
                        continue
                except AttributeError:
                    pass

                try:
                    product_name, date_str = re.match(
                        r'\d*([专享久铭盈静康创新稳禄收益健]+\d+[号指数]+)[^\d]*(\d+)', file_name
                    ).groups()
                except AttributeError as a_error:
                    if '1262账户合并对帐单' in file_name:
                        product_name, date_str = '专享1号', date.strftime('%Y%m%d')
                        assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                    else:
                        if file_name.startswith('上海久铭投资管理有限公司') or file_name.startswith('静久康铭（上海）'):
                            if '久铭1号' in file_name:
                                product_name = '久铭1号'
                            elif '静康1号' in file_name:
                                product_name = '静康1号'
                            else:
                                raise NotImplementedError(file_name)
                        else:
                            raise NotImplementedError(file_name)
                        # try:
                        #     # 105038753_上海久铭投资管理有限公司
                        #     raise NotImplementedError
                if product_name.startswith('久铭'):
                    if re.match(r'久铭\d+', product_name):
                        pass
                    else:
                        product_name = product_name.replace('久铭', '')
                # except AttributeError:
                #     product_name, date_str = re.match(
                #         r'([久铭静康创新稳禄收益健]+\d+[号指数]+)(\d+)', re.sub(r'\W', '', file_name)
                #     ).groups()
                # print(product_name)

                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': AnXin.folder_institution_map[folder_name], 'currency': 'RMB',
                    'offset': OFFSET_OPEN,
                }

                product_file_map[product_name] = file_name
                assert '信用' not in file_name, file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(AnXin.normal_pos, identified_dict)
                matcher.ignore_line.update(['合计'])
                try:
                    pos_list = matcher.map(content.sheet_by_name('拥股情况'))
                except XLRDError:
                    try:
                        pos_list = matcher.map(content.sheet_by_name('持仓清单'))
                    except XLRDError:
                        try:
                            pos_list = matcher.map(content.sheet_by_name('股份明细'))
                        except XLRDError:
                            matcher.set_start_line('拥股情况').set_end_line('新股配号')
                            pos_list = matcher.map(content.sheet_by_index(0))

                matcher = ExcelMapper(AnXin.normal_acc, identified_dict)
                try:
                    matcher.set_start_line('资金情况')
                    acc_obj = matcher.map(content.sheet_by_name('资金情况'))[0]
                except XLRDError:
                    try:
                        matcher.set_start_line('资金资产情况')
                        acc_obj = matcher.map(content.sheet_by_name('资金资产情况'))[0]
                    except XLRDError:
                        matcher.set_start_line('资金情况').set_end_line('对账单')
                        acc_obj = matcher.map(content.sheet_by_index(0))[0]

                matcher = ExcelMapper(AnXin.normal_flow, identified_dict)
                matcher.ignore_line.update(['合计'])
                try:
                    flow_list = matcher.map(content.sheet_by_name('对帐单'))
                except XLRDError:
                    matcher.ignore_line.update(['合计', ])
                    matcher.set_start_line('对账单').set_end_line('资金情况')
                    flow_list = matcher.map(content.sheet_by_index(0))
                for flow in flow_list:
                    if '股息红利个人所得税扣款' in flow['trade_class']:
                        flow['trade_class'] = '股息红利所得税扣款'
                    elif flow['trade_class'] == '融资买入借款(+)':
                        flow['trade_class'] = '融资买入借款'
                    elif flow['trade_class'] == '融资定期还息(-)':
                        flow['trade_class'] = '融资定期还息'
                    else:
                        pass

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

                if return_type == 'dict':
                    # 初始化result_dict
                    if product_name not in result_dict:
                        result_dict[product_name] = dict()
                    result_dict[product_name] = dict()
                    result_dict[product_name]['position'] = pos_list
                    result_dict[product_name]['account'] = acc_obj
                    result_dict[product_name]['flow'] = flow_list

                elif return_type == 'list':
                    result_list.append(utils.get_journal(
                        utils.get_data_dict(file_name, product_name=product_name, pos_list=pos_list, acc_obj=acc_obj,
                                            flow_list=flow_list)))

            elif file_name.lower().endswith('.rar'):
                # BatchDecompression(folder_path,folder_path,['盯市']).batchExt()
                # continue
                os.remove(os.path.join(folder_path, file_name))

            elif file_name.lower().endswith('zip'):
                with zipfile.ZipFile(os.path.join(folder_path, file_name), mode='r') as z_file:
                    for sub_file in z_file.namelist():
                        assert isinstance(sub_file, str)
                        z_file.extract(sub_file, path=folder_path)
                os.remove(os.path.join(folder_path, file_name))

            else:
                raise NotImplementedError(file_name)

        if return_type == 'dict':
            return result_dict, product_file_map
        elif return_type == 'list':
            return result_list, product_file_map
        else:
            raise RuntimeError

    margin_pos = {
        'shareholder_code': ['股东账号', '股东帐号', '股东账户', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'hold_volume': ['股份余额', ],
        'weight_average_cost': ['参考成本价', ], 'market_value': ['参考市值', ], 'market_price': ['参考市价', ],
        'total_cost': ['参考成本', ],
        'None': ['参考盈亏', '股份可用', '交易冻结', ],
    }
    margin_flow = {
        'trade_class': ['摘要代码', '摘要'], 'security_code': ['证券代码', ], 'security_name': ['证券简称', '证券名称'],
        'trade_volume': ['数量', '成交股数'], 'trade_price': ['成交价格', ], 'cash_move': ['发生金额', '清算金额'],
        'None': [
            '资金余额', '手续费', '印花税', '过户费', '其他费', '备注信息', '发生日期', '业务类型',
            '股东账户', '股份余额', '备注', '清算日期', '交易渠道',
        ],
    }
    margin_acc = {
        'capital_sum': ['资产总值', '总资产'], 'market_sum': ['证券市值', '资产市值'], 'cash_amount': ['资金余额', ],
        'liability_principal': ['融资余额', ], 'liability_amount_interest': ['未了结融资利息', ],
        'liability_amount_fee': ['融资费用', ], 'net_asset': ['净资产', ], 'total_liability': ['负债合计', ],
        'None': [
            '货币代码', '资金可用', '异常冻结', '交易冻结', '在途资金', '在途可用', '融资保证金',
            '融券市值', '融券费用', '未了结融券利息', '融券保证金', '上一日未了结融资利息', '上一日未了结融券利息',
            '资产账户', '融资负债', '融券负债', '保证金余额', '负债日期'
        ],
    }
    margin_liability = {
        'contract_date': ['合约日期', ], 'payback_date': ['合约到期日', ],
        'security_code': ['证券代码', ],  # 'security_name': ['证券名称', ],
        'contract_type': ['合约类型', ], 'contract_amount': ['合约金额', ], 'fee_payable': ['合约费用', ],
        'contract_volume': ['合约数量', ], 'interest_payable': ['剩余利息', ],
        None: [
            '市场', '合约序号', '已偿还金额', '剩余金额', '已偿还数量', '剩余数量', '委托价格', '委托数量', '委托金额',
        ]
    }
    margin_id_product_map = {
        '104453357': '久铭1号', '104509863': '静康1号', '104508010': '久铭50指数', '105127088': '专享1号',
        '105056011': '收益2号',
    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            AnXin.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            # elif '副本' in file_name:
            #     continue
            elif file_name.lower().endswith('xls'):
                if file_name == 'rzrq229融资融券帐户对帐单.xls':
                    os.rename(
                        os.path.join(folder_path, file_name),
                        os.path.join(folder_path, '专享1号{}融资融券帐户对帐单.xls'.format(date.strftime('%Y%m%d'))),
                    )
                    continue
                if '账户合并对帐单' in file_name:
                    target_folder = folder_path.replace('两融', '普通')
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(os.path.join(folder_path, file_name), folder_path.replace('两融', '普通'))
                    continue
                try:
                    identify_code = re.match(r'(\d+)', file_name).group(1)
                    if identify_code.startswith('88'):
                        pass
                    else:
                        assert identify_code in AnXin.margin_id_product_map, file_name
                        product_name = AnXin.normal_id_product_map[identify_code]
                        if product_name not in result_dict:
                            result_dict[product_name] = None
                        product_file_map[product_name] = file_name
                        continue
                except AttributeError:
                    pass

                try:
                    product_name, date_str = re.match(r"([^\d]+\d+[号指数]+)[^\d]*(\d+)", file_name).groups()
                except AttributeError:
                    try:
                        product_name, date_str = re.match(r"\d*\s([^\d]+\d+[号指数]+)[^\d]*(\d+)", file_name).groups()
                    except AttributeError:
                        product_name, date_str = re.match(r"\d*[_]*([^\d]+\d+[号指数]+)[^\d]*(\d+)", file_name).groups()
                if re.match(r'久铭稳健\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                elif re.match(r'久铭收益\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                elif re.match(r'久铭专享\d+号', product_name):
                    product_name = product_name.replace('久铭', '')
                elif re.match(r'上海久铭投资管理有限公司－', product_name):
                    product_name = product_name.replace('上海久铭投资管理有限公司－', '')
                else:
                    pass

                identified_dict = {
                    'product': product_name, 'date': date, 'institution': AnXin.folder_institution_map[folder_name],
                    'currency': 'RMB', 'account_type': folder_name, 'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(AnXin.margin_pos, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                try:
                    pos_list = matcher.map(content.sheet_by_name('当前资产'))
                except xlrd.biffh.XLRDError:
                    pos_list = matcher.map(content.sheet_by_name('股份明细 '))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(AnXin.margin_flow, identified_dict)
                matcher.ignore_line.update(['合计', ])
                try:
                    flow_list = matcher.map(content.sheet_by_name('业务流水'))
                except xlrd.biffh.XLRDError:
                    flow_list = matcher.map(content.sheet_by_name('对账单流水'))
                for flow in flow_list:
                    if '股息红利个人所得税扣款' in flow['trade_class']:
                        flow['trade_class'] = '股息红利所得税扣款'
                    elif flow['trade_class'] == '融资买入借款(+)':
                        flow['trade_class'] = '融资买入借款'
                    else:
                        pass
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(AnXin.margin_liability, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                try:
                    liability_list = matcher.map(content.sheet_by_name('负债明细'))
                except xlrd.biffh.XLRDError:
                    liability_list = matcher.map(content.sheet_by_name('负债汇总情况 '))
                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(AnXin.margin_acc, identified_dict).add_identified_dict({
                    'liability_amount_for_pay': 0.0,
                })
                try:
                    acc_obj_01 = matcher.map(content.sheet_by_name('资产负债情况'))[0]
                except xlrd.biffh.XLRDError:
                    acc_obj_01 = matcher.map(content.sheet_by_name('资金资产情况 '))[0]
                matcher = ExcelMapper(AnXin.margin_acc, identified_dict, )
                try:
                    acc_obj_02 = matcher.map(content.sheet_by_name('负债情况'))[0]
                except xlrd.biffh.XLRDError:
                    acc_obj_02 = matcher.map(content.sheet_by_name('负债汇总情况 '))[0]
                assert isinstance(acc_obj_01, dict) and isinstance(acc_obj_02, dict)
                acc_obj = acc_obj_01.copy()
                acc_obj.update(acc_obj_02)
                acc_obj['cash_available'] = acc_obj['cash_amount']
                result_dict[product_name]['account'] = acc_obj

                match_margin_pos_acc(pos_list, acc_obj)
                # match_margin_liability_acc(liability_list, acc_obj)
                # confirm_margin_account(acc_obj)
                confirm_margin_flow_list(flow_list)
            elif file_name.lower().endswith('.rar'):
                os.remove(os.path.join(folder_path, file_name))
            elif file_name.lower().endswith('zip'):
                with zipfile.ZipFile(os.path.join(folder_path, file_name), mode='r') as z_file:
                    for sub_file in z_file.namelist():
                        assert isinstance(sub_file, str)
                        z_file.extract(sub_file, path=folder_path)
                os.remove(os.path.join(folder_path, file_name))
            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    future_flow = {
        'security_code': ['合约', ], 'security_name': ['品种', ], 'trade_class': ['买卖', ],
        'trade_price': ['成交价', ], 'trade_volume': ['手数', ], 'offset': ['开平', ],
        'trade_amount': ['成交额', ], 'trade_fee': ['手续费', ], 'investment_tag': ['投保', ],
        None: ['成交日期', '交易所', '权利金收支', ],
    }
    future_acc = {
        'capital_sum': ['期末结存', ], 'last_capital_sum': ['期初结存', ], 'cash_amount': ['可用资金', ],
        'market_sum': ['保证金占用', ], 'market_pl': ['持仓盯市盈亏', ], 'out_in_cash': ['出入金', ],
        'trade_fee': ['手续费', ], 'realized_pl': ['平仓盈亏', ],
    }
    future_pos = {
        'security_code': ['合约', ], 'security_name': ['品种', ],
        'long_position': ['买持', ], 'short_position': ['卖持', ],
        'buy_average_cost': ['买均价', ], 'sell_average_cost': ['卖均价', ],
        'prev_settlement': ['昨结算', ], 'settlement_price': ['今结算', ],
        'market_pl': ['持仓盯市盈亏', ], 'investment_tag': ['投保', ],
        'long_mkv': ['多头期权市值', ], 'short_mkv': ['空头期权市值', ], 'margin': ['保证金占用', ],
        None: ['交易所', '浮动盈亏', ],
    }

    @staticmethod
    def load_future(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        id_product_map = {
            '8001001277': '久铭50指数', '8001002072': '静康创新稳健1号',
        }
        BatchDecompression(folder_path, folder_path, ['盯市', '浮动']).batchExt()
        for file_name in os.listdir(folder_path):
            AnXin.log.debug_running(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('txt'):
                if '盯市' not in file_name:
                    continue
                pro_id = re.match(r"(\d+)帐单", file_name).group(1)
                product_name = id_product_map[pro_id]
                assert product_name in PRODUCT_NAME_RANGE, '{} {}'.format(product_name, file_name)
                if product_name not in result_dict:
                    result_dict[product_name] = None
                    # result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                # identified_dict = {
                #     'product': product_name, 'date': date,
                #     'institution': AnXin.folder_institution_map[folder_name],
                #     'currency': 'RMB', 'account_type': folder_name,
                #     'offset': OFFSET_OPEN,
                # }
                # content = open(
                #     os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                # ).read()
                #
                # matcher = TextMapper(AnXin.future_acc, identified_dict, )
                # try:
                #     acc = re.search(r"资金状况([\w\W]*)持仓明细", content, re.M).groups()
                # except AttributeError:
                #     acc = re.search(r"资金状况([\w\W]*)持仓汇总", content, re.M).groups()
                # assert len(acc) == 1, 'wrong re implication'
                # acc = acc[0]
                # acc = re.sub(r'[a-zA-Z]', '', acc).replace('/', '').replace('(', '').replace(')', '')
                # acc = acc.replace('手 续 费', '手续费').replace('出 入 金', '出入金')
                # matcher.map_horizontal(acc)
                # acc_obj = matcher.form_new()
                # result_dict[product_name]['account'] = acc_obj
                #
                # matcher = TextMapper(AnXin.future_pos, identified_dict, )
                # matcher.set_line_sep('|')
                # pos = re.search(r"持仓汇总([\w\W]*)共\s\d+条", content, re.M).groups()
                # assert len(pos) == 1, 'wrong re implication'
                # pos_list = matcher.map(pos[0])
                # result_dict[product_name]['position'] = pos_list
                #
                # # matcher = TextMapper(ChangJiang.future_flow, identified_dict, )
                # # try:
                # #     flow = re.search(r"成交记录([\w\W]*)共\d+条[^共条持仓明细]+持仓明细", content, re.M).groups()
                # # except AttributeError:
                # #     flow = tuple()
                # # if len(flow) == 0:
                # #     flow_list = list()
                # # elif len(flow) == 1:
                # #     flow_list = matcher.map(flow[0])
                # # else:
                # #     raise RuntimeError(flow)
                # # match_future_pos_acc(pos_list, acc_obj)
                # # confirm_future_flow_list(flow_list)
                # flow_list = list()
                # result_dict[product_name]['flow'] = flow_list
                #
                # confirm_future_account(acc_obj)
                # match_future_pos_acc(pos_list, acc_obj)

            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    option_pos = {
        'security_code': ['合约', ],  # 'security_name': ['合约名称', ],
        'warehouse_class': ['持仓方向', ],  # 'warehouse_volume': ['当前数量', ],  # 'warehouse_cost': ['', ],
        'settlement_price': ['结算价', ], 'hold_volume': ['持仓数量', ],
        'market_value': ['市值', ],
        'None': ['交易板块', '期权类别', '维持保证金'],
    }
    option_acc = {
        'cash_amount': ['可用资金', ], 'market_sum': ['权利方市值', ], 'capital_sum': ['市值权益', ],
        'cash_available': ['可用资金', ],
        'None': ['冻结金额', '已用保证金', '可用保证金', '币种'],
    }
    option_flow = {
        'security_code': ['合约编码', ], 'security_name': ['合约简称', ],
        'warehouse_class': ['持仓类别', ], 'trade_class': ['业务名称', ], 'offset': ['开平仓方向', ],
        'trade_price': ['价格', ], 'trade_volume': ['数量', ], 'trade_amount': ['成交金额', ],
        'trade_fee': ['费用', ], 'cash_rest': ['当前余额', ], 'reserve_tag': ['备兑标志', ],
        'None': ['成交时间', '交易类别', '证券代码', '权利金收支', ],
    }
    option_acc_flow = {
        'trade_class': ['业务标志', ], 'cash_move': ['发生金额', ], 'cash_rest': ['后资金额', ],
        'None': ['发生日期', '当前时间', '币种类别', ]
    }
    option_id_product_map = {
        '880100001226': '收益2号',
        '668801000035': '收益2号',
        '668801000039': '专享1号',
        '668801000040': '久盈2号',
        '661026000005': '久铭1号',  # @wave
        '661026000006': '久铭50指数',  # @wave
        '661026000008': '静康1号',  # @wave
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        from jetend.structures import TextMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            AnXin.log.debug(file_name)
            if file_name.startswith('.'):
                continue
            elif file_name.lower().endswith('txt'):
                try:
                    pro_id = re.search(r"(\d+)", file_name).group(1)
                    product_name = AnXin.option_id_product_map[pro_id]
                except AttributeError:
                    if '专享一号' in file_name:
                        product_name = '专享1号'
                    else:
                        raise NotImplementedError(file_name)
                except KeyError:
                    if '久盈2号' in file_name:
                        product_name = '久盈2号'
                    else:
                        raise NotImplementedError(file_name)

                if product_name not in result_dict:
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name

                # content = open(
                #     os.path.join(folder_path, file_name), mode='r', encoding='gb18030', errors='ignore'
                # ).read()
                # identified_dict = {
                #     'date': date, 'product': product_name, 'currency': 'RMB', 'account_type': folder_name,
                #     'institution': AnXin.folder_institution_map[folder_name],
                # }
                #
                # matcher = TextMapper(AnXin.option_acc, identified_dict)
                # acc = re.search(r"资金信息([\w\W]*)资金变动清单", content, re.M).group(1)
                # acc_obj = matcher.map(acc)[0]
                # result_dict[product_name]['account'] = acc_obj
                #
                # matcher = TextMapper(XingYe.option_pos, identified_dict)
                # matcher.ignore_cell.update(['成本价'])
                # matcher.ignore_line.update(['合计'])
                # pos = re.search(r"合约持仓清单([\w\W]*)获取对账单", content, re.M).group(1)
                # pos_list = matcher.map(pos)
                # result_dict[product_name]['position'] = pos_list
                #
                # matcher = TextMapper(XingYe.option_flow, identified_dict)
                # flow = re.search(r"获取对账单([\w\W]*)组合持仓清单", content, re.M).group(1)
                # matcher.ignore_line.update(['合计'])
                # flow_list = matcher.map(flow)
                # for flow_obj in flow_list:
                #     assert 'trade_class' in flow_obj, flow_obj
                #     if str_check(flow_obj['trade_class']) in ('买',) and str_check(flow_obj['offset']) in ('开仓',):
                #         flow_obj['cash_move'] = - abs(
                #             float_check(flow_obj['trade_amount'])
                #         ) - abs(float_check(flow_obj['trade_fee']))
                #     else:
                #         raise NotImplementedError(flow_obj)
                # result_dict[product_name]['flow'] = flow_list
                #
                # # matcher = TextMapper(XingYe.option_acc_flow, identified_dict)
                # # flow = re.search(r"资金变动清单([\w\W]*)合约持仓清单", content, re.M).group(1)
                # # matcher.ignore_line.update(['合计'])
                # # # for acc_flow in matcher.map(flow):
                # # #     assert isinstance(acc_flow, RawOptionFlow)
                # # #     acc_flow.trade_price = acc_flow.cash_move
                # # #     acc_flow.trade_volume = 1
                # # #     flow_list.append(acc_flow)
                # # #
                # # # pos_list = DataList(RawOptionPosition)
                #
                # confirm_option_flow_list(flow_list)
                # match_option_pos_acc(pos_list, acc_obj)
            # elif file_name.lower().endswith('rar'):
            #     os.remove(os.path.join(folder_path, file_name))
            elif file_name.lower().endswith('xls'):
                pro_id = re.search(r"\w+_(\d+)", file_name).group(1)
                product_name = AnXin.option_id_product_map[pro_id]

                if product_name not in result_dict:
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
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
        from jetend.Constants import PRODUCT_CODE_NAME_MAP
        from utils import identify_valuation_records
        file_name = file_path.split(os.path.sep)[-1]
        AnXin.log.debug_running('读取托管估值表', file_name)
        # 文件名：SCH044_久铭专享1号私募证券投资基金_2019-09-16估值表
        try:
            product_code, product, date_str = re.search(r'([A-Za-z0-9]+)_(\w+)私募[^\d]+_(\d+-\d+-\d+)',
                                                        file_name).groups()
        except AttributeError:
            product_code, product, date_str = re.search(r'([A-Za-z0-9]+)_(\w+)私募[^\d]+_(\d+\d+\d+)',
                                                        file_name).groups()
        product_name = PRODUCT_CODE_NAME_MAP[product_code]
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            date = datetime.datetime.strptime(date_str, '%Y%m%d')

        hand_dict = {
            'product_code': product_code, 'product_name': product_name, 'date': date,
            'file_name': file_name, 'institution': '安信证券',
        }
        mapper = ExcelMapper(AnXin.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        return identify_valuation_records(m_list, hand_dict)
        # # 读取净值、份额、净资产、税费
        # for m_dict in m_list:
        #     assert isinstance(m_dict, dict)
        #     account_code = check_str_element(m_dict, 'account_code', '科目代码')
        #     account_name = m_dict.get('account_name', '')
        #     # account_name = check_str_element(m_dict, 'account_name', '科目名称')
        #     if re.sub(r'\W', '', account_code) in ('单位净值', '基金单位净值', '今日单位净值'):
        #         result_dict['net_value'] = float_check(m_dict['account_name'])
        #     if re.sub(r'\W', '', account_code) in ('资产净值', '基金资产净值'):
        #         result_dict['net_asset'] = float_check(m_dict['total_market_value'])
        #     if re.sub(r'\W', '', account_code) == '实收资本':
        #         result_dict['fund_shares'] = float_check(m_dict['total_market_value'])
        #     if '税' in account_name:
        #         if len(str_check(account_code)) == 4:
        #             assert 'tax_payable' not in result_dict, str('重复读取应交税费 {} {}'.format(file_path, m_dict))
        #             result_dict['tax_payable'] = float_check(m_dict['total_market_value'])
        #         elif len(str_check(m_dict['account_code'])) > 4:
        #             pass
        #         else:
        #             raise NotImplementedError('{} {}'.format(file_path, m_dict))
        # check_float_element(result_dict, 'net_value', '单位净值')
        # check_float_element(result_dict, 'net_asset', '净资产')
        # check_float_element(result_dict, 'fund_shares', '基金份额')
        # result_dict.update(hand_dict)
        # return result_dict


if __name__ == '__main__':
    print(AnXin.load_normal(
        r'D:\Documents\久铭产品交割单20190906\安信普通账户',
        datetime.date(2019, 9, 6),
    ))
