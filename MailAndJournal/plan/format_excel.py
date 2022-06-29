import os
import xlrd
import xlwt
from xlutils.copy import copy
import xlwings as xw


# def Excle_borders_set(file_name):
#
#     work_book = xw.Book(file_name)  # 打开文件
#     for i in range(0, len(work_book.sheets)):
#         work_sheet = work_book.sheets[i]  # 选择表格
#         last_column = work_sheet.range(1, 1).end('right').get_address(0, 0)[0]  # 获取最后列
#         last_row = work_sheet.range(1, 1).end('down').row  # 获取最后行
#         sheet_range = f'A1:{last_column}{last_row}'  # 生成表格的数据范围
#         # 设置边框
#         work_sheet.range(sheet_range).api.Borders(8).LineStyle = 1  # 上边框
#         work_sheet.range(sheet_range).api.Borders(9).LineStyle = 1  # 下边框
#         work_sheet.range(sheet_range).api.Borders(7).LineStyle = 1  # 左边框
#         work_sheet.range(sheet_range).api.Borders(10).LineStyle = 1  # 右边框
#         work_sheet.range(sheet_range).api.Borders(12).LineStyle = 1  # 内横边框
#         work_sheet.range(sheet_range).api.Borders(11).LineStyle = 1  # 内纵边框
#     # 保存并关闭excel
#     work_book.save(file_name)
#     work_book.close()


def Excel_write(file_name, save_path, L=None):
    if L is None:
        L = []
    workbook = xlrd.open_workbook(file_name, formatting_info=True)
    new_book = copy(workbook)
    _borders = xlwt.Borders()
    _borders.left = 1
    _borders.right = 1
    _borders.top = 1
    _borders.bottom = 1
    style = xlwt.XFStyle()
    style.borders = _borders
    workbook_for_read = xlrd.open_workbook(file_name)
    for i in range(0, len(workbook.sheets())):
        sheet = workbook.sheet_by_index(i)
        sheet_for_read=workbook_for_read.sheet_by_index(i)
        new_sheet = new_book.get_sheet(i)
        rowNum = sheet.nrows
        colNum = sheet.ncols
        for j in range(0, rowNum):
            for k in range(0, colNum):
                new_sheet.write(j, k, sheet_for_read.cell(j, k).value, style)
        # 在末尾增加新行
        new_str1 = '投资经理：'
        new_str2 = '风控审核：'
        new_str3 = '交易员：'
        new_sheet.write(rowNum, 0, new_str1)
        new_sheet.write(rowNum, 3, new_str2)
        new_sheet.write(rowNum, 6, new_str3)
        # 覆盖保存
    new_book.save(save_path)


save_path = r'D:\Documents\实习生-金融工程\Desktop\打印2\副本\场外基金交易计划0720-0814.xlsx'
file_path = r'D:\Documents\实习生-金融工程\Desktop\打印2\源文件\场外基金交易计划0720-0814.xlsx'
Excel_write(file_path, save_path)
