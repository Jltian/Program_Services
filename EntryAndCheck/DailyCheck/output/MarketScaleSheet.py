# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime

from jetend.structures import List
from jetend.jmSheets import *

from modules.AccountPosition import AccountPosition


def output_market_scale_sheet(self, date: datetime.date, output_folder: str):
    from os import path, makedirs
    from xlsxwriter import Workbook
    from jetend.Constants import DataBaseName

    acc_pos_list = List.from_pd(AccountPosition, self.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM 产品余额持仓表 WHERE 日期 = '{}';""".format(date)
    ))
    last_net_value_list = List.from_pd(AccountPosition, self.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM 产品余额持仓表 WHERE 日期 = '{}' AND 科目名称 = '单位净值'
        ;""".format(date - datetime.timedelta(days=1))
    ))
    product_id_list = [self.find_product_code_by_name(var) for var in acc_pos_list.collect_attr_set('product')]
    product_id_list.sort()

    makedirs(output_folder, exist_ok=True)
    output_path = path.join(output_folder, '{} 产品规模明细表.xlsx'.format(date))

    book = Workbook(filename=output_path)
    excel_formats = {
        'bold': book.add_format({'bold': True, }), 'center': book.add_format({'align': 'center'}),
        'date': book.add_format({'num_format': 'yyyy-mm-dd'}),
        'number2': book.add_format({'num_format': '#,##0.00'}),
        'number3': book.add_format({'num_format': '#,##0.000'}),
        'number4': book.add_format({'num_format': '#,##0.0000'}),
        'number8': book.add_format({'num_format': '#,##0.00000000'}),
        'percentage': book.add_format({'num_format': '0.00%'}),
        'bold_number2': book.add_format({'num_format': '#,##0.00', 'bold': True, }, ),
        'bold_number3': book.add_format({'num_format': '#,##0.000', 'bold': True, }, ),
        'bold_number4': book.add_format({'num_format': '#,##0.0000', 'bold': True, }, ),
    }

    # ----------------------- [持仓余额明细] -----------------------
    sheet = book.add_worksheet(name='持仓余额明细')
    sheet.set_column(0, 0, width=11, )
    sheet.set_column(1, 1, width=10, )
    sheet.set_column(2, 2, width=12.4, )
    sheet.set_column(3, 3, width=17, )
    sheet.set_column(4, 4, width=10, )
    sheet.set_column(5, 5, width=14, )
    sheet.set_column(8, 8, width=16, )
    sheet.set_column(11, 11, width=16, )

    line = 0
    column_map = {
        '日期': 0, '产品': 1, '券商': 2, '证券名称': 3, '证券代码': 4, '持仓数量': 5, '市场': 6, '实时价': 7,
        '实时市值': 8, '收盘汇率': 9, '收盘价': 10, '收盘市值': 11, '是否记入券商托管规模': 12,
    }
    for tag in column_map.keys():
        sheet.write_string(line, column_map[tag], tag, cell_format=excel_formats['bold'])

    for product in acc_pos_list.collect_attr_set('product'):
        product_pos_list = acc_pos_list.find_value_where(
            product=product, account_name=('股票', '可转债', '债券', '货基', '期货', '申购股票'),
        )
        for obj in product_pos_list:
            assert isinstance(obj, AccountPosition)
            line += 1
            sheet.write_datetime(line, column_map['日期'], date, cell_format=excel_formats['date'])
            sheet.write_string(line, column_map['产品'], obj.product, )
            sheet.write_string(line, column_map['券商'], obj.institution, )
            sheet.write_string(line, column_map['证券名称'], obj.security_name)
            sheet.write_string(line, column_map['证券代码'], obj.security_code)
            sheet.write_number(line, column_map['持仓数量'], obj.volume, cell_format=excel_formats['number2'])
            if obj.exchange_market in ('SH', 'SZ'):
                sheet.write_string(line, column_map['市场'], 'A股')
            elif obj.exchange_market in ('HK', ) and '收益互换' not in obj.institution:
                sheet.write_string(line, column_map['市场'], '港股通')
            elif obj.institution == '港股收益互换':
                sheet.write_string(line, column_map['市场'], 'HKSWAP')
            elif obj.institution == '美股收益互换':
                sheet.write_string(line, column_map['市场'], 'USSWAP')
            else:
                sheet.write_string(line, column_map['市场'], obj.account_name)
            sheet.write_formula(line, column_map['实时价'], """
            =IF(RTD("wdf.rtq",,E{line},"LastPrice")=0,s_ipo_price(E{line}),RTD("wdf.rtq",,E{line},"LastPrice"))
            """.format(line=line + 1), cell_format=excel_formats['number2'])
            sheet.write_formula(line, column_map['实时市值'], """
            =F{line}*J{line}*H{line}""".format(line=line + 1), cell_format=excel_formats['number2'])
            sheet.write_number(line, column_map['收盘汇率'], obj.exchange_rate, cell_format=excel_formats['number4'])
            sheet.write_formula(line, column_map['收盘价'], """
            =IF(s_dq_close(E{line},A{line},1)=0,s_ipo_price(E{line}),s_dq_close(E{line},A{line},1))
            """.format(line=line + 1), cell_format=excel_formats['number2'])
            sheet.write_formula(line, column_map['收盘市值'], """
            =F{line}*J{line}*K{line}""".format(line=line + 1), cell_format=excel_formats['number2'])

    # ----------------------- [账户余额明细] -----------------------
    sheet = book.add_worksheet(name='账户余额明细')
    sheet.set_column(0, 0, width=11, )
    sheet.set_column(3, 3, width=13, )
    sheet.set_column(4, 4, width=15, )

    line = 0
    column_map = {
        '日期': 0, '产品': 1, '账户类型': 2, '账户': 3, '余额': 4, '币种': 5,
    }
    for tag in column_map.keys():
        sheet.write_string(line, column_map[tag], tag, cell_format=excel_formats['bold'])

    for product in acc_pos_list.collect_attr_set('product'):
        product_pos_list = acc_pos_list.find_value_where(
            product=product, account_name=('银行存款', '证券账户', '信用账户', '期货账户', '期权账户'),
        )
        for obj in product_pos_list:
            assert isinstance(obj, AccountPosition)
            line += 1
            sheet.write_datetime(line, column_map['日期'], date, cell_format=excel_formats['date'])
            sheet.write_string(line, column_map['产品'], obj.product, )
            sheet.write_string(line, column_map['账户类型'], obj.account_name, )
            sheet.write_string(line, column_map['账户'], obj.institution)
            sheet.write_number(line, column_map['余额'], obj.volume, cell_format=excel_formats['number2'])
            sheet.write_string(line, column_map['币种'], obj.currency_origin)

    # ----------------------- [产品估值明细] -----------------------
    for product_id in product_id_list:
        product = self.find_product_info_by_code(product_id).name
        p_acc_pos = acc_pos_list.find_value_where(product=product)

        summary_line_dict = dict()

        sheet = book.add_worksheet(name=product)

        sheet.set_column(0, 0, width=12, )
        sheet.set_column(1, 1, width=17, )
        sheet.set_column(2, 2, width=10, )
        sheet.set_column(3, 3, width=14, )
        sheet.set_column(4, 4, width=18, )
        sheet.set_column(5, 5, width=18, )
        sheet.set_column(6, 6, width=18, )
        sheet.set_column(7, 7, width=7, )
        sheet.set_column(8, 8, width=8, )
        sheet.set_column(9, 9, width=9, )
        sheet.set_column(10, 10, width=9.25, )
        sheet.set_column(11, 11, width=18, )

        total_asset_line, total_liability_line, total_pos_line = set(), set(), set()
        total_pos_cell = '$M$1'

        line = 0
        sheet.merge_range(line, 1, line, 11, '{} {}'.format(product_id, product),
                          cell_format=book.add_format({'align': 'center', 'bold': True, }))
        sheet.write_datetime(line, 0, date, cell_format=excel_formats['date'])

        line += 1
        column_list = [
            '资产类别', '类别', '品种代码', '持仓品种', '持仓数量（万股）', '收盘价', '收盘市值（亿元）', '涨跌幅', '仓位占比',
            '实时市价', '实时涨跌', '实时市值（亿元）',
        ]
        for i in range(len(column_list)):
            sheet.write_string(line, i, column_list[i], cell_format=excel_formats['bold'])

        # 普通账户持仓
        sub_acc_pos = p_acc_pos.find_value_where(account_name='证券账户')
        sub_acc_pos.extend(p_acc_pos.find_value_where(account_name='信用账户'))
        institution_set = sub_acc_pos.collect_attr_set('institution')
        sub_class_iter_line = 0
        for institution in institution_set:
            if '收益互换' in institution:
                continue
            institution_iter_line = 0
            sub_acc_pos = p_acc_pos.find_value_where(institution=institution)
            for obj in sub_acc_pos:
                if obj.account_name in (
                        '证券账户', '应收利息', '应付利息', '应付融资费用', '信用账户', '短期借款', '应付融资利息'):
                    continue
                line += 1
                total_pos_line.add(line + 1)
                total_asset_line.add(line + 1)
                if sub_class_iter_line == 0:
                    sheet.write_string(line, 0, '多头持仓', cell_format=excel_formats['bold'])
                sub_class_iter_line += 1
                if institution_iter_line == 0:
                    sheet.write_string(line, 1, obj.institution, )
                institution_iter_line += 1
                sheet.write_string(line, 2, obj.security_code, )
                sheet.write_string(line, 3, obj.security_name, )
                sheet.write_number(line, 4, obj.volume / 10000.0, cell_format=excel_formats['number4'])
                sheet.write_formula(line, 5, "=s_dq_close(C{},$A$1,1)".format(line + 1, date),
                                    cell_format=excel_formats['number2'])
                if obj.security_code.split('.')[-1].upper() == 'HK':
                    sheet.write_formula(line, 6, '=E{}*F{}*汇率!$D$2/10000'.format(line + 1, line + 1),
                                        cell_format=excel_formats['number4'])
                else:
                    sheet.write_formula(line, 6, '=E{}*F{}/10000'.format(line + 1, line + 1),
                                        cell_format=excel_formats['number4'])
                sheet.write_formula(line, 7, "=s_dq_pctchange(C{},$A$1)/100*I{}".format(line + 1, line + 1),
                                    cell_format=excel_formats['percentage'])
                sheet.write_formula(line, 8, "=G{}/{}".format(line + 1, total_pos_cell),
                                    cell_format=excel_formats['percentage'])
                sheet.write_formula(line, 9, """=RTD("wdf.rtq",,C{},"LastPrice")""".format(line + 1),
                                    cell_format=excel_formats['number2'])
                sheet.write_formula(line, 10, "=(J{line}/F{line}-1)*I{line}".format(line=line + 1),
                                    cell_format=excel_formats['percentage'])
                if obj.security_code.split('.')[-1].upper() == 'HK':
                    sheet.write_formula(line, 11, "=E{line}*J{line}*汇率!$D$2/10000".format(line=line + 1),
                                        cell_format=excel_formats['number4'])
                else:
                    sheet.write_formula(line, 11, "=E{line}*J{line}/10000".format(line=line + 1),
                                        cell_format=excel_formats['number4'])

        for institution in institution_set:
            institution_iter_line = 0
            if '收益互换' not in institution:
                continue
            sub_acc_pos = p_acc_pos.find_value_where(institution=institution)
            for obj in sub_acc_pos:
                if obj.account_name in ('证券账户', '应收利息', '应付利息'):
                    continue
                if abs(obj.volume) < 0.01:
                    continue
                line += 1
                total_pos_line.add(line + 1)
                total_asset_line.add(line + 1)
                if sub_class_iter_line == 0:
                    sheet.write_string(line, 0, '多头持仓', cell_format=excel_formats['bold'])
                sub_class_iter_line += 1
                if institution_iter_line == 0:
                    sheet.write_string(line, 1, obj.institution, )
                institution_iter_line += 1
                sheet.write_string(line, 2, obj.security_code, )
                sheet.write_string(line, 3, obj.security_name, )
                sheet.write_number(line, 4, obj.volume / 10000.0, cell_format=excel_formats['number4'])
                sheet.write_formula(line, 5, "=s_dq_close(C{},$A$1,1)".format(line + 1, date),
                                    cell_format=excel_formats['number2'])
                if institution == '港股收益互换':
                    sheet.write_formula(line, 6, '=E{}*F{}*汇率!$D$3/10000'.format(line + 1, line + 1),
                                        cell_format=excel_formats['number4'])
                elif institution == '美股收益互换':
                    sheet.write_formula(line, 6, '=E{}*F{}*汇率!$D$4/10000'.format(line + 1, line + 1),
                                        cell_format=excel_formats['number4'])
                else:
                    raise NotImplementedError(institution)
                sheet.write_formula(line, 7, "=s_dq_pctchange(C{},$A$1)/100*I{}".format(line + 1, line + 1),
                                    cell_format=excel_formats['percentage'])
                sheet.write_formula(line, 8, "=G{}/{}".format(line + 1, total_pos_cell),
                                    cell_format=excel_formats['percentage'])
                sheet.write_formula(line, 9, """=RTD("wdf.rtq",,C{},"LastPrice")""".format(line + 1),
                                    cell_format=excel_formats['number2'])
                sheet.write_formula(line, 10, "=(J{line}/F{line}-1)*I{line}".format(line=line + 1),
                                    cell_format=excel_formats['percentage'])
                if institution == '港股收益互换':
                    sheet.write_formula(line, 11, "=E{line}*J{line}*汇率!$D$3/10000".format(line=line + 1),
                                        cell_format=excel_formats['number4'])
                elif institution == '美股收益互换':
                    sheet.write_formula(line, 11, "=E{line}*J{line}*汇率!$D$4/10000".format(line=line + 1),
                                        cell_format=excel_formats['number4'])
                else:
                    raise NotImplementedError(institution)

        # TODO：期货账户持仓
        # sub_acc_pos = p_acc_pos.find_value_where(account_name='期货账户')
        # institution_set = sub_acc_pos.collect_attr_set('institution')

        # TODO：期权账户持仓

        # 基金投资
        sub_acc_pos = p_acc_pos.find_value_where(account_name='公募基金')
        if len(sub_acc_pos) > 0:
            raise NotImplementedError(sub_acc_pos)

        # 自有产品
        sub_acc_pos = p_acc_pos.find_value_where(account_name='自有产品')
        summary_line_dict['自有产品'] = list()
        institution_iter_line = 0
        for obj in sub_acc_pos:
            if abs(obj.volume) < 0.01:
                continue
            line += 1
            total_pos_line.add(line + 1)
            total_asset_line.add(line + 1)
            summary_line_dict['自有产品'].append(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '多头持仓', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            if institution_iter_line == 0:
                sheet.write_string(line, 1, '所持产品', )
            institution_iter_line += 1
            sheet.write_string(line, 2, obj.security_code, )
            sheet.write_string(line, 3, obj.security_name, )
            sheet.write_number(line, 4, obj.volume / 10000.0, cell_format=excel_formats['number4'])
            sheet.write_number(line, 5, obj.market_price_origin, cell_format=excel_formats['number3'])
            sheet.write_formula(line, 6, '=E{}*F{}/10000'.format(line + 1, line + 1),
                                cell_format=excel_formats['number4'])
            sheet.write_formula(line, 8, "=G{}/{}".format(line + 1, total_pos_cell),
                                cell_format=excel_formats['percentage'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        # 账户余额
        sub_class_iter_line = 0
        sub_acc_pos = p_acc_pos.find_value_where(account_name='银行存款')
        for obj in sub_acc_pos:
            if abs(obj.volume) < 0.01:
                continue
            line += 1
            total_asset_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '现金及余额', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '银行存款({})'.format(obj.institution), )
            sheet.write_number(line, 5, obj.volume, cell_format=excel_formats['number2'])
            sheet.write_number(line, 6, obj.market_value / 100000000.0, cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = p_acc_pos.find_value_where(account_name='证券账户')
        sub_acc_pos.extend(p_acc_pos.find_value_where(account_name='信用账户'))
        sub_acc_pos.extend(p_acc_pos.find_value_where(account_name='期货账户'))
        sub_acc_pos.extend(p_acc_pos.find_value_where(account_name='期权账户'))
        for obj in sub_acc_pos:
            if abs(obj.volume) < 0.01:
                continue
            line += 1
            total_asset_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '现金及余额', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '账户余额({})'.format(obj.institution), )
            sheet.write_number(line, 5, obj.volume, cell_format=excel_formats['number2'])
            sheet.write_number(line, 6, obj.market_value / 100000000.0, cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        # 应收项目
        sub_class_iter_line = 0
        sub_acc_pos = p_acc_pos.find_value_where(account_name='应收利息')
        if len(sub_acc_pos) > 0:
            line += 1
            total_asset_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '应收项目', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '应收利息', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = p_acc_pos.find_value_where(account_name='应收股利')
        if len(sub_acc_pos) > 0:
            line += 1
            total_asset_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '应收项目', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '应收分红', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = p_acc_pos.find_value_where(account_name='累计应收管理费返还')
        sub_acc_pos.extend(p_acc_pos.find_value_where(account_name='已收应收管理费返还'))
        if len(sub_acc_pos) > 0:
            line += 1
            total_asset_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '应收项目', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '应收管理费返还', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        # 应付项目
        sub_class_iter_line = 0
        sub_acc_pos = p_acc_pos.find_value_where(account_name='累计应付管理费')
        sub_acc_pos.extend(p_acc_pos.find_value_where(account_name='已付应付管理费'))
        if len(sub_acc_pos) > 0:
            line += 1
            total_liability_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '负债', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '应付管理费', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = p_acc_pos.find_value_where(account_name='累计应付业绩报酬')
        sub_acc_pos.extend(p_acc_pos.find_value_where(account_name='累计已付业绩报酬'))
        if len(sub_acc_pos) > 0:
            line += 1
            total_liability_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '负债', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '应付业绩报酬', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = p_acc_pos.find_value_where(account_name='应付利息', institution='美股收益互换')
        if len(sub_acc_pos) > 0:
            line += 1
            total_liability_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '负债', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '美股应付利息', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = p_acc_pos.find_value_where(account_name='应付利息', institution='港股收益互换')
        if len(sub_acc_pos) > 0:
            line += 1
            total_liability_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '负债', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '港股应付利息', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = p_acc_pos.find_value_where(account_name='短期借款', )
        if len(sub_acc_pos) > 0:
            line += 1
            total_liability_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '负债', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '融资负债', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = List()
        for obj in p_acc_pos.find_value_where(account_name='应付利息', ):
            if '收益互换' in obj.institution:
                continue
            sub_acc_pos.append(obj)
        if len(sub_acc_pos) > 0:
            line += 1
            total_liability_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '负债', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '融资利息', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = p_acc_pos.find_value_where(account_name='应付申购款', )
        if len(sub_acc_pos) > 0:
            line += 1
            total_liability_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '负债', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '应付申购款', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        sub_acc_pos = p_acc_pos.find_value_where(account_name='其他应付款', )
        if len(sub_acc_pos) > 0:
            line += 1
            total_liability_line.add(line + 1)
            if sub_class_iter_line == 0:
                sheet.write_string(line, 0, '负债', cell_format=excel_formats['bold'])
            sub_class_iter_line += 1
            sheet.write_string(line, 1, '其他应付款', )
            sheet.write_number(line, 6, sub_acc_pos.sum_attr('market_value') / 100000000.0,
                               cell_format=excel_formats['number4'])
            sheet.write_formula(line, 11, "=G{}".format(line + 1), cell_format=excel_formats['number4'])

        line += 2
        sheet.write_string(line, 0, '总资产', cell_format=excel_formats['bold'])
        formula_str = '={}'.format('+'.join(['G{}'.format(var) for var in total_asset_line]))
        sheet.write_formula(line, 6, formula_str, cell_format=excel_formats['bold_number4'])
        formula_str = '={}'.format('+'.join(['L{}'.format(var) for var in total_asset_line]))
        sheet.write_formula(line, 11, formula_str, cell_format=excel_formats['bold_number4'])

        line += 1
        sheet.write_string(line, 0, '总负债', cell_format=excel_formats['bold'])
        formula_str = '={}'.format('+'.join(['G{}'.format(var) for var in total_liability_line]))
        sheet.write_formula(line, 6, formula_str, cell_format=excel_formats['bold_number4'])
        formula_str = '={}'.format('+'.join(['L{}'.format(var) for var in total_liability_line]))
        sheet.write_formula(line, 11, formula_str, cell_format=excel_formats['bold_number4'])

        line += 1
        sheet.write_string(line, 0, '多头汇总', cell_format=excel_formats['bold'])
        formula_str = '={}'.format('+'.join(['G{}'.format(var) for var in total_pos_line]))
        sheet.write_formula(line, 6, formula_str, cell_format=excel_formats['bold_number4'])
        sheet.write_formula(0, 12, """=G{}""".format(line + 1))
        formula_str = '={}'.format('+'.join(['L{}'.format(var) for var in total_pos_line]))
        sheet.write_formula(line, 11, formula_str, cell_format=excel_formats['bold_number4'])

        obj = p_acc_pos.find_value(account_name='资产净值')
        line += 1
        sheet.write_string(line, 0, '净资产', cell_format=excel_formats['bold'])
        sheet.write_number(line, 5, obj.volume, cell_format=excel_formats['bold_number2'])
        sheet.write_number(line, 6, obj.volume / 100000000, cell_format=excel_formats['bold_number4'])
        sheet.write_formula(line, 11, """=L{}+L{}""".format(line - 2, line - 1),
                           cell_format=excel_formats['bold_number4'])

        obj = p_acc_pos.find_value(account_name='实收基金')
        line += 1
        sheet.write_string(line, 0, '份额', cell_format=excel_formats['bold'])
        sheet.write_number(line, 5, obj.volume, cell_format=excel_formats['bold_number2'])
        sheet.write_number(line, 6, obj.volume / 100000000, cell_format=excel_formats['bold_number4'])

        obj = p_acc_pos.find_value(account_name='单位净值')
        line += 1
        sheet.write_string(line, 0, '单位净值', cell_format=excel_formats['bold'])
        sheet.write_number(line, 5, obj.volume, cell_format=excel_formats['bold_number3'])
        sheet.write_formula(line, 7, """==(F{}-F{})/F{}""".format(line + 2, line + 1, line + 1),
                            cell_format=excel_formats['percentage'])
        sheet.write_formula(line, 9, """=L{}/G{}""".format(line - 1, line), cell_format=excel_formats['bold_number3'])
        sheet.write_formula(line, 10, """==(J{line}-F{line})/F{line}""".format(line=line + 1),
                            cell_format=excel_formats['percentage'])

        obj = last_net_value_list.find_value(product=product)
        line += 1
        sheet.write_string(line, 0, '前日净值', cell_format=excel_formats['bold'])
        sheet.write_number(line, 5, obj.volume, cell_format=excel_formats['bold_number3'])

        line +=2
        sheet.write_string(line, 0, '相关统计', cell_format=excel_formats['bold'])

        sheet.write_string(line, 1, '自有产品市值')
        formula_str = '={}'.format('+'.join(['G{}'.format(var) for var in summary_line_dict['自有产品']]))
        sheet.write_formula(line, 6, formula_str, cell_format=excel_formats['number4'])

        # sub_acc_list = acc_list.find_value_where(account_name='银行存款')
        # if len(sub_acc_list) > 0:
        #     line += 1
        #     account_code = 1002
        #     total_asset_line.add(line + 1)
        #     sheet.write_string(line, 0, str(account_code), cell_format=excel_formats['bold'])
        #     sheet.write_string(line, 1, '银行存款', cell_format=excel_formats['bold'])
        #     sheet.write_string(line, 2, '***', cell_format=excel_formats['bold'])
        #     # sheet.write_number(line, 3, 1, cell_format=excel_formats['bold'])
        #     sheet.write_formula(line, 6, '=SUM(G{}:G{})'.format(line + 2, line + 1 + len(sub_acc_list)),
        #                         cell_format=excel_formats['bold_number2'])
        #     sheet.write_formula(line, 9, '=SUM(J{}:J{})'.format(line + 2, line + 1 + len(sub_acc_list)),
        #                         cell_format=excel_formats['bold_number2'])
        #     sub_level = 0
        #     for obj in sub_acc_list:
        #         line += 1
        #         sub_level += 1
        #         sheet.write_string(line, 0, '{0}.{1:02d}'.format(account_code, sub_level), )
        #         sheet.write_string(line, 1, '银行存款_活期存款账户_{}'.format(obj.sub_account), )
        #         sheet.write_string(line, 2, 'CNY', )
        #         sheet.write_number(line, 3, 1)
        #         sheet.write_number(line, 6, obj.net_value, cell_format=excel_formats['number2'])
        #         sheet.write_number(line, 9, obj.net_value, cell_format=excel_formats['number2'])

    # ------- [汇率表] -------
    sheet = book.add_worksheet(name='汇率')
    sheet.set_column(0, 4, width=12)
    column_list = ['日期', '币种', '来源', '汇率', ]
    for i in range(len(column_list)):  # 写入列名
        sheet.write_string(0, i, column_list[i])
    exchange_rate = 0.0
    for obj in acc_pos_list.find_value_where(account_name='股票'):
        if abs(exchange_rate) >= 0.01:
            continue
        if obj.security_code.split('.')[-1].upper() == 'HK' and '收益互换' not in obj.institution:
            exchange_rate = obj.exchange_rate
    data_list = [
        ('港币-人民币', '港股通', exchange_rate),
        ('港币-人民币', '港股收益互换', self.find_exchange_rate(date, 'HKDCNYSET.SWAP').value),
        ('美元-人民币', '美股收益互换', self.find_exchange_rate(date, 'USDCNYSET.SWAP').value),
    ]
    for i in range(len(data_list)):
        sheet.write_datetime(i + 1, 0, date, cell_format=excel_formats['date'])
        sheet.write_string(i + 1, 1, data_list[i][0])
        sheet.write_string(i + 1, 2, data_list[i][1])
        cell = data_list[i][2]
        if isinstance(cell, float):
            sheet.write_number(i + 1, 3, cell, cell_format=excel_formats['number8'])
        elif isinstance(cell, str):
            sheet.write_formula(i + 1, 3, cell, cell_format=excel_formats['number8'])
        else:
            raise TypeError(data_list[i])

    book.close()
