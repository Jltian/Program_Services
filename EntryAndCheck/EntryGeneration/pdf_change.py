# https://www.jianshu.com/p/f33233e4c712
import pdfplumber  # 为了操作PDF
from openpyxl import Workbook
wb = Workbook()  # 创建文件对象
ws = wb.active  # 获取第一个sheet
path="D:/1.pdf"
pdf = pdfplumber.open(path)
print('\n')
print('开始读取数据')
print('\n')
print(pdf.pages[1].extract_tables()[0][0])
ws.append(pdf.pages[1].extract_tables()[0][0])
for page in pdf.pages:
    # 获取当前页面的全部文本信息，包括表格中的文字
    # print(page.extract_text())
    for table in page.extract_tables():
        # print(table)
        for row in table:
            if "序号" not in row:
                # print(type(row))
                rowlist=str(row).replace("[","",).replace("]","").replace("'","").replace("\\n","").split(",")
                print(rowlist)
                ws.append(rowlist)
        print('---------- 分割线 ----------')
pdf.close()
# 保存Excel表
wb.save('中国建筑集团2020届校园招聘需求名录.xlsx')
print('\n')
print('写入excel成功')
print('保存位置：')
print('中国建筑集团2020届校园招聘需求名录.xlsx')
print('\n')