# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime
import os

from xlsxwriter import Workbook

from jetend.Constants import *
from jetend.DataCheck import *

from jetend.modules.jmInfoBoard import jmInfoBoard
from jetend.structures import List
from jetend.jmSheets import *


def output_valuation_sheet(info_board: jmInfoBoard, product: str, date: datetime.date, output_folder: str):
    """根据会计凭证输出非托管产品估值表表单"""

    product_id = info_board.find_product_code_by_name(product)
    product_info = info_board.find_product_info_by_code(product_id)
    file_name = '{}_{}资产估值表_{}'.format(product_id, product_info.full_name, date)

    os.makedirs(os.path.join(output_folder, '{}'.format(date)), exist_ok=True)
    output_path = os.path.expanduser(os.path.join(output_folder, '{}'.format(date), '{}.xlsx'.format(file_name)))

    book = Workbook(filename=output_path)
    excel_formats = {
        'bold': book.add_format({'bold': True, }), 'center': book.add_format({'align': 'center'}),
        'date': book.add_format({'num_format': 'yyyy-mm-dd'}),
        'number2': book.add_format({'num_format': '#,##0.00'}),
        'number4': book.add_format({'num_format': '#,##0.0000'}),
        'percentage': book.add_format({'num_format': '0.00%'}),
        'bold_number2': book.add_format({'num_format': '#,##0.00', 'bold': True, }, ),
        'bold_number3': book.add_format({'num_format': '#,##0.000', 'bold': True, }, ),
        'bold_number4': book.add_format({'num_format': '#,##0.0000', 'bold': True, }, ),
    }
    formula_dict = {
        # '资产成本占比': """=G4/INDEX(B:B,MATCH("资产合计",A:A,0),0)""",
        # '资产市值占比': """=J4/INDEX(B:B,MATCH("资产合计",A:A,0),0)""",
        # '负债成本占比': """=G4/INDEX(B:B,MATCH("负债合计",A:A,0),0)""",
        # '负债市值占比': """=J4/INDEX(B:B,MATCH("负债合计",A:A,0),0)""",
        '净资产成本占比': """=G{}/INDEX(B:B,MATCH("净资产",A:A,0),0)""",
        '净资产市值占比': """=J{}/INDEX(B:B,MATCH("净资产",A:A,0),0)""",
    }
    sheet = book.add_worksheet(name='Sheet1')
    sheet.set_column(0, 0, width=18, )
    sheet.set_column(1, 1, width=50, )
    sheet.set_column(2, 3, width=5, )
    sheet.set_column(4, 4, width=14, )
    sheet.set_column(5, 5, width=15, )
    sheet.set_column(6, 6, width=20, )
    sheet.set_column(7, 8, width=10, )
    sheet.set_column(9, 9, width=20, )
    sheet.set_column(10, 10, width=10, )
    sheet.set_column(11, 11, width=20, )
    sheet.set_column(12, 13, width=9, )

    acc_list = List.from_pd(EntryAccount, info_board.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM 会计科目余额表 WHERE 产品 = '{}' AND 日期 = '{}';""".format(product, date)
    ))
    for obj in acc_list:        # 市值保留两位
        obj.set_attr('net_value', round(obj.net_value, 2))
    pos_list = List.from_pd(EntryPosition, info_board.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM 会计产品持仓表 WHERE 产品 = '{}' AND 日期 = '{}';""".format(product, date)
    ))
    total_asset_line, total_liability_line = set(), set()

    line = 0
    # sheet.write_string(line, 0, file_name, cell_format=excel_formats['bold'])
    sheet.merge_range(line, 0, line, 13, file_name, cell_format=book.add_format(
        {'align': 'center', 'bold': True, }
    ))

    line += 1
    column_list = [
        '科目代码', '科目名称', '币种', '汇率', '数量', '单位成本', '成本-本币', '成本占比', '行情', '市值-本币',
        '市值占比', '估值增值-本币', '停牌信息', '权益信息'
    ]
    for i in range(len(column_list)):
        sheet.write_string(line, i, column_list[i], cell_format=excel_formats['bold'])

    sub_acc_list = acc_list.find_value_where(account_name='银行存款')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1002
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '银行存款', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '银行存款_活期存款账户_{}'.format(obj.sub_account), )
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 6, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = acc_list.find_value_where(account_name='存出保证金')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1031
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '存出保证金', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            if is_valid_str(obj.base_account):
                sheet.write_string(line, 1, '存出保证金_{}_{}'.format(obj.sub_account, obj.base_account), )
            else:
                sheet.write_string(line, 1, '存出保证金_{}'.format(obj.sub_account), )
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 6, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = pos_list.find_value_where(account_name='股票投资')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1102
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '股票投资', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 11, '=SUM(L{}:L{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        for obj in sub_acc_list:
            line += 1
            sheet.write_string(line, 0, '{0}.{1}'.format(account_code, obj.security_code), )
            sheet.write_string(line, 1, '{}_{}'.format(obj.security_name, obj.institution, ), )
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 4, obj.hold_volume, cell_format=excel_formats['number2'])
            sheet.write_number(line, 5, obj.weight_average_cost, cell_format=excel_formats['number2'])
            sheet.write_number(line, 6, obj.total_cost, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 8, obj.close_price, cell_format=excel_formats['number2'])
            sheet.write_number(line, 9, obj.market_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_formula(line, 11, """=J{}-G{}""".format(line + 1, line + 1),
                                cell_format=excel_formats['number2'])

    sub_acc_list = pos_list.find_value_where(account_name='债券投资')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1103
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '债券投资', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 11, '=SUM(L{}:L{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        for obj in sub_acc_list:
            line += 1
            sheet.write_string(line, 0, '{0}.{1}'.format(account_code, obj.security_code), )
            sheet.write_string(line, 1, '{}_{}'.format(obj.security_name, obj.institution, ), )
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 4, obj.hold_volume, cell_format=excel_formats['number2'])
            sheet.write_number(line, 5, obj.weight_average_cost, cell_format=excel_formats['number2'])
            sheet.write_number(line, 6, obj.total_cost, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 8, obj.close_price, cell_format=excel_formats['number2'])
            sheet.write_number(line, 9, obj.market_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_formula(line, 11, """=J{}-G{}""".format(line + 1, line + 1),
                                cell_format=excel_formats['number2'])

    sub_acc_list = pos_list.find_value_where(account_name='基金投资')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1105
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '基金投资', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 11, '=SUM(L{}:L{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        for obj in sub_acc_list:
            line += 1
            sheet.write_string(line, 0, '{0}.{1}'.format(account_code, obj.security_code), )
            sheet.write_string(line, 1, '{}_{}'.format(obj.security_name, obj.institution, ), )
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 4, obj.hold_volume, cell_format=excel_formats['number2'])
            sheet.write_number(line, 5, obj.weight_average_cost, cell_format=excel_formats['number2'])
            sheet.write_number(line, 6, obj.total_cost, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 8, obj.close_price, cell_format=excel_formats['number2'])
            sheet.write_number(line, 9, obj.market_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_formula(line, 11, """=J{}-G{}""".format(line + 1, line + 1),
                                cell_format=excel_formats['number2'])

    sub_acc_list = pos_list.find_value_where(account_name='权证投资')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1106
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '权证投资', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 11, '=SUM(L{}:L{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        for obj in sub_acc_list:
            line += 1
            sheet.write_string(line, 0, '{0}.{1}'.format(account_code, obj.security_code), )
            sheet.write_string(line, 1, '{}_{}'.format(obj.security_name, obj.institution, ), )
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 4, obj.hold_volume, cell_format=excel_formats['number2'])
            sheet.write_number(line, 5, obj.weight_average_cost, cell_format=excel_formats['number2'])
            sheet.write_number(line, 6, obj.total_cost, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 8, obj.close_price, cell_format=excel_formats['number2'])
            sheet.write_number(line, 9, obj.market_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_formula(line, 11, """=J{}-G{}""".format(line + 1, line + 1),
                                cell_format=excel_formats['number2'])

    sub_acc_list = List()
    for obj in acc_list.find_value_where(account_name='结算备付金', ):
        if obj.sub_account in ('中信美股', '中信港股',):
            continue
        else:
            sub_acc_list.append(obj)
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1021
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '结算备付金', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 11, '=SUM(L{}:L{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            value_added = acc_list.find_value_where(
                account_name='权证投资', sub_account='估值增值', base_account=obj.base_account
            ).sum_attr('net_value')
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '结算备付金_{}_{}'.format(obj.sub_account, obj.base_account))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 4, 1)
            # sheet.write_number(line, 5, obj.weight_average_cost, cell_format=excel_formats['number2'])
            # sheet.write_number(line, 6, obj.total_cost, cell_format=excel_formats['number2'])
            # sheet.write_number(line, 8, obj.close_price, cell_format=excel_formats['number2'])
            sheet.write_number(line, 6, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, obj.net_value + value_added, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_formula(line, 11, """=J{}-G{}""".format(line + 1, line + 1),
                                cell_format=excel_formats['number2'])

    sub_acc_list = acc_list.find_value_where(account_name='结算备付金', sub_account='中信美股')
    sub_acc_list.extend(acc_list.find_value_where(account_name='结算备付金', sub_account='中信港股'))
    if len(sub_acc_list) > 0:
        raise NotImplementedError(sub_acc_list)
        # line += 1
        # account_code = 1107
        # total_asset_line.add(line + 1)
        # sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        # sheet.write_string(line, 1, '收益互换', cell_format=excel_formats['bold'])
        # sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        # sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
        #                     cell_format=excel_formats['bold_number2'])
        # sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
        #                     cell_format=excel_formats['percentage'])
        # sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
        #                     cell_format=excel_formats['bold_number2'])
        # sheet.write_formula(line, 11, '=SUM(L{}:L{})'.format(line + 2, line + 1 + len(sub_acc_list)),
        #                     cell_format=excel_formats['bold_number2'])
        # sub_level = 0
        # for obj in sub_acc_list:
        #     line += 1
        #     sub_level += 1
        #     rece_obj = acc_list.find_value(account_name='应付利息', sub_account=obj.sub_account)
        #     sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
        #     sheet.write_string(line, 1, '收益互换-{}（中信证券）-{}'.format(
        #         product_info.full_name, obj.sub_account[-2:]), )
        #     sheet.write_string(line, 2, 'CNY', )
        #     sheet.write_number(line, 3, 1)
        #     sheet.write_number(line, 4, 1)
        #     # sheet.write_number(line, 5, obj.weight_average_cost, cell_format=excel_formats['number2'])
        #     # sheet.write_number(line, 6, obj.total_cost, cell_format=excel_formats['number2'])
        #     sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
        #                     cell_format=excel_formats['percentage'])
        #     # sheet.write_number(line, 8, obj.close_price, cell_format=excel_formats['number2'])
        #     sheet.write_number(line, 9, obj.net_value + rece_obj.net_value, cell_format=excel_formats['number2'])
        #     sheet.write_formula(line, 11, """=J{}-G{}""".format(line + 1, line + 1),
        #                         cell_format=excel_formats['number2'])

    sub_acc_list = acc_list.find_value_where(account_name='收益互换')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1107
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '收益互换', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(
            line + 2, line + 1 + len(sub_acc_list.collect_attr_set('base_account'))
        ), cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(
            line + 2, line + 1 + len(sub_acc_list.collect_attr_set('base_account'))
        ), cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 11, '=SUM(L{}:L{})'.format(
            line + 2, line + 1 + len(sub_acc_list.collect_attr_set('base_account'))
        ), cell_format=excel_formats['bold_number2'])
        sub_level = 0
        # assert len(sub_acc_list.find_value_where(sub_account='估值增值')) == len(
        #     sub_acc_list.find_value_where(sub_account='成本')
        # ), sub_acc_list
        # for obj in sub_acc_list.find_value_where(sub_account='估值增值'):
        for institution in sub_acc_list.collect_attr_set('base_account'):
            #     if obj.sub_account == '成本':
            #         continue
            cost_obj = sub_acc_list.find_value(sub_account='成本', base_account=institution)
            value_obj = sub_acc_list.find_value_where(sub_account='估值增值', base_account=institution)
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '收益互换-{}'.format(institution))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 4, 1)
            sheet.write_number(line, 6, cost_obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            # sheet.write_number(line, 8, obj.close_price, cell_format=excel_formats['number2'])
            sheet.write_number(line, 9, value_obj.sum_attr('net_value') + cost_obj.net_value,
                               cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_formula(line, 11, """=J{}-G{}""".format(line + 1, line + 1),
                                cell_format=excel_formats['number2'])

    sub_acc_list = acc_list.find_value_where(account_name='应收股利')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1203
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '应收股利', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '应收股利_{}_{}'.format(obj.sub_account, obj.base_account))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 6, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = List()
    for obj in acc_list.find_value_where(account_name='应收利息'):
        if abs(obj.net_value) < 0.05:
            continue
        else:
            sub_acc_list.append(obj)
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1204
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '应收利息', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 11, '=SUM(L{}:L{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '应收利息_{}_{}'.format(obj.base_account, obj.sub_account))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 6, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = acc_list.find_value_where(account_name='其他应收款')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 1221
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '其他应收款', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '其他应收款_{}_{}'.format(obj.sub_account, obj.base_account))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 6, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = acc_list.find_value_where(account_name='证券清算款')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 3003
        total_asset_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '证券清算款', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '证券清算款_{}_{}'.format(obj.sub_account, obj.base_account))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 6, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = acc_list.find_value_where(account_name='短期借款')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 2001
        total_liability_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '短期借款', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '短期借款_{}_{}'.format(obj.sub_account, obj.base_account))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 6, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = List()
    for obj in acc_list.find_value_where(account_name='应付利息', ):
        if obj.sub_account in ('中信港股', '中信美股',):
            continue
        else:
            sub_acc_list.append(obj)
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 2231
        total_liability_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '应付利息', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '应付利息{}_{}'.format(obj.sub_account, obj.base_account))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 6, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = acc_list.find_value_where(account_name='应付管理人报酬')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 2206
        total_liability_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '应付管理人报酬', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '应付管理人报酬')
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            assert obj.net_value <= 0, str(obj)
            sheet.write_number(line, 6, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    # sub_acc_list = acc_list.find_value_where(account_name='应付赎回款')
    sub_acc_list = List()
    for obj in acc_list.find_value_where(account_name='应付赎回款'):
        if 0.01 <= abs(obj.net_value) < 0.05:
            assert isinstance(obj, EntryAccount)
            pass
            # print('应付赎回款轧差 {}'.format(str(obj)))
            # obj.set_attr('net_value', 0.0)
        else:
            sub_acc_list.append(obj)
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 2203
        total_liability_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '应付赎回款', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            if 0.01 <= abs(obj.net_value) < 0.05:
                assert isinstance(obj, EntryAccount)
                print('应付赎回款轧差 {}'.format(str(obj)))
                obj.set_attr('net_value', 0.0)
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '应付赎回款_{}_{}'.format(obj.sub_account, obj.base_account, ))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            sheet.write_number(line, 6, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = acc_list.find_value_where(account_name='其他应付款')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 2241
        total_liability_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '其他应付款', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        for obj in sub_acc_list:
            line += 1
            sub_level += 1
            sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
            sheet.write_string(line, 1, '其他应付款_{}_{}'.format(obj.sub_account, obj.base_account))
            sheet.write_string(line, 2, 'CNY', )
            sheet.write_number(line, 3, 1)
            assert obj.net_value <= 0, str(obj)
            sheet.write_number(line, 6, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])
            sheet.write_number(line, 9, - obj.net_value, cell_format=excel_formats['number2'])
            sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                                cell_format=excel_formats['percentage'])

    sub_acc_list = List()
    for obj in acc_list.find_value_where(account_name='应交税费'):
        if '增值税附加' not in obj.sub_account:
            sub_acc_list.append(obj)
    # sub_acc_list = acc_list.find_value_where(account_name='应交税费')
    if len(sub_acc_list) > 0:
        line += 1
        account_code = 2221
        total_liability_line.add(line + 1)
        sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        sheet.write_string(line, 1, '应交税费', cell_format=excel_formats['bold'])
        sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + 2),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + 2),
                            cell_format=excel_formats['bold_number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_level = 0
        # for obj in sub_acc_list:
        line += 1
        sub_level += 1
        sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
        sheet.write_string(line, 1, '应交税费_应交增值税')
        sheet.write_string(line, 2, 'CNY', )
        sheet.write_number(line, 3, 1)
        sheet.write_number(line, 6, - sub_acc_list.sum_attr('net_value'), cell_format=excel_formats['number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_number(line, 9, - sub_acc_list.sum_attr('net_value'), cell_format=excel_formats['number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sub_acc_list = List()
        for obj in acc_list.find_value_where(account_name='应交税费'):
            if '增值税附加' in obj.sub_account:
                sub_acc_list.append(obj)
        line += 1
        sub_level += 1
        sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
        sheet.write_string(line, 1, '应交税费_应交增值税_附加税')
        sheet.write_string(line, 2, 'CNY', )
        sheet.write_number(line, 3, 1)
        sheet.write_number(line, 6, - sub_acc_list.sum_attr('net_value'), cell_format=excel_formats['number2'])
        sheet.write_formula(line, 7, formula_dict['净资产成本占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_number(line, 9, - sub_acc_list.sum_attr('net_value'), cell_format=excel_formats['number2'])
        sheet.write_formula(line, 10, formula_dict['净资产市值占比'].format(line + 1),
                            cell_format=excel_formats['percentage'])

    line += 2
    sheet.write_string(line, 0, '资产合计', cell_format=excel_formats['bold'])
    sheet.write_formula(line, 1, """=J{}""".format(line + 1), cell_format=excel_formats['bold_number2'])
    formula_str = '={}'.format('+'.join(['G{}'.format(var) for var in total_asset_line]))
    sheet.write_formula(line, 6, formula_str, cell_format=excel_formats['bold_number2'])
    formula_str = '={}'.format('+'.join(['J{}'.format(var) for var in total_asset_line]))
    sheet.write_formula(line, 9, formula_str, cell_format=excel_formats['bold_number2'])

    line += 1
    sheet.write_string(line, 0, '负债合计', cell_format=excel_formats['bold'])
    sheet.write_formula(line, 1, """=J{}""".format(line + 1), cell_format=excel_formats['bold_number2'])
    formula_str = '={}'.format('+'.join(['G{}'.format(var) for var in total_liability_line]))
    sheet.write_formula(line, 6, formula_str, cell_format=excel_formats['bold_number2'])
    formula_str = '={}'.format('+'.join(['J{}'.format(var) for var in total_liability_line]))
    sheet.write_formula(line, 9, formula_str, cell_format=excel_formats['bold_number2'])

    line += 1
    sheet.write_string(line, 0, '净资产', cell_format=excel_formats['bold'])
    sheet.write_formula(line, 1, """=J{}""".format(line + 1), cell_format=excel_formats['bold_number2'])
    sheet.write_formula(line, 6, '=G{}-G{}'.format(line - 1, line), cell_format=excel_formats['bold_number2'])
    sheet.write_formula(line, 9, '=J{}-J{}'.format(line - 1, line), cell_format=excel_formats['bold_number2'])

    line += 1
    acc = acc_list.find_value(account_name='实收基金')
    assert isinstance(acc, EntryAccount)
    sheet.write_string(line, 0, '实收资本', cell_format=excel_formats['bold'])
    sheet.write_formula(line, 1, """=J{}""".format(line + 1), cell_format=excel_formats['bold_number2'])
    sheet.write_number(line, 6, abs(acc.net_value), cell_format=book.add_format(
        {'num_format': '#,##0.00', 'bold': True, }, ))
    sheet.write_number(line, 9, abs(acc.net_value), cell_format=book.add_format(
        {'num_format': '#,##0.00', 'bold': True, }, ))

    net_value_obj = List.from_pd(AccountPosition, info_board.db.read_pd_query(
        DataBaseName.management,
        """
        SELECT * FROM 产品余额持仓表 WHERE 产品 = '{}' AND 科目名称 = '单位净值' AND 日期 = '{}'
        ;""".format(product, date)
    ))
    assert len(net_value_obj) == 1, '{} {} 单位净值\n{}'.format(product, date, net_value_obj)
    net_value_obj = net_value_obj[0]

    last_net_value_obj = List.from_pd(AccountPosition, info_board.db.read_pd_query(
        DataBaseName.management,
        """
        SELECT * FROM 产品余额持仓表 WHERE 产品 = '{}' AND 科目名称 = '单位净值' AND 日期 = '{}'
        ;""".format(product, date - datetime.timedelta(days=1))
    ))
    assert len(last_net_value_obj) == 1, last_net_value_obj
    last_net_value_obj = last_net_value_obj[0]

    line += 1
    sheet.write_string(line, 0, '昨日净值', cell_format=excel_formats['bold'])
    sheet.write_formula(line, 1, """=J{}""".format(line + 1), cell_format=excel_formats['bold_number3'])
    sheet.write_number(line, 9, last_net_value_obj.market_value, cell_format=excel_formats['bold_number3'])

    line += 1
    sheet.write_string(line, 0, '单位净值', cell_format=excel_formats['bold'])
    sheet.write_formula(line, 1, """=J{}""".format(line + 1), cell_format=excel_formats['bold_number3'])
    sheet.write_number(line, 9, round(net_value_obj.volume, 3), cell_format=excel_formats['bold_number3'])

    book.close()

    return '{}.xlsx'.format(file_name)
