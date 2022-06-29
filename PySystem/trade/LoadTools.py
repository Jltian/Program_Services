# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import pandas as pd
import re
import xlrd

from xlrd.biffh import XLRDError


def load_xlsx_like(file_path: str):
    """
    返回一个以流水文件首行为 key，数据行为 value 的字典列表, e.g. [{trade_time: xxxxx, }, {}, ]
    """
    return_list = list()            # 返回的数据列表
    content_list = list()           # 先把文件内容清理为以列表组成的列表
    try:
        file_content = xlrd.open_workbook(file_path, encoding_override='gb18030')
        file_content = pd.read_excel(file_path, )
        print(file_content)
        raise NotImplementedError
    except XLRDError:
        content_file = open(file_path, mode='r', ).read()
        for content_line in content_file.split('\n'):
            line_list = list()
            for content_cell in content_line.split('\t'):
                if re.match(r'=\"([^\"])\"', content_cell):
                    try:
                        line_list.append(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
                    except AttributeError as a_error:
                        print(content_cell, '\n', content_line)
                        raise a_error
                elif re.match(r'=\"([\w\W]*)\"', content_cell):
                    line_list.append(re.search(r'=\"([^\"]*)\"', content_cell).groups()[0])
                elif len(re.sub(r'[Ee\d.,:+]', '', content_cell.replace('-', ''))) == 0:  # 数字表达
                    line_list.append(content_cell)
                elif len(re.sub(r'\W', '', content_cell)) == 0:
                    line_list.append('-')
                elif len(re.sub(r'[\w()]', '', content_cell)) == 0:
                    line_list.append(content_cell)
                elif len(re.sub(r'[\w]', '', content_cell.replace(' ', ''))) == 0:
                    line_list.append(content_cell.replace(' ', ''))
                # elif re.match(r'([\w\W]*)', content_cell):
                #     line_list.append(content_cell)
                else:
                    raise NotImplementedError('{}\n{}'.format(content_cell, content_line))
            if len(re.sub('\W', '', '|'.join(line_list))) == 0:
                continue
            else:
                content_list.append(line_list)
    column_list = content_list[0]
    for i in range(1, len(content_list), 1):
        data_list = content_list[i]
        assert len(column_list) == len(data_list), 'Column: {}\nData: {}'.format(column_list, data_list)
        content_cell = dict(zip(column_list, data_list))
        try:
            content_cell.pop('')
        except KeyError:
            pass
        return_list.append(content_cell)
    return return_list


def load_csv(file_path: str):
    return_list = list()
    content_list = list()           # 先把文件内容清理为以列表组成的列表
    with open(file_path, mode='r', encoding='gb18030') as f:
        content_file = f.read()
    for content_line in content_file.split('\n'):
        content_line = content_line.replace(' ', '').replace('\u3000', '')
        line_list = content_line.split(',')
        if len(re.sub('\W', '', '|'.join(line_list))) == 0:
            continue
        else:
            content_list.append(line_list)
    column_list = content_list[0]
    for i in range(1, len(content_list), 1):
        data_list = content_list[i]
        assert len(column_list) == len(data_list), 'Column: {}\nData: {}'.format(column_list, data_list)
        content_cell = dict(zip(column_list, data_list))
        try:
            content_cell.pop('')
        except KeyError:
            pass
        return_list.append(content_cell)
    return return_list



if __name__ == '__main__':
    load_xlsx_like(r'Z:\当日交易流水\当日成交20200310\久铭1号股票中金证券.xls')
