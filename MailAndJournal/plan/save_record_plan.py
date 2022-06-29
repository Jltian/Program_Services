import xlrd
from xlutils.copy import copy
import xlwt

path_xls = r'D:\test\yimi\基金交易流水\场外基金交易计划318-322.xls'
title = '交易计划'

workbook = xlrd.open_workbook(path_xls, formatting_info=True)
style = xlwt.XFStyle()
al = xlwt.Alignment()
al.horz = 0x02
al.vert = 0x01
style.alignment = al
font = xlwt.Font()
font.name = '宋体'
font.height = 222
style.font = font
borders = xlwt.Borders()
borders.left = xlwt.Borders.THIN
borders.right = xlwt.Borders.THIN
borders.top = xlwt.Borders.THIN
borders.bottom = xlwt.Borders.THIN
borders.left_colour = 0x40
borders.right_colour = 0x40
borders.top_colour = 0x40
borders.bottom_colour = 0x40
style.borders = borders

style1 = xlwt.XFStyle()
font1 = xlwt.Font()
font1.name = '宋体'
font1.height = 222
style1.font = font1

for i in range(len(workbook.sheet_names())):
    sheet = workbook.sheet_by_index(i)
    rowNum = sheet.nrows
    colNum = sheet.ncols
    newbook = copy(workbook)
    newsheet = newbook.get_sheet(i)
    for j in range(9):
        newsheet.col(j).width = 3100
    str1='投资经理：'
    str2='风控审核：'
    str3='交易员：'
    newsheet.write(rowNum, 0, str1, style1)
    newsheet.write(rowNum, 3, str2, style1)
    newsheet.write(rowNum, 6, str3, style1)
    newsheet.write_merge(0,0,0,8,str(workbook.sheet_names()[i])+title, style)
    newbook.save(path_xls)
    workbook = xlrd.open_workbook(path_xls, formatting_info=True)