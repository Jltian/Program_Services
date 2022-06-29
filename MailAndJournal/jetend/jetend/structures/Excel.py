# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import os
import xlwt
import xlsxwriter


class XlwtExcel(object):
    def __init__(self, encoding: str = 'utf-8', style_compression: int = 0):
        self.book = xlwt.Workbook(encoding=encoding, style_compression=style_compression)

        # ---- [set when using] ---- #
        self.column_list_dict = dict()
        self.sheet_dict = dict()
        self.sheet_working_line_dict = dict()

    @classmethod
    def create_book(cls, encoding: str = 'utf-8', style_compression: int = 0):
        return cls(encoding=encoding, style_compression=style_compression)

    def add_sheet(self, sheetname: str, cell_overwrite_ok: bool = True):
        sheet = self.book.add_sheet(sheetname=sheetname, cell_overwrite_ok=cell_overwrite_ok)
        self.sheet_dict[sheetname] = sheet
        self.sheet_working_line_dict[sheetname] = 0
        assert isinstance(sheet, xlwt.Worksheet)
        return sheet

    def __derive_sheet__(self, sheet):
        if isinstance(sheet, xlwt.Worksheet):
            sheet = sheet
        elif isinstance(sheet, str):
            sheet = self.sheet_dict[sheet]
        else:
            raise TypeError(type(sheet))
        assert isinstance(sheet, xlwt.Worksheet)
        return sheet

    def add_line_list(self, sheet, content_list: list, style=xlwt.Style.default_style):
        sheet = self.__derive_sheet__(sheet)
        for i in range(len(content_list)):
            sheet.write(self.sheet_working_line_dict[sheet.name], i, content_list[i], style=style)
        self.sheet_working_line_dict[sheet.name] = self.sheet_working_line_dict[sheet.name] + 1
        return sheet

    def add_obj_column(self, sheet, obj, style=xlwt.Style.default_style):
        from jetend.Interface import AbstractDataObject
        sheet = self.__derive_sheet__(sheet)
        if isinstance(obj, (list, tuple)):
            column_list = obj
        elif isinstance(obj, AbstractDataObject):
            column_list = [var for var in obj.inner2outer_map.values()]
        else:
            raise TypeError(type(obj))
        self.column_list_dict[sheet.name] = column_list
        return self.add_line_list(sheet, column_list, style=style)

    def add_obj_line(self, sheet, obj, style=xlwt.Style.default_style):
        from jetend.Interface import AbstractDataObject
        sheet = self.__derive_sheet__(sheet)
        if isinstance(obj, (list, tuple)):
            data_list = obj
        elif isinstance(obj, AbstractDataObject):
            column_list = self.column_list_dict[sheet.name]
            outer2inner = obj.outer2inner_map()
            data_list = [getattr(obj, outer2inner[var]) for var in column_list]
        else:
            raise TypeError(type(obj))
        return self.add_line_list(sheet, data_list, style=style)

    def write_line_list(self, sheet, line: int, content_list: list, style=xlwt.Style.default_style):
        sheet = self.__derive_sheet__(sheet)
        for i in range(len(content_list)):
            sheet.write(line, i, content_list[i], style=style)
        return sheet

    def save(self, path: str, folder_exist_ok: bool = True, ):
        path_folder = os.path.split(path)
        assert len(path_folder) > 1, 'Illegal path folder {}'.format(path)
        path_folder = os.path.sep.join(path_folder[:-1])
        os.makedirs(path_folder, exist_ok=folder_exist_ok)
        self.book.save(path)


class XlsxExcelWriter(object):
    def __init__(self, filename: str, options=None):
        self.book = xlsxwriter.Workbook(filename=filename, options=options)

        self.sheet_dict = dict()

    def add_sheet(self, sheetname: str):
        work_sheet = self.book.add_worksheet(name=sheetname)
        self.sheet_dict[sheetname] = work_sheet
        assert isinstance(work_sheet, xlsxwriter.workbook.Worksheet)
        return work_sheet

    def __derive_sheet__(self, sheet):
        if isinstance(sheet, xlwt.Worksheet):
            sheet = sheet
        elif isinstance(sheet, str):
            sheet = self.sheet_dict[sheet]
        else:
            raise TypeError(type(sheet))
        assert isinstance(sheet, xlwt.Worksheet)
        return sheet

    def save(self):
        self.book.close()
