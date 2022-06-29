# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import xlrd
import shutil
import zipfile

# from unrar import rarfile

from Abstracts import AbstractInstitution
from Checker import *

from JournalLoader.Move import Move


class ZhongJin(AbstractInstitution):
    """中金"""
    folder_institution_map = {
        '中金普通账户': '中金',
        '中金两融账户': '中金两融',
        '中金期权账户': '中金期权',
    }
    normal_pos = {
        'cash_account': ['资金帐号', '股东帐号'], 'shareholder_code': ['证券账号', ], 'security_code': ['证券代码', ],
        'security_name': ['证券名称', ], 'hold_volume': ['证券余额', '股份余额'],
        'weight_average_cost': ['参考成本', '参考成本价', ],
        'close_price': ['收盘价', '参考市价', ], 'market_value': ['参考市值', ], 'currency': ['币种', ],
        'None': ['日期', '客户姓名', '交易市场', '冻结数量', '可用数量', '股份可用', '交易冻结', '参考盈亏'],
    }
    normal_flow = {
        'capital_account': ['资金帐号', '股东帐号'], 'currency': ['币种', ], 'trade_class': ['业务标志', '摘要', ],
        'shareholder_code': ['股东代码', ], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'trade_volume': ['成交数量', '成交股数'], 'trade_price': ['成交均价', '成交价格'], 'trade_amount': ['成交金额', ],
        'cash_move': ['清算金额', '发生金额', ],
        'None': [
            '日期', '客户姓名', '交易市场', '手续费', '印花税', '过户费', '发生日期', '成交币种', '港股汇率', '发生币种',
            '资金余额', '所得税', '净手续费', '经手证管费','交易规费', '清算费', '交易单费', '尾差修正', '财汇局征费'
        ]
    }
    normal_acc = {
        'capital_account': ['资金帐号', '资产账户'], 'currency': ['币种', ], 'cash_amount': ['资金余额', ],
        'cash_available': ['可用余额', ],
        'market_sum': ['证券市值', '资产市值', ], 'capital_sum': ['资产总值', '总资产', ],
        'None': ['日期', '营业部', '客户姓名', '冻结资金', '可用资金', '可取资金', '客户代码', '港股通资金可用'],
    }
    hk_pos = {
        'cash_account': ['资金帐号', ], 'shareholder_code': ['证券账号', ], 'security_code': ['证券代码', ],
        'security_name': ['证券名称', ], 'hold_volume': ['证券余额', ], 'weight_average_cost': ['参考成本'],
        'close_price': ['收盘价', ], 'market_value': ['参考市值', ], 'currency': ['币种', ],
        'None': ['日期', '客户姓名', '交易市场', '可用数量', '未回买入数量', '未回卖出数量',]
    }
    normal_id_product_map = {
        '210000420': '久盈2号', '210000425': '久铭8号', '210000511': '久铭1号',
        '830304246': '稳健17号', '830304288': '稳健8号',
        '12928637': '全球丰收1号',
    }

    @staticmethod
    def load_normal(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            ZhongJin.log.debug_running(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~') or '副本' in file_name:
                continue
            elif file_name.lower().endswith('pdf'):
                continue
            elif file_name.lower().endswith('xls'):
                if '信用' in file_name:
                    target_path = folder_path.replace('中金普通', '中金两融')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                if '期权' in file_name:
                    target_path = folder_path.replace('中金普通', '中金期权')
                    if not os.path.exists(target_path):
                        os.makedirs(target_path)
                    shutil.move(os.path.join(folder_path, file_name), target_path)
                    continue
                if file_name.startswith('上海久铭'):
                    product_name, date_str = re.match(r"上海久铭-([^\d]+\d+[号指数]+)_\w+_(\d+)", file_name).groups()
                elif file_name.startswith('久铭'):
                    if '私募证券' in file_name:
                        product_name, date_str = re.match(r"([^\d]+\d+[号指数]+)私募\w+_\w+_(\d+)", file_name).groups()
                    else:
                        product_name, date_str = re.match(r"([^\d]+\d+[号指数]+)_\w+_(\d+)", file_name).groups()
                else:
                    raise NotImplementedError(file_name)
                # product_name = loader.env.product_name_map[product_name]
                if product_name[:4] in ('久铭久盈', '久铭稳健', '久铭创新', '久铭专享', ):
                    product_name = product_name.replace('久铭', '')
                else:
                    pass
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date_str, date)
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': ZhongJin.folder_institution_map[folder_name],
                    'offset': OFFSET_OPEN,
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                # 初始化result_dict
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ZhongJin.normal_flow, identified_dict, )
                flow_list = matcher.map(content.sheet_by_name('交收汇总'))
                # print(flow_list)
                # 解决久铭8号、久铭1号成交额跟成交价格、成交数量计算结果差距超过1的的情况，例如0625那天
                if product_name in ('久铭8号', '久铭1号'):
                    for flow in flow_list:
                        if flow['trade_class'] in (
                                '银行转存', '港股通组合费收取', '股息红利税补缴', '利息结算', '股息入帐', '股通组合费收', '银行转取',
                                'ETF现金替代退款', '利息归本', '交收资金冻结'
                        ):
                            continue
                        else:
                            flow['trade_price'] = float_check(flow['trade_amount'])/float_check(flow['trade_volume'])
                # print(flow_list)
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhongJin.normal_pos, identified_dict, )
                pos_list = matcher.map(content.sheet_by_name('持仓信息'))
                matcher = ExcelMapper(ZhongJin.hk_pos, identified_dict, )
                pos_list.extend(matcher.map(content.sheet_by_name('港股持仓')))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongJin.normal_acc, identified_dict, )
                acc_obj = matcher.map(content.sheet_by_name('资产信息'))[0]
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('xlsx'):
                # 普通柜台对账单_20200331-久铭全球丰收1号(12928637)
                try:
                    date_str, some_id = re.match(r'\w+_(\d+)-\w+\((\d+)\)', file_name).groups()
                except:
                    continue
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date, file_name)
                product_name = ZhongJin.normal_id_product_map[some_id]
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': ZhongJin.folder_institution_map[folder_name],
                    'offset': OFFSET_OPEN, 'currency': 'RMB',
                }
                assert product_name in PRODUCT_NAME_RANGE, product_name
                # 初始化result_dict
                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                matcher = ExcelMapper(ZhongJin.normal_flow, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                flow_list = matcher.map(content.sheet_by_name('对帐单'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhongJin.normal_pos, identified_dict, )
                matcher.ignore_line.update(['合计', ])
                pos_list = matcher.map(content.sheet_by_name('持仓清单'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongJin.normal_acc, identified_dict, )
                try:
                    acc_obj = matcher.map(content.sheet_by_name('资金情况'))[0]
                except Exception as acc_obj:
                    m = Move(os.path.join(folder_path,file_name))
                    m.output_log(acc_obj)
                    continue
                result_dict[product_name]['account'] = acc_obj

                match_normal_pos_acc(pos_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            elif file_name.lower().endswith('rar') or file_name.lower().endswith('zip'):
                if '交易数据' in file_name or '行情数据' in file_name:
                    os.remove(os.path.join(folder_path, file_name))
                elif '对账单' in file_name:
                    pass
                else:
                    raise NotImplementedError
            elif file_name.lower().endswith('dbf'):
                os.remove(os.path.join(folder_path, file_name))
                continue



            else:
                raise NotImplementedError(file_name)

        return result_dict, product_file_map

    margin_pos = {
        # 'product': [''], 'close_price': ['最新价格', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', ], 'hold_volume': ['证券余额', '股份余额'],
        'weight_average_cost': ['参考成本', '参考成本价'], 'market_value': ['参考市值', ], 'close_price': ['收盘价'],
        # 'total_cost': ['参考成本', ],
        'shareholder_code': ['股东代码', '股东帐号', ],
        'None': ['日期', '客户姓名', '资金帐号', '交易市场', '冻结数量', '质押券数量', '股份可用', '交易冻结', '参考盈亏', ]
    }
    margin_flow = {
        'trade_class': ['业务标志', '摘要代码', ],
        'security_code': ['证券代码', ], 'security_name': ['证券名称', '证券简称', ],
        # 'shareholder_code': ['股东代码', ],
        'trade_volume': ['成交数量', '数量', ], 'trade_price': ['成交均价', '成交价格', ],
        'trade_amount': ['成交金额', ], 'cash_move': ['清算金额', '发生金额', ],
        'None': [
            '日期', '客户姓名', '资金帐号', '交易市场', '手续费', '印花税', '过户费', '发生日期', '业务类型', '资金余额',
            '其他费', '备注信息',
        ],
    }
    margin_acc = {
        'capital_account': ['资金帐号', ], 'cash_available': ['资金可用', ],
        'cash_amount': ['资金余额', ], 'capital_sum': ['资产总值', ], 'market_sum': ['证券市值', '担保证券市值'],
        'total_liability': ['负债总额', '负债合计', ], 'liability_principal': ['融资负债金额', '融资余额', ],
        'liability_amount_interest': ['应付利息及费用', '未了结融资利息'],
        'liability_amount_for_pay': ['已结未付融资利息', ], 'liability_amount_fee': ['融资费用', ],
        'payback_date': ['合约到期日', ],
        # 'interest_payable': ['未了结融资利息', ],
        # 'fee_payable': ['融资费用', ],
        None: [
            '日期', '营业部', '客户姓名', '授信额度', '可用授信额度', '保证金可用余额', '融券负债金额', '维持担保比例',
            '货币代码', '异常冻结', '交易冻结', '在途资金', '在途可用', '融资保证金', '融券市值', '融券费用',
            '未了结融券利息', '融券保证金', '净资产',
        ]
    }

    margin_liability = {
        'contract_date': ['日期', '合约日期'], 'security_code': ['证券代码', ], 'security_name': ['证券名称', ],
        'contract_type': ['负债类别', '合约类型'], 'contract_volume': ['交易数量', '合约数量'],
        'contract_amount': ['负债金额', '合约金额', ],
        'interest_payable': ['负债利息', '剩余利息'], 'payback_date': ['到期日期', '合约到期日', ],
        'fee_payable': ['未了结费用', '合约费用'],
        None: [
            '资金帐号', '客户姓名', '已还款金额', '负债数量', '已还券数量', '开始日期', '利率', '市场', '合约序号',
            '已偿还金额', '剩余金额', '已偿还数量', '剩余数量', '委托价格', '委托数量', '委托金额',
        ]
    }
    margin_id_product_map = {
        '12988681': '全球丰收1号',
    }

    @staticmethod
    def load_margin(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()

        for file_name in os.listdir(folder_path):
            ZhongJin.log.debug(file_name)
            # 忽略隐藏文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xls'):
                if file_name.startswith('久铭创新稳健6号'):
                    product_name = '创新稳健6号'
                else:
                    raise NotImplementedError(file_name)
                # some_id = re.match(r"(\d+)", file_name).groups()[0]

                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': ZhongJin.folder_institution_map[folder_name], 'currency': 'RMB',
                    'offset': OFFSET_OPEN,
                }
                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                matcher = ExcelMapper(ZhongJin.margin_flow, identified_dict, )
                matcher.ignore_line.update(['合计'])
                flow_list = matcher.map(content.sheet_by_name('交收汇总'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhongJin.margin_pos, identified_dict, )
                pos_list = matcher.map(content.sheet_by_name('持仓信息'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongJin.margin_liability, identified_dict, )
                liability_list = matcher.map(content.sheet_by_name('负债明细'))
                for obj in liability_list:
                    obj['fee_payable'] = 0.0
                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(ZhongJin.margin_acc, identified_dict)
                acc_obj = matcher.map(content.sheet_by_name('资产及负债汇总'))[0]
                acc_obj['cash_available'] = acc_obj['cash_amount']
                acc_obj['liability_amount_fee'] = 0.0
                acc_obj['liability_amount_for_pay'] = 0.0
                result_dict[product_name]['account'] = acc_obj

                match_margin_pos_acc(pos_list, acc_obj)
                match_margin_liability_acc(liability_list, acc_obj)
                confirm_normal_flow_list(flow_list)
            elif file_name.lower().endswith('xlsx'):
                # 信用柜台对帐单_20200331-久铭全球丰收1号(12988681)
                try:
                    date_str, some_id = re.match(r'\w+_(\d+)-\w+\((\d+)\)', file_name).groups()
                except:
                    continue
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date, file_name)
                product_name = ZhongJin.margin_id_product_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, file_name
                identified_dict = {
                    'product': product_name, 'date': date, 'account_type': folder_name,
                    'institution': ZhongJin.folder_institution_map[folder_name], 'currency': 'RMB',
                    'offset': OFFSET_OPEN,
                }
                content = xlrd.open_workbook(os.path.join(folder_path, file_name))

                if product_name not in result_dict:
                    result_dict[product_name] = dict()
                product_file_map[product_name] = file_name

                matcher = ExcelMapper(ZhongJin.margin_flow, identified_dict, )
                matcher.ignore_line.update(['合计'])
                flow_list = matcher.map(content.sheet_by_name('业务流水'))
                result_dict[product_name]['flow'] = flow_list

                matcher = ExcelMapper(ZhongJin.margin_pos, identified_dict, )
                pos_list = matcher.map(content.sheet_by_name('当前资产'))
                result_dict[product_name]['position'] = pos_list

                matcher = ExcelMapper(ZhongJin.margin_liability, identified_dict, )
                liability_list = matcher.map(content.sheet_by_name('负债明细'))
                # for obj in liability_list:
                #     obj['fee_payable'] = 0.0
                result_dict[product_name]['liabilities'] = liability_list

                matcher = ExcelMapper(ZhongJin.margin_acc, identified_dict)
                matcher.ignore_line.update(['合计'])
                acc_obj = matcher.map(content.sheet_by_name('资产负债情况'))[0]
                # acc_obj['cash_available'] = acc_obj['cash_amount']
                # acc_obj['liability_amount_fee'] = 0.0
                acc_obj['liability_amount_for_pay'] = 0.0
                matcher = ExcelMapper(ZhongJin.margin_acc, identified_dict)
                matcher.ignore_line.update(['合计'])
                acc_obj_part = matcher.map(content.sheet_by_name('负债情况'))[0]
                acc_obj.update(acc_obj_part)
                acc_obj['market_sum'] = sum([float_check(var['market_value']) for var in pos_list])
                acc_obj['capital_sum'] = acc_obj['market_sum'] + float_check(acc_obj['cash_amount'])
                result_dict[product_name]['account'] = acc_obj

                match_margin_pos_acc(pos_list, acc_obj)
                match_margin_liability_acc(liability_list, acc_obj)
                confirm_normal_flow_list(flow_list)

            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map

    option_acc = {
        'capital_account': ['资产账户', ],
        'market_sum': ['权利仓市值', ], 'cash_amount': ['资金可用金额', ], 'capital_sum': ['期末结存', ],
        'None': [
            '交易日期', '机构名称', '客户代码', '客户名称', '期初结存', '可用资金', '行权资金冻结金额', '行权冻结维持保证金',
            '占用保证金', '垫付资金', '预计垫资罚息', '归还垫资', '归还罚息', '减免罚息', '卖券收入', '利息归本',
            '利息税', '银衍入金', '银衍出金', '权利金收付', '行权收付', '手续费', '结算费', '经手费', '交易所经手费',
            '行权过户费', '行权结算费', '行权手续费', '浮动盈亏', '占用买入额度', '买入额度', '义务仓市值', '保证金风险率',
            '应追加保证金', '追保通知内容', '客户确认标志', '客户确认时间', '行权锁定保证金', '转入金额', '转出金额',
            '货币代码',
        ],
    }
    option_id_product_map = {
        '12985075': '全球丰收1号',
    }

    @staticmethod
    def load_option(folder_path: str, date: datetime.date):
        from jetend.structures import ExcelMapper
        # from structures import DataList
        # from sheets.raws.RawOption import RawOptionFlow, RawOptionPosition
        folder_name = folder_path.split(os.path.sep)[-1]
        result_dict, product_file_map = dict(), dict()
        for file_name in os.listdir(folder_path):
            if file_name.startswith('.') or file_name.startswith('~'):
                continue
            elif file_name.lower().endswith('xlsx'):
                # 期权柜台对账单_20200331-久铭全球丰收1号(12985075)
                date_str, some_id = re.match(r'\w+_(\d+)-\w+\((\d+)\)', file_name).groups()
                assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date, file_name)
                product_name = ZhongJin.option_id_product_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, file_name
                assert date.strftime('%Y%m%d') in file_name, '{} {}'.format(date, file_name)
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
                # identified_dict = {
                #     'product': product_name, 'date': date, 'account_type': folder_path, 'currency': 'RMB',
                #     'institution': ZhongJin.folder_institution_map[folder_name],
                #     'warehouse_class': '权利仓',
                # }
                # content = xlrd.open_workbook(os.path.join(folder_path, file_name))
                #
                # matcher = ExcelMapper(ZhongJinCaiFu.option_acc, identified_dict)
                # acc_obj = matcher.map(content.sheet_by_name('客户结算单查询'))[0]
                # result_dict[product_name]['account'] = acc_obj
                #
                # # option_flow_filename = '历史交收明细查询{}.xls'.format(pro_id)
                # # if os.path.exists(os.listdir(folder_path, option_flow_filename)):
                # #     content = xlrd.open_workbook(os.listdir(folder, option_flow_filename))
                # #     matcher = ExcelMapper(GuoJun.option_flow, identified_dict)
                # #     flow_list = matcher.map(content.sheet_by_name(option_flow_filename.split('.')[0]))
                # # else:
                # #     flow_list = DataList(RawOptionFlow)
                # flow_list = list()
                # result_dict[product_name]['flow'] = flow_list
                #
                # pos_list = list()
                # result_dict[product_name]['position'] = pos_list
                #
                # confirm_option_flow_list(flow_list)
                # match_option_pos_acc(pos_list, acc_obj)
            elif file_name.lower().endswith('xls'):
                # 期权柜台对账单_20200331-久铭全球丰收1号(12985075)
                if '创新稳健6号' in file_name:
                    product_name = '创新稳健6号'
                else:
                    raise NotImplementedError(file_name)
                # date_str, some_id = re.match(r'\w+_(\d+)-\w+\((\d+)\)', file_name).groups()
                # assert date_str == date.strftime('%Y%m%d'), '{} {}'.format(date, file_name)
                # product_name = ZhongJin.option_id_product_map[some_id]
                assert product_name in PRODUCT_NAME_RANGE, file_name
                assert date.strftime('%Y%m%d') in file_name, '{} {}'.format(date, file_name)
                if product_name not in result_dict:
                    # result_dict[product_name] = dict()
                    result_dict[product_name] = None
                product_file_map[product_name] = file_name
            else:
                raise NotImplementedError(file_name)
        return result_dict, product_file_map


if __name__ == '__main__':
    print(ZhongJin.load_normal(r'D:\NutStore\久铭产品交割单\2019年\久铭产品交割单20190701\中金普通账户', datetime.date(2019, 7, 1)))
