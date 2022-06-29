# -*- encoding: UTF-8 -*-
import os
import datetime

import pandas as pd

from jetend.DataCheck import *


class jmValuationBoard(object):
    """把何梦洁的估值表格作为数据源"""
    file_product_map = {
        '久铭2号估值表.xlsx': '久铭2号', '久铭3号估值表.xlsx': '久铭3号',
        '久铭全球1号估值表.xlsx': '全球1号', '久铭收益1号估值表.xlsx': '收益1号',
        '久铭双盈1号估值表.xlsx': '双盈1号', '久铭稳利2号估值表.xlsx': '稳利2号',
        '稳健2号估值表.xlsx': '稳健2号', '稳健3号估值表.xlsx': '稳健3号', '稳健5号估值表.xlsx': '稳健5号',
        '稳健6号估值表.xlsx': '稳健6号', '稳健7号估值表.xlsx': '稳健7号', '稳健8号估值表.xlsx': '稳健8号',
        '稳健9号估值表.xlsx': '稳健9号', '稳健10号估值表.xlsx': '稳健10号', '稳健11号估值表.xlsx': '稳健11号',
        '稳健12号估值表.xlsx': '稳健12号', '稳健15号估值表.xlsx': '稳健15号', '稳健16号估值表.xlsx': '稳健16号',
        '稳健17号估值表.xlsx': '稳健17号', '稳健18号估值表.xlsx': '稳健18号', '稳健19号估值表.xlsx': '稳健19号',
        '稳健21号估值表.xlsx': '稳健21号', '稳健22号估值表.xlsx': '稳健22号', '稳健31号估值表.xlsx': '稳健31号',
        '稳健32号估值表.xlsx': '稳健32号', '稳健33号估值表.xlsx': '稳健33号',
    }

    def __init__(self, path: str, info_board):
        from jetend.modules.jmInfoBoard import jmInfoBoard
        from jetend.structures import get_logger
        assert isinstance(info_board, jmInfoBoard)
        self.log = get_logger(self.__class__.__name__)
        self.__path__ = path
        self.data = dict()
        self.info_board = info_board

    @property
    def product_file_map(self):
        product_file_map = self.data.get('product_file_map', None)
        if product_file_map is None:
            new_d = dict()
            for file, product in self.file_product_map.items():
                new_d[product] = file
            product_file_map = new_d
            self.data['product_file_map'] = product_file_map
        return product_file_map

    def __sub_path__(self, *args):
        return os.path.join(self.__path__, *args)

    def __load_product__(self, product: str, date: datetime.date):
        if product in self.data:
            pd_data = self.data[product]
        else:
            self.log.debug_running('opening', self.product_file_map[product])
            pd_data = pd.read_excel(self.__sub_path__(self.product_file_map[product]), sheet_name='资产负债表', )
            pd_data = pd_data[pd_data['日期'] <= pd.Timestamp(date + datetime.timedelta(days=1))]
            pd_data = pd_data[pd_data['日期'] >= pd.Timestamp(date - datetime.timedelta(days=10))]
            self.data[product] = pd_data
        assert isinstance(pd_data, pd.DataFrame)
        return pd_data

    def __derive_pd_content__(self, pd_data: pd.DataFrame, date: datetime.date, tag: str, shift: int = 0):
        column_list = list(pd_data.columns)
        pd_data_line = pd_data[pd_data['日期'] == pd.Timestamp(date)]
        if len(pd_data_line.index) == 1:
            pd_data_line = pd_data_line.iloc[0, ]
        elif len(pd_data_line.index) == 2:
            pd_data_line = pd_data_line.iloc[0, ]
        elif len(pd_data_line.index) == 0:
            pd_data_line = pd_data[pd_data['日期'] == pd.Timestamp(date - datetime.timedelta(days=1))]
            if len(pd_data_line.index) == 2:
                pd_data_line = pd_data_line.iloc[1, ]
            else:
                raise NotImplementedError(str(pd_data_line.head()))
        else:
            raise NotImplementedError(str(pd_data_line.head()))
        try:
            return float(pd_data_line[column_list.index(tag) + shift])
        except ValueError as col_not_find:
            # self.log.debug(str(pd_data.columns))
            raise col_not_find

    def __search_pd_column__(self, pd_data: pd.DataFrame, key: str):
        assert len(key) > 0
        for col in pd_data.columns:
            if key in col:
                return col
        raise KeyError

    def hist_product_net_value_per_share(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product, date=date)
        return self.__derive_pd_content__(pd_data, date, '今日单位净值', shift=0)

    def hist_product_net_value(self, product: str, date: datetime.datetime):
        pd_data = self.__load_product__(product, date=date)
        return self.__derive_pd_content__(pd_data, date, '申赎前资产类合计', shift=0)

    def hist_product_net_shares(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product, date=date)
        try:
            return self.__derive_pd_content__(pd_data, date, '基金现份额', shift=0)
        except ValueError:
            return self.__derive_pd_content__(pd_data, date, '基金份额', shift=0)

    def hist_product_accumulated_management_fee_payable(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product, date=date)
        try:
            if product in ('全球1号', '收益1号', ):
                accumulated_fee_tag = '累计固定管理费'
            elif product in ('稳健18号',):
                accumulated_fee_tag = '累计管理费用'
            else:
                accumulated_fee_tag = '累计应付管理费'
            return self.__derive_pd_content__(pd_data, date, accumulated_fee_tag, shift=0)
        except ValueError as amf:
            if self.info_board.find_product_management_fee_rate(product, date) >= 0.000001:
                raise amf
            else:
                return 0

    def hist_product_management_fee_payable(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product, date=date)
        try:
            if product in ('全球1号',):
                fee_payable_tag = '应付固定管理费'
            elif product in ('收益1号',):
                fee_payable_tag = '固定管理费'
            elif product in ('稳健18号',):
                fee_payable_tag = '应付管理费'
            else:
                fee_payable_tag = '应付管理费'
            return self.__derive_pd_content__(pd_data, date, fee_payable_tag, shift=0)
        except ValueError as amf:
            if self.info_board.find_product_management_fee_rate(product, date) >= 0.000001:
                raise amf
            else:
                return 0

    def hist_product_daily_management_fee_payable(self, product: str, date: datetime.date):
        return self.hist_product_accumulated_management_fee_payable(
            product=product, date=date,
        ) - self.hist_product_accumulated_management_fee_payable(
            product=product, date=date - datetime.timedelta(days=1))

    def hist_product_daily_management_profit_payable(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product, date=date)
        paid_tag, for_pay_tag = '已付业绩报酬', '业绩报酬'
        last_for_pay = self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), for_pay_tag)
        for_pay = self.__derive_pd_content__(pd_data, date, for_pay_tag)
        if not is_valid_float(for_pay):
            return 0
        elif is_valid_float(last_for_pay):
            return self.__derive_pd_content__(pd_data, date, paid_tag) + for_pay \
                   - self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), paid_tag) \
                   - last_for_pay
        else:
            return self.__derive_pd_content__(pd_data, date, for_pay_tag)

    def hist_product_management_fee_receivable(self, product: str, fund_name: str, date: datetime.date):
        pd_data = self.__load_product__(product, date=date)

        def find_tag(pd_d: pd.DataFrame, fund_n: str):
            for col in pd_d.columns:
                if '应收' in col and '管理费' in col and fund_n.replace('指数', '') in col and '累计' not in col:
                    return col
            for col in pd_d.columns:
                if '返还' in col and '管理费' in col and fund_n.replace('指数', '') in col and '累计' not in col:
                    return col
            return None
        try:
            tag = find_tag(pd_data, fund_name)
            if tag is None:
                if (product, fund_name) in [
                    ('稳健6号', '中证500指数'), ('稳健6号', '沪深300指数'),
                ]:
                    return self.__derive_pd_content__(pd_data, date, '已收{}管理费'.format(fund_name), shift=1)
                elif (product, fund_name) in [('稳健12号', '稳健7号'), ]:
                    return self.__derive_pd_content__(pd_data, date, '应收{}'.format(fund_name))
                else:
                    raise ValueError(fund_name)
            else:
                return self.__derive_pd_content__(pd_data, date, tag, shift=0)
        except ValueError as rmf:
            if self.info_board.find_product_management_fee_rate(fund_name, date) >= 0.000001:
                raise rmf
            else:
                return 0

    def hist_product_accumulated_management_fee_receivable(self, product: str, fund_name: str, date: datetime.date):
        pd_data = self.__load_product__(product, date=date)

        def find_tag(pd_d: pd.DataFrame, fund_n: str):
            for col in pd_d.columns:
                if '累计应收' in col and '管理费' in col and fund_n.replace('指数', '') in col:
                    return col
            return None
        try:
            tag = find_tag(pd_data, fund_name)
            if tag is None:
                if (product, fund_name) in [
                    ('稳健6号', '中证500指数'), ('稳健6号', '沪深300指数'),
                ]:
                    return self.__derive_pd_content__(pd_data, date, '已收{}管理费'.format(fund_name), shift=-1)
                elif (product, fund_name) in [('稳健12号', '稳健7号'), ]:
                    raise NotImplementedError
                elif (product, fund_name) in [
                    ('稳健3号', '稳健7号'), ('稳健5号', '稳健7号'), ('稳利2号', '稳健1号'), ('收益1号', '久铭2号'),
                ]:
                    return 0
                else:
                    raise ValueError('{} {}'.format(product, fund_name))
            else:
                return self.__derive_pd_content__(pd_data, date, tag, shift=0)
        except ValueError as rmf:
            if self.info_board.find_product_management_fee_rate(fund_name, date) >= 0.000001:
                raise rmf
            else:
                return 0

    def hist_product_daily_management_fee_receivable(self, product: str, fund_name: str, date: datetime.date):
        if (product, fund_name) in [('稳健12号', '稳健7号'), ]:
            today_rec = self.hist_product_management_fee_receivable(product=product, fund_name=fund_name, date=date,)
            last_rec = self.hist_product_management_fee_receivable(
                product=product, fund_name=fund_name, date=date - datetime.timedelta(days=1),
            )
        else:
            today_rec = self.hist_product_accumulated_management_fee_receivable(
                product=product, fund_name=fund_name, date=date,
            )
            last_rec = self.hist_product_accumulated_management_fee_receivable(
                product=product, fund_name=fund_name, date=date - datetime.timedelta(days=1)
            )
        if not is_valid_float(last_rec):
            last_rec = 0
        if not is_valid_float(today_rec):
            raise NotImplementedError('{} {} {} {}'.format(product, fund_name, date, last_rec))
        assert today_rec >= last_rec, '{} {} {} {} {}'.format(product, fund_name, date, today_rec, last_rec)
        return today_rec - last_rec

    @staticmethod
    def __get_fund_column_name__(product: str, fund_name: str):
        if (product, fund_name) in [
            ('收益1号', '稳健21号'), ('稳健6号', '稳健18号'), ('稳健6号', '稳健22号'), ('稳健16号', '稳健21号'),
            ('稳健7号', '稳健22号'), ('稳健7号', '稳健16号'), ('收益1号', '稳健22号'),
        ]:
            key_tag = fund_name
        elif product in ('稳健3号', '稳健2号', '稳健5号', '稳健7号', '稳健18号', ):
            key_tag = '{}市值'.format(fund_name)
        elif product == '稳健6号' and '稳健' in fund_name:
            key_tag = '{}市值'.format(fund_name)
        else:
            key_tag = '{}基金市值'.format(fund_name)
        return key_tag

    def hist_product_fund_holding_market_value(self, product: str, fund_name: str, date: datetime.date):
        pd_data = self.__load_product__(product, date=date)
        if (product, fund_name) in [('收益1号', '久铭2号'), ]:
            key_tag = self.__search_pd_column__(pd_data, fund_name)
        else:
            key_tag = self.__get_fund_column_name__(product=product, fund_name=fund_name)
        return self.__derive_pd_content__(pd_data, date=date, tag=key_tag, shift=0)

    def hist_product_fund_holding_net_value_per_unit(self, product: str, fund_name: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        if fund_name in ('中海久铭1号', ):
            key_tag = '中海-久铭1号信托计划'
        elif fund_name in ('启元18号', ):
            key_tag = '启元18号'
        elif fund_name == '浦江之星289号':
            key_tag = self.__search_pd_column__(pd_data, '浦江之星')
        elif fund_name == '同晖1号':
            key_tag = self.__search_pd_column__(pd_data, '合晟同晖')
        elif fund_name in ('浦睿1号', '久铭2号'):
            key_tag = self.__search_pd_column__(pd_data, fund_name)
        else:
            key_tag = self.__get_fund_column_name__(product=product, fund_name=fund_name)
        return self.__derive_pd_content__(pd_data, date=date, tag=key_tag, shift=3)

    def hist_product_bond_holding_price(self, product: str, bond_name: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        if bond_name == '17宝武EB':
            if product in ('稳健6号', ):
                key_tag = '可交换债收盘'
            else:
                key_tag = '宝武eb收盘'
        else:
            raise NotImplementedError(bond_name)
        return self.__derive_pd_content__(pd_data, date=date, tag=key_tag, shift=0)

    # def hist_product_meigu_market_value(self, product: str, date: datetime.date):
    #     pd_data = self.__load_product__(product=product, date=date)
    #     return self.__derive_pd_content__(pd_data, date, '美股市值（cny)', shift=0)

    def hist_product_meigu_daily_interest_payable(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = '美股市值（cny)'
        today_paid = (self.__derive_pd_content__(pd_data, date, tag, shift=3) -
                      self.__derive_pd_content__(pd_data, date, tag, shift=4)) * self.__derive_pd_content__(
            pd_data, date, tag, shift=-2)
        last_paid = (self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=3)
                     - self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=4)
                     ) * self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=-2)
        if not is_valid_float(self.__derive_pd_content__(pd_data, date, tag, shift=-2)):
            return 0.0
        if not is_valid_float(last_paid) and not is_valid_float(today_paid):
            return 0.0
        if not is_valid_float(last_paid):
            last_paid = 0.0
        if not is_valid_float(today_paid):
            return 0.0
        return (today_paid - last_paid) + self.hist_product_meigu_interest_paid(product, date)

    def hist_product_meigu_interest_paid(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = '美股市值（cny)'
        last_paid = self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=4)
        today_paid = self.__derive_pd_content__(pd_data, date, tag, shift=4)
        if not is_valid_float(last_paid):
            last_paid = 0.0
        if not is_valid_float(today_paid):
            today_paid = 0.0
        if abs(last_paid - today_paid) < 0.01:
            return 0.0
        else:
            return (today_paid - last_paid) * self.__derive_pd_content__(pd_data, date, tag, shift=-2)

    def hist_product_meigu_deposit(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = '美股保证金（cny)'
        amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
        if is_valid_float(amount):
            return amount
        else:
            return 0.0

    def hist_product_meigu_total_value(self, product: str, date: datetime.date):
        return self.hist_product_meigu_market_value(product, date) + self.hist_product_meigu_deposit(product, date)

    def hist_product_meigu_market_value(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = '美股市值（cny)'
        amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
        if is_valid_float(amount):
            return amount
        else:
            return 0.0

    def hist_product_ganggu_daily_interest_payable(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = '港股市值（cny)'
        today_paid = (self.__derive_pd_content__(pd_data, date, tag, shift=3) -
                      self.__derive_pd_content__(pd_data, date, tag, shift=4)) * self.__derive_pd_content__(
            pd_data, date, tag, shift=-2)
        last_paid = (self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=3)
                     - self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=4)
                     ) * self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=-2)
        if not is_valid_float(self.__derive_pd_content__(pd_data, date, tag, shift=-2)):
            return 0.0
        if not is_valid_float(last_paid) and not is_valid_float(today_paid):
            return 0.0
        if not is_valid_float(last_paid):
            last_paid = 0.0
        if not is_valid_float(today_paid):
            return 0.0
        return (today_paid - last_paid) + self.hist_product_ganggu_interest_paid(product, date)

    def hist_product_ganggu_interest_paid(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = '港股市值（cny)'
        last_paid = self.__derive_pd_content__(pd_data, date - datetime.timedelta(days=1), tag, shift=4)
        today_paid = self.__derive_pd_content__(pd_data, date, tag, shift=4)
        if not is_valid_float(last_paid):
            last_paid = 0.0
        if not is_valid_float(today_paid):
            today_paid = 0.0
        if abs(last_paid - today_paid) < 0.01:
            return 0.0
        else:
            return (today_paid - last_paid) * self.__derive_pd_content__(pd_data, date, tag, shift=-2)

    def hist_product_ganggu_total_value(self, product: str, date: datetime.date):
        return self.hist_product_ganggu_market_value(product, date) + self.hist_product_ganggu_deposit(product, date)

    def hist_product_ganggu_deposit(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = '港股保证金（cny)'
        amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
        if is_valid_float(amount):
            return amount
        else:
            return 0.0

    def hist_product_ganggu_market_value(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = '港股市值（cny)'
        amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
        if is_valid_float(amount):
            return amount
        else:
            return 0.0

    def hist_product_bank_cash(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = '银行存款'
        return self.__derive_pd_content__(pd_data, date, tag, shift=0)

    def hist_product_ping_an_cash(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        if product in ('全球1号', '收益1号'):
            tag = '募集户存款（平安）'
        else:
            tag = '平安募集户'
        amount = self.__derive_pd_content__(pd_data, date, tag, shift=0)
        if not is_valid_float(amount):
            amount = 0
        return amount

    def hist_product_guo_jun_cash(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        if product == '稳健17号':
            tag = '证券存出保证金（国君）'
        else:
            tag = '证券存出保证金'
        return self.__derive_pd_content__(pd_data, date, tag, shift=0)

    def hist_product_stock_market_value(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        if product == '稳健15号':
            tag = '证券市值'
        else:
            tag = '股票市值'
        return self.__derive_pd_content__(pd_data, date, tag, shift=0)

    def hist_product_stock_new_value(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        try:
            tag = self.__search_pd_column__(pd_data, '新股')
            return self.__derive_pd_content__(pd_data, date, tag, shift=0)
        except KeyError:
            return 0.0

    def hist_product_bond_baowu_interest_receivable(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        try:
            tag = '宝武eb收盘'
            return self.__derive_pd_content__(pd_data, date, tag, shift=1) - self.__derive_pd_content__(
                pd_data, date - datetime.timedelta(days=1), tag, shift=1)
        except ValueError:
            return 0.0

    def hist_vat(self, product: str, date: datetime.date):
        pd_data = self.__load_product__(product=product, date=date)
        tag = self.__search_pd_column__(pd_data, '预提增值税')
        vat = self.__derive_pd_content__(pd_data, date, tag, shift=0)
        if not is_valid_float(vat):
            vat = 0.0
        return vat

    @staticmethod
    def __print_patterned_column_list__(pd_data: pd.DataFrame, tag: str):
        column_list = list()
        for col in pd_data.columns:
            if tag in col:
                column_list.append(col)
        print(column_list)


if __name__ == '__main__':
    pass
    # import os
    # from core.Environment import Environment
    #
    # env = Environment()
    #
    # ds = ValuationTableDataSource(os.path.join(env.root_path(), '..', '2018.12.14'))
    # ds.load_fund_net_value()

    # from sheets.Information import ProductInfo
    # from sheets.entry.Position import EntryPosition
    # pro_list = DataList.from_pd(EntryPosition, env.data_base.read_pd_query(
    #     DataBaseName.management,
    #     """SELECT * FROM `会计产品持仓表`;"""
    # ))
    # for obj in pro_list:
    #     assert isinstance(obj, EntryPosition)
    #     sql = """UPDATE `录入基金交易流水` SET `产品代码` = '{}' WHERE `产品名称` = '{}';""".format(
    #         obj.security_code, obj.security_name
    #     )
    #     env.data_base.execute(DataBaseName.management, sql)
    #     print(sql)

    # name_code_map = {
    #     '启元18号': 'ST1188', '长安鑫垚': '004907.OF', '长安鑫恒': '004898.OF', '贝溢一号': 'SW3945',
    # }
    # for name, code in name_code_map.items():
    #     sql = """UPDATE `2018上半年基金交易流水` SET `产品代码` = '{}' WHERE `产品名称` = '{}';""".format(
    #         code, name
    #     )
    #     env.data_base.execute(DataBaseName.management, sql)
    #     sql = """UPDATE `录入基金交易流水` SET `产品代码` = '{}' WHERE `产品名称` = '{}';""".format(
    #         code, name
    #     )
    #     env.data_base.execute(DataBaseName.management, sql)

    # env.exit()
