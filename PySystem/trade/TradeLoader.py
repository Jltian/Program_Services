# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import os
import re
import xlrd
import datetime

import pandas as pd

from xlrd.biffh import XLRDError

from jetend.structures import List, MySQL, Sqlite
from jetend.Constants import DataBaseName
from jetend.jmSheets import *

from trade.LoadTools import load_csv, load_xlsx_like

from trade.Interface import AbstractLoader
from trade.institutions.AnXin import AnXin
from trade.institutions.ChangAn import ChangAn
from trade.institutions.ChangJiang import ChangJiang
from trade.institutions.DeBang import DeBang
from trade.institutions.DongFang import DongFang
from trade.institutions.GuoJun import GuoJun
from trade.institutions.GuoXin import GuoXin
from trade.institutions.HuaChuang import HuaChuang
from trade.institutions.HuaJing import HuaJing
from trade.institutions.HuaTai import HuaTai
from trade.institutions.ShenWan import ShenWan
from trade.institutions.XingYe import XingYe
from trade.institutions.ZhongJin import ZhongJin
from trade.institutions.ZhaoShang import ZhaoShang
from trade.institutions.ZhongXin import ZhongXin
from trade.Checker import *


class TradeFlowLoader(object):
    institution_loader_map = {
        # 普通账户
        '安信证券': AnXin, '长江证券': ChangJiang, '德邦证券': DeBang, '东方证券': DongFang,
        '华创证券': HuaChuang, '华菁证券': HuaJing, '华泰证券': HuaTai,
        '国信证券': GuoXin, '国君证券': GuoJun, '申万证券': ShenWan, '兴业证券': XingYe,
        '中金证券': ZhongJin, '招商证券': ZhaoShang, '中信证券': ZhongXin,
        # 港股通
        '安信证券港股通': AnXin,
        '长江证券港股通': ChangJiang,
        '德邦证券港股通': DeBang,
        '东方证券港股通': DongFang,
        '国君证券港股通': GuoJun,
        '国信证券港股通': GuoXin,
        '申万证券港股通': ShenWan,
        '兴业证券港股通': XingYe,
        '招商证券港股通': ZhaoShang,
        '中金证券港股通': ZhongJin,
        '中信证券港股通': ZhongXin,
        # 长安
        '长安基金': ChangAn,
        # 期货账户
        '国投安信': AnXin, '安信期货': AnXin, '长江期货': ChangJiang,
    }

    def __init__(self, db: MySQL, folder_path: str):
        from jetend import get_logger
        from jetend.modules.jmInfoBoard import jmInfoBoard
        from jetend.modules.jmMarketBoard import jmMarketBoard
        self.log = get_logger(self.__class__.__name__)
        self.db = db
        self.info_board = jmInfoBoard(self.db)
        from WindPy import w
        w.start()
        self.market_board = jmMarketBoard(w, Sqlite())

        self.normal_flow = List()       # 普通
        self.margin_flow = List()       # 两融
        self.future_flow = List()       # 期货
        self.option_flow = List()       # 期权

        self.security_position_list = List()        # 证券持仓列表
        self.account_deposition_list = List()       # 账户余额列表

        self.current_date = None
        assert os.path.exists(folder_path), '当日交易流水路径 {} 不存在'.format(folder_path)
        self.__path__ = folder_path

    def load_simple_output_flow(self, date: datetime.date):
        """载入陈田田的交易流水 -> List(TradeFlow, )"""
        folder_path = os.path.join(self.__path__, '当日成交{}'.format(date.strftime('%Y%m%d')))
        assert os.path.exists(folder_path), '当日成交文件夹 {} 不存在'.format(folder_path)
        self.current_date = date
        self.log.debug('READING FLOW ON DATE {}'.format(self.current_date))

        # ---- [读取流水] ----
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            # 忽略隐藏文件和临时文件
            if file_name.startswith('.') or file_name.startswith('~'):
                continue

            # 需要手动解压压缩文件包
            if file_name.lower().endswith('rar') or file_name.lower().endswith('zip'):
                raise RuntimeError('存在文件 {}，请确认该文件已正确解压'.format(file_name))

            # 逐个处理excel文件
            self.log.debug_running('读取当日交易流水', file_name)
            try:
                product, account_type, institution = re.search(
                    r'(\D+\d*[号指数信利]+)([股票两融期货权美港收益互换]+)(\w+)', file_name, flags=re.I,
                ).groups()
            except AttributeError as f_a_e:
                self.log.error(file_name)
                raise f_a_e

            if '久铭创新' in product:
                product = product.replace('久铭', '')
            if '久铭专享' in product:
                product = product.replace('久铭', '')

            try:
                loader_cls = self.institution_loader_map[institution]
            except KeyError:
                raise NotImplementedError(file_name)
            assert issubclass(loader_cls, AbstractLoader), loader_cls.__name__

            file_type = file_name.lower().split('.')[-1]
            if file_type in ('xls', 'xlsx'):
                file_content = load_xlsx_like(file_path)
                # try:
                #     file_content = xlrd.open_workbook(file_path, encoding_override='gb18030')
                # except XLRDError:
                #     content_list = list()
                #     content_file = open(file_path, mode='r', ).read()
                #     for content_line in content_file.split('\n'):
                #         line_list = list()
                #         for content_cell in content_line.split('\t'):
                #             if re.match(r'=\"([^\"])\"', content_cell):
                #                 try:
                #                     line_list.append(re.search(r'=\"([^\"=]*)\"', content_cell).groups()[0])
                #                 except AttributeError as a_error:
                #                     print(content_cell, '\n', content_line)
                #                     raise a_error
                #             elif re.match(r'=\"([\w\W]*)\"', content_cell):
                #                 line_list.append(re.search(r'=\"([^\"]*)\"', content_cell).groups()[0])
                #             elif len(re.sub(r'[Ee\d.,:+]', '', content_cell.replace('-', ''))) == 0:     # 数字表达
                #                 line_list.append(content_cell)
                #             elif len(re.sub(r'\W', '', content_cell)) == 0:
                #                 line_list.append('-')
                #             elif len(re.sub(r'[\w()]', '', content_cell)) == 0:
                #                 line_list.append(content_cell)
                #             elif len(re.sub(r'[\w]', '', content_cell.replace(' ', ''))) == 0:
                #                 line_list.append(content_cell.replace(' ', ''))
                #             # elif re.match(r'([\w\W]*)', content_cell):
                #             #     line_list.append(content_cell)
                #             else:
                #                 raise NotImplementedError('{}\n{}'.format(content_cell, content_line))
                #         content_list.append('|'.join(line_list))
                #     file_content = '\n'.join(content_list)
            elif file_type in ('csv', ):
                file_content = load_csv(file_path)
                # file_content = pd.read_csv(os.path.join(folder_path, file_name), encoding='gb18030')
            else:
                raise NotImplementedError(file_name)

            if account_type == '股票':
                flow_list = loader_cls.convert_column_map(file_content, loader_cls.normal_flow)
                for flow in flow_list:
                    flow.update({
                        'product': product, 'date': date, 'institution': institution,
                        'currency': 'RMB', 'account_type': '普通账户',
                    })
                    try:
                        trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
                    except ValueError:
                        try:
                            trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S.%f').time()
                        except ValueError:
                            trade_time = datetime.time(hour=0, minute=0, second=0)
                    flow['trade_time'] = trade_time
                    flow['trade_name'] = str_check(flow['trade_class'])
                    # trade_status = str_check(flow['trade_status'])
                    # assert trade_status == '成交', str(flow)
                    if '港股通' in institution:
                        flow['trade_amount'] = float_check(flow['trade_price']) * float_check(flow['trade_volume'])
                    trade_class = str_check(flow['trade_class'])
                    if trade_class in (
                            '买入', '买', '增强限价盘买入'
                    ):
                        flow['trade_direction'] = TRADE_DIRECTION_BUY
                    elif trade_class in (
                            '卖出', '卖', '限价卖出'
                    ):
                        flow['trade_direction'] = TRADE_DIRECTION_SELL
                    else:
                        raise NotImplementedError('{}\n{}'.format(trade_class, flow))
                confirm_normal_trade_flow_list(flow_list)
                # # try:
                # #     loaded_result = loader_cls.load_normal_excel(file_path, product, date, institution)
                # # except NotImplementedError:
                # #     loaded_result = loader_cls.load_normal_text(file_content, product, date, institution)
                # if isinstance(file_content, str):
                #     loaded_result = loader_cls.load_normal_text(file_content, product, date, institution)
                # elif isinstance(file_content, (pd.DataFrame, xlrd.Book)):
                #     loaded_result = loader_cls.load_normal_excel(file_path, product, date, institution)
                # else:
                #     raise NotImplementedError('{} {}'.format(type(file_content), file_content))
                self.normal_flow.extend(List.from_dict_list(DailyNormalTradeFlow, flow_list))

            elif account_type == '两融':
                if institution == '国君证券':
                    loaded_result = loader_cls.load_margin_excel(
                        os.path.join(folder_path, file_name), product, date, institution,
                    )
                else:
                    loaded_result = loader_cls.load_simple_margin(
                        os.path.join(folder_path, file_name), product, date, institution,
                    )
                self.margin_flow.extend(List.from_dict_list(DailyMarginTradeFlow, loaded_result))

            elif account_type == '期货':
                flow_list = loader_cls.convert_column_map(file_content, loader_cls.future_flow)
                for flow in flow_list:
                    flow.update({
                        'product': product, 'date': date, 'institution': institution,
                        'currency': 'RMB', 'account_type': '期货账户',
                    })
                    trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
                    flow['trade_time'] = trade_time
                    trade_class = str_check(flow['trade_class'])
                    if trade_class in ('买',):
                        flow['trade_direction'] = TRADE_DIRECTION_BUY
                    elif trade_class in ('卖', ):
                        flow['trade_direction'] = TRADE_DIRECTION_SELL
                    else:
                        raise NotImplementedError(flow)
                confirm_option_trade_flow_list(flow_list)
                self.future_flow.extend(List.from_dict_list(DailyFutureTradeFlow, flow_list))

            elif account_type == '期权':
                flow_list = loader_cls.convert_column_map(file_content, loader_cls.option_flow)
                for flow in flow_list:
                    flow.update({
                        'product': product, 'date': date, 'institution': institution,
                        'currency': 'RMB', 'account_type': '期权账户',
                    })
                    trade_time = datetime.datetime.strptime(flow['trade_time'], '%H:%M:%S').time()
                    flow['trade_time'] = trade_time
                    trade_class = str_check(flow['trade_class'])
                    if trade_class in ('买', ):
                        flow['trade_direction'] = TRADE_DIRECTION_BUY
                    elif trade_class in ('卖', ):
                        flow['trade_direction'] = TRADE_DIRECTION_SELL
                    else:
                        raise NotImplementedError(flow)
                confirm_option_trade_flow_list(flow_list)
                self.option_flow.extend(List.from_dict_list(DailyOptionTradeFlow, flow_list))

            elif account_type in ('美股收益互换', '港股收益互换'):
                if '开曼' in file_name:
                    raise NotImplementedError('{} {}'.format(account_type, file_name))
                loaded_result = ZhongXin.load_swap_excel(file_path, product, date, account_type)
                for flow in loaded_result:
                    fee_amount = 0.0
                    if flow['trade_direction'] == TRADE_DIRECTION_BUY:
                        flow['cash_move'] = - abs(flow['trade_amount']) - fee_amount
                    elif flow['trade_direction'] == TRADE_DIRECTION_SELL:
                        flow['cash_move'] = abs(flow['trade_amount']) - fee_amount
                    else:
                        raise NotImplementedError(flow)

                self.normal_flow.extend(List.from_dict_list(DailyNormalTradeFlow, loaded_result))

            else:
                raise NotImplementedError(file_name)

        sql_template = "DELETE FROM {} WHERE 日期 = '{}'"

        if len(self.normal_flow) > 0:
            self.log.info_running('储存当日普通流水')
            self.db.execute(DataBaseName.management, sql_template.format('当日普通交易流水', self.current_date))
            self.db.insert_data_list(DataBaseName.management, '当日普通交易流水', self.normal_flow)

        # self.log.debug(self.margin_flow)
        if len(self.margin_flow) > 0:
            self.log.info_running('储存当日两融流水')
            self.db.execute(DataBaseName.management, sql_template.format('当日两融交易流水', self.current_date))
            self.db.insert_data_list(DataBaseName.management, '当日两融交易流水', self.margin_flow)

        if len(self.future_flow) > 0:
            self.log.info_running('储存当日期货流水')
            self.db.execute(DataBaseName.management, sql_template.format('当日期货交易流水', self.current_date))
            self.db.insert_data_list(DataBaseName.management, '当日期货交易流水', self.future_flow)

        if len(self.option_flow) > 0:
            self.log.info_running('储存当日期权流水')
            self.db.execute(DataBaseName.management, sql_template.format('当日期权交易流水', self.current_date))
            self.db.insert_data_list(DataBaseName.management, '当日期权交易流水', self.future_flow)

    def update_security_position(self, date: datetime.date):
        self.current_date = date

        for pos in List.from_pd(DailySecurityPosition, self.db.read_pd_query(DataBaseName.management, """
        SELECT * FROM `当日证券持仓` WHERE 日期 = (SELECT MAX(日期) FROM `当日证券持仓` WHERE 日期 < '{}');""".format(
            self.current_date))):
            pos.date = self.current_date
            if abs(pos.volume) < 0.01:
                continue
            else:
                self.security_position_list.append(pos)
        # last_date = list(self.security_position_list.collect_attr_set('date'))[0]

        sql_template = "SELECT * FROM {} WHERE 日期 = '{}';"

        flow_list = List.from_pd(BankFlow, self.db.read_pd_query(
            DataBaseName.journal, sql_template.format('银行标准流水', self.current_date)))
        new_pos_institution_map = {
            '久铭1号': '安信普通', '久铭9号': '国君普通', '稳健1号': '国君普通', '稳健22号': '招商普通',
            '久铭5号': '申万普通', '收益2号': '国君普通', '稳健23号': '德邦普通', '创新稳健2号': '兴业普通',
        }
        for flow in flow_list:
            if flow.trade_class in ('新股缴款', ):
                security_code, security_name, volume = re.match(r'(\d+)[（(](\w+)）(\d+)股', flow.subject).groups()
                assert isinstance(security_code, str)
                if security_code.startswith('6'):
                    security_code = '.'.join([security_code, 'SH'])
                else:
                    raise NotImplementedError(flow)
                pos = DailySecurityPosition(
                    product=flow.product, date=self.current_date, volume_type='-',
                    security_code=security_code, security_name=security_name,
                    volume=volume, institution=new_pos_institution_map[flow.product],
                )
                self.security_position_list.append(pos)
            elif flow.trade_class in (
                    '银证转账', '赎回', '申购', '管理费返还', '认购', '业绩报酬', '管理费', '证券开户费', '增值税及附加',
                    '印刷费支付', '开户费', '基金投资', '利息归本', '托管费', '运营服务费', '业绩报酬返还',
                    '申购退回款',
            ):
                continue
            else:
                raise NotImplementedError(flow)

        flow_list = List.from_pd(DailyNormalTradeFlow, self.db.read_pd_query(
            DataBaseName.management, sql_template.format('当日普通交易流水', self.current_date)
        ))          # 普通账户交易流水
        for flow in flow_list:
            assert isinstance(flow, DailyNormalTradeFlow)
            try:
                # 新股
                if flow.security_name.startswith('N'):
                    pos = self.security_position_list.find_value(
                        product=flow.product, security_code=flow.security_code,
                        # institution='-',
                    )
                    pos.institution = flow.institution.replace('证券', '普通').replace('港股通', '')
                else:
                    pos = self.security_position_list.find_value(
                        product=flow.product, security_code=flow.security_code,
                        institution=flow.institution.replace('证券', '普通').replace('港股通', ''),
                    )
            except ValueError:
                if flow.security_name.startswith('N'):
                    pos = DailySecurityPosition(
                        product=flow.product, date=self.current_date,
                        institution=flow.institution.replace('证券', '普通').replace('港股通', ''),
                        security_code=flow.security_code, security_name=flow.security_name,
                        volume=abs(flow.trade_volume), volume_type='-'
                    )
                else:
                # assert not flow.security_name.startswith('N'), str(flow)
                    pos = DailySecurityPosition(
                        product=flow.product, date=self.current_date,
                        institution=flow.institution.replace('证券', '普通').replace('港股通', ''),
                        security_code=flow.security_code, security_name=flow.security_name,
                        volume=0.0, volume_type='-'
                    )
                self.security_position_list.append(pos)
            if flow.trade_direction == TRADE_DIRECTION_BUY:
                pos.volume += abs(flow.trade_volume)
            elif flow.trade_direction == TRADE_DIRECTION_SELL:
                pos.volume -= abs(flow.trade_volume)
            else:
                raise NotImplementedError(flow)
            # assert pos.volume >= 0.0, '{}\n{}'.format(pos, flow)

        flow_list = List.from_pd(DailyMarginTradeFlow, self.db.read_pd_query(
            DataBaseName.management, sql_template.format('当日两融交易流水', self.current_date)
        ))          # 两融账户交易流水
        for flow in flow_list:
            assert isinstance(flow, DailyMarginTradeFlow)
            try:
                pos = self.security_position_list.find_value(
                    product=flow.product, security_code=flow.security_code, volume_type=flow.trade_class,
                    institution=flow.institution.replace('证券', '两融').replace('港股通', ''),
                )
            except ValueError:
                pos = DailySecurityPosition(
                    product=flow.product, date=self.current_date,
                    institution=flow.institution.replace('证券', '两融').replace('港股通', ''),
                    security_code=flow.security_code, security_name=flow.security_name,
                    volume=0.0, volume_type=flow.trade_class,
                )
                self.security_position_list.append(pos)
            if flow.trade_direction == TRADE_DIRECTION_BUY:
                pos.volume += abs(flow.trade_volume)
            elif flow.trade_direction == TRADE_DIRECTION_SELL:
                pos.volume -= abs(flow.trade_volume)
            else:
                raise NotImplementedError(flow)

        flow_list = List.from_pd(DailyFutureTradeFlow, self.db.read_pd_query(
            DataBaseName.management, sql_template.format('当日期货交易流水', self.current_date)
        ))          # 期货账户交易流水
        for flow in flow_list:
            assert isinstance(flow, DailyFutureTradeFlow)
            if (flow.trade_direction, flow.trade_offset) in [
                (TRADE_DIRECTION_BUY, '开仓'), (TRADE_DIRECTION_SELL, '平仓'),
            ]:
                try:
                    pos = self.security_position_list.find_value(
                        product=flow.product, security_code=flow.security_code,
                        institution=flow.institution, volume_type='多',
                    )
                except ValueError:
                    pos = DailySecurityPosition(
                        product=flow.product, date=self.current_date, institution=flow.institution,
                        security_code=flow.security_code, volume=0.0, volume_type='多',
                    )
                    self.security_position_list.append(pos)
                if flow.trade_direction == TRADE_DIRECTION_BUY:
                    pos.volume += abs(flow.trade_volume)
                elif flow.trade_direction == TRADE_DIRECTION_SELL:
                    pos.volume -= abs(flow.trade_volume)
                else:
                    raise NotImplementedError(flow)
            elif (flow.trade_direction, flow.trade_offset) in [
                (TRADE_DIRECTION_SELL, '开仓'), (TRADE_DIRECTION_BUY, '平仓'),
            ]:
                try:
                    pos = self.security_position_list.find_value(
                        product=flow.product, security_code=flow.security_code,
                        institution=flow.institution, volume_type='空',
                    )
                except ValueError:
                    pos = DailySecurityPosition(
                        product=flow.product, date=self.current_date, institution=flow.institution,
                        security_code=flow.security_code, volume=0.0, volume_type='空',
                    )
                    self.security_position_list.append(pos)
                if flow.trade_direction == TRADE_DIRECTION_BUY:
                    pos.volume += abs(flow.trade_volume)
                elif flow.trade_direction == TRADE_DIRECTION_SELL:
                    pos.volume -= abs(flow.trade_volume)
                else:
                    raise NotImplementedError(flow)
            else:
                raise NotImplementedError(flow)

        sql_template = "DELETE FROM {} WHERE 日期 = '{}';"
        self.log.info_running('储存当日证券持仓')
        self.db.execute(DataBaseName.management, sql_template.format('当日证券持仓', self.current_date))
        self.db.insert_data_list(DataBaseName.management, '当日证券持仓', self.security_position_list)

    def compare_security_position(self, date: datetime.date):
        self.current_date = date

        last_list = List.from_pd(DailySecurityPosition, self.db.read_pd_query(DataBaseName.management, """
        SELECT * FROM `当日证券持仓` WHERE 日期 = (SELECT MAX(日期) FROM `当日证券持仓` WHERE 日期 < '{}');""".format(date)))
        # self.log.debug(last_list)
        today_list = List.from_pd(DailySecurityPosition, self.db.read_pd_query(
            DataBaseName.management, """SELECT * FROM `当日证券持仓` WHERE 日期 = '{}';""".format(date)))

        output_file = open(os.path.join('D:\Downloads', '{} 当日交易流水持仓变化.txt'.format(date)), mode='w')

        output_file.write('{} 产品持仓变化：\n'.format(date))

        product_set = last_list.collect_attr_set('product')
        product_set.update(today_list.collect_attr_set('product'))
        for product in product_set:
            security_set = last_list.find_value_where(product=product).collect_attr_set('security_code')
            security_set.update(today_list.find_value_where(product=product).collect_attr_set('security_code'))
            for security_code in security_set:
                last_volume = last_list.find_value_where(
                    product=product, security_code=security_code).sum_attr('volume')
                today_volume = today_list.find_value_where(
                    product=product, security_code=security_code).sum_attr('volume')
                if abs(last_volume) < 0.01 and abs(today_volume) >= 0.01:
                    output_file.write('\n产品 {} 增加持仓 {}'.format(product, security_code))
                elif abs(last_volume) >= 0.01 and abs(today_volume) < 0.01:
                    output_file.write('\n产品 {} 减少持仓 {}'.format(product, security_code))
                else:
                    continue

        output_file.close()

    def update_account_deposition(self, date: datetime.date):
        from jetend.modules.jmInfoBoard import jmInfoBoard
        info_board = jmInfoBoard(self.db)
        self.current_date = date

        last_acc_date = None
        for acc in List.from_pd(DailyAccountDeposition, self.db.read_pd_query(DataBaseName.management, """
        SELECT * FROM `当日账户余额` WHERE 日期 = (SELECT MAX(日期) FROM `当日账户余额` WHERE 日期 < '{}');""".format(
            self.current_date))):
            if last_acc_date is None:
                last_acc_date = acc.date
            else:
                assert last_acc_date == acc.date, '{}\n{}'.format(last_acc_date, acc)
            acc.date = self.current_date
            self.account_deposition_list.append(acc)
        assert isinstance(last_acc_date, datetime.date), self.account_deposition_list

        flow_list = List.from_pd(BankFlow, self.db.read_pd_query(DataBaseName.journal, """
        SELECT * FROM 银行标准流水 WHERE 日期 > '{}' AND 日期 <= '{}';""".format(last_acc_date, self.current_date)))
        sub_data_list = List()
        for obj in flow_list:
            assert isinstance(obj, BankFlow)
            if is_valid_str(obj.extra_info):
                assert obj.extra_info == '内部', obj.__dict__
                if obj.trade_class == '申购':
                    sub_data_list.append(BankFlow(
                        product=obj.opposite, date=obj.date, institution='-',
                        trade_class='基金投资', opposite='久铭', subject=obj.product,
                        trade_amount=-obj.trade_amount,
                    ))
                elif obj.trade_class == '认购':
                    sub_data_list.append(BankFlow(
                        product=obj.opposite, date=obj.date, institution='-',
                        trade_class='认购', opposite='久铭', subject=obj.product,
                        trade_amount=-obj.trade_amount,
                    ))
                elif obj.trade_class == '赎回':
                    sub_data_list.append(BankFlow(
                        product=obj.opposite, date=obj.date, institution='-',
                        trade_class='基金投资', opposite='久铭', subject=obj.product,
                        trade_amount=-obj.trade_amount,
                    ))
                elif obj.trade_class in ('份额转换',):
                    sub_data_list.append(BankFlow(
                        product=obj.opposite, date=obj.date, institution='-', trade_class='份额转换',
                        opposite=obj.product, trade_amount=-obj.trade_amount,
                    ))
                elif obj.trade_class in ('份额转换差额',):
                    sub_data_list.append(BankFlow(
                        product=obj.opposite, date=obj.date, institution='-', trade_class='份额转换差额',
                        opposite=obj.product, trade_amount=-obj.trade_amount,
                    ))
                elif obj.trade_class in ('托管户互转',):
                    pass
                elif obj.trade_class == '基金转出':
                    assert obj.trade_amount < 0, obj.__dict__
                    sub_data_list.append(BankFlow(
                        product=obj.opposite, date=obj.date, institution='-', trade_class='基金转入',
                        opposite=obj.product, trade_amount=-obj.trade_amount,
                    ))
                else:
                    raise NotImplementedError(obj.__dict__)
            else:
                pass
        flow_list.extend(sub_data_list)
        for flow in flow_list:
            self.log.debug(flow)
            flow_product = flow.product.replace('久铭专享', '专享', ).replace('久铭信利1号', '信利1号', )
            # 证券账户余额变化
            if flow.trade_class in ('银证转账', ):
                # opposite_institution = flow.opposite.replace('美股收益互换', '中信美股')
                if flow.opposite in ('美股收益互换', '港股收益互换', ):     # 收益互换暂时不在证券账户余额表中
                    continue
                # if flow.opposite in ('国投安信期货', ) and '指数' in flow_product:
                #     continue
                flow_opposite = flow.opposite.replace('信用', '两融').replace(
                    '中信（山东）', '中信'
                ).replace('中信(山东)', '中信')
                try:
                    acc = self.account_deposition_list.find_value(product=flow_product, institution=flow_opposite)
                except ValueError as v_error:
                    if '期货' in flow.opposite:
                        continue
                    # if flow.trade_amount < 0:
                    #     self.account_deposition_list.append(DailyAccountDeposition(
                    #         product=flow_product, date=date, account_type
                    #     ))
                    #     inner2outer_map = {
                    #         'product': '产品', 'date': '日期', 'account_type': '账户类型', 'institution': '机构',
                    #         'volume': '余额', 'currency': '币种', 'institution_combined': '券商',
                    #     }
                    print(self.account_deposition_list.find_value_where(product=flow.product))
                    raise ValueError('流水 {} 找不到账户'.format(flow))
                except RuntimeError as r_error:
                    acc_list = self.account_deposition_list.find_value_where(
                        product=flow_product, institution=flow.opposite)
                    acc = None
                    if len(acc_list) == 2 and '银行活期' in acc_list.collect_attr_set('account_type'):
                        for obj in acc_list:
                            if obj.account_type != '银行活期':
                                acc = obj
                        assert isinstance(acc, DailyAccountDeposition)
                    else:
                        print(self.account_deposition_list.find_value_where(product=flow.product))
                        raise r_error
                acc.volume = acc.volume - flow.trade_amount
            elif flow.trade_class in (
                    '赎回', '申购', '管理费返还', '认购', '业绩报酬', '新股申购', '托管费', '基金投资', '运营服务费',
                    '管理费', '增值税及附加', '托管户互转', '网银汇款手续费', '新股缴款', '证券开户费', '印刷费支付',
                    '开户费', '利息归本', '业绩报酬返还',
            ):
                continue
            else:
                raise NotImplementedError(flow)
        for flow in flow_list:
            self.log.debug(flow)
            flow_product = flow.product.replace('久铭专享1号', '专享1号', ).replace('久铭信利1号', '信利1号', ).replace(
                '久铭信利2号', '信利2号').replace('上证50指数', '久铭50指数').replace('沪深300指数', '久铭300指数').replace(
                '中证500指数', '久铭500指数').replace('久铭专享5号', '专享5号', )
            # 银行存款余额变化
            if flow.institution == '-':
                acc = self.account_deposition_list.find_value(product=flow_product, account_type='银行活期', )
            else:
                acc = self.account_deposition_list.find_value(
                    product=flow_product, account_type='银行活期', institution=flow.institution)
            acc.volume = acc.volume + flow.trade_amount

        def parse_security_code(security_code: str):
            assert '.' in security_code, security_code
            exchange_tag = security_code.split('.')[-1]
            if exchange_tag == 'SH':
                if security_code[:2] in ('60', '68', ):
                    type_tag = '股票'
                elif security_code[:2] in ('51', ):
                    type_tag = 'ETF'
                elif security_code[:3] in ('110', '113', ):
                    type_tag = '转债'
                elif security_code[:3] in ('132', ):
                    type_tag = '交债'
                else:
                    raise NotImplementedError(security_code)
            elif exchange_tag == 'SZ':
                if security_code[:2] in ('00', ):
                    type_tag = '股票'
                else:
                    raise NotImplementedError(security_code)
            elif exchange_tag == 'HK':
                if re.match(r'\d\d\d\d.HK', security_code):
                # if security_code[:2] in ('09',  '39'):
                    type_tag = '股票'
                else:
                    raise NotImplementedError(security_code)
            elif exchange_tag == 'CFE':
                if security_code[:2] in ('IH', ):
                    type_tag = '期货'
                else:
                    raise NotImplementedError(security_code)
            else:
                raise NotImplementedError(security_code)
            return type_tag, exchange_tag

        sql_template = "SELECT * FROM {} WHERE 日期 = '{}';"

        flow_list = List.from_pd(DailyNormalTradeFlow, self.db.read_pd_query(
            DataBaseName.management, sql_template.format('当日普通交易流水', self.current_date)
        ))  # 普通账户交易流水
        for flow in flow_list:
            assert isinstance(flow, DailyNormalTradeFlow)
            if flow.product in ('浦睿1号', ):
                continue
            if flow.institution in ['中信美股', '中信港股', ]:
                continue
            flow_institution = flow.institution.replace('证券', '').replace('港股通', '')
            security_type, exchange_code = parse_security_code(flow.security_code)
            if security_type == '股票' and exchange_code == 'HK':
                security_type = '港股通'
            # assert flow.institution not in ['中信美股', '中信港股', ], str(flow)
            fee_sum = 0.0
            # 计算印花税
            if security_type == '股票':
                fee_sum += 0.00064 * abs(flow.trade_amount)
            elif security_type in ('ETF', '转债', '交债', ):
                pass
            elif security_type == '港股通':
                # fee_sum += 0.0001 * abs(flow.trade_amount)
                fee_sum += 0.001 * abs(flow.trade_amount)
            else:
                raise NotImplementedError('{}\n{}'.format(security_type, flow))
            # 计算过户费
            if security_type == '股票':
                fee_sum += 0.00002 * abs(flow.trade_amount)
            elif security_type in ('ETF', '转债', '交债', ):
                pass
            elif security_type == '港股通':
                fee_sum += max(0.00002 * abs(flow.trade_amount), 2)
            else:
                raise NotImplementedError('{}\n{}'.format(security_type, flow))
            # elif security_type in ('')
            try:
                fee_rate = info_board.find_security_trade_fee(
                    flow.product, '{}普通'.format(flow_institution), security_type, '佣金', date).fee_rate
            except AssertionError:
                fee_rate = 0.0003
            fee_sum += fee_rate * abs(flow.trade_amount)

            acc = self.account_deposition_list.find_value(
                product=flow.product, account_type='证券账户', institution=flow_institution)

            if flow.currency == acc.currency:
                exchange_rate = 1.0
            elif (flow.currency, acc.currency) == ('HKD', 'RMB'):
                if date < datetime.date.today():
                    exchange_rate = self.market_board.exchange_settle_rate('HKD', 'CNY', 'HKS', date)
                else:
                    exchange_rate = self.market_board.float_field('close', 'HKDCNYSET.HKS', date)
            else:
                raise NotImplementedError((flow.currency, acc.currency))
            if flow.trade_direction == TRADE_DIRECTION_BUY:
                acc.volume = acc.volume - (abs(flow.trade_amount) + fee_sum) * exchange_rate
            elif flow.trade_direction == TRADE_DIRECTION_SELL:
                acc.volume = acc.volume + (abs(flow.trade_amount) - fee_sum) * exchange_rate
            else:
                raise NotImplementedError(flow)

        account_list = List.from_pd(RawNormalAccount, self.db.read_pd_query(
                DataBaseName.management, sql_template.format('原始普通账户资金记录', date)))
        last_pos_list = List.from_pd(DailySecurityPosition, self.db.read_pd_query(DataBaseName.management, """
        SELECT * FROM `当日证券持仓` WHERE 日期 = (SELECT MAX(日期) FROM `当日证券持仓` WHERE 日期 < '{}');""".format(date)))
        last_pos_date_list = List(last_pos_list.collect_attr_set('date'))
        assert len(last_pos_date_list) <= 1, str(last_pos_date_list)
        for acc in self.account_deposition_list.find_value_where(account_type='证券账户', ):
            if len(last_pos_date_list) == 0:
                continue
            else:
                last_pos_date = last_pos_date_list[0]
                assert isinstance(last_pos_date, datetime.date)
            # 计算并扣除港股通组合费
            sub_pos_list, sub_total_market_value = List(), 0.0
            days_count = (date - last_pos_date) / datetime.timedelta(days=1)
            for pos in last_pos_list.find_value_where(product=acc.product):
                if acc.institution not in pos.institution:
                    continue
                if 'HK' in pos.security_code.upper() and 'SWAP' not in pos.institution_combined:
                    sub_pos_list.append(pos)
                    sub_total_market_value += pos.volume * self.market_board.float_field(
                        'close', pos.security_code, date)
            if len(sub_pos_list) > 0:
                self.log.debug(sub_pos_list)
                try:
                    fee_rate = info_board.find_security_trade_fee(
                        acc.product, '{}普通'.format(acc.institution), '每日计提', '港股通组合费', date).fee_rate
                except AssertionError:
                    fee_rate = 0.00008
                exchange_rate = self.market_board.float_field('close', 'HKDCNYSET.HKS', date)
                fee_amount = fee_rate * exchange_rate * sub_total_market_value * days_count / 360
                acc.volume = acc.volume - fee_amount

        # # 检查资金状况
        for acc in self.account_deposition_list.find_value_where(account_type='证券账户', ):
            check_list = account_list.find_value_where(product=acc.product, institution=acc.institution)
            if len(check_list) == 1:
                check_acc = check_list[0]
            elif len(check_list) == 0:
                continue
            else:
                raise NotImplementedError('{}\n{}'.format(acc, check_list))
            if is_different_float(acc.volume, check_acc.cash_amount, gap=0.5):
                acc.volume = check_acc.cash_amount

        flow_list = List.from_pd(DailyMarginTradeFlow, self.db.read_pd_query(
            DataBaseName.management, sql_template.format('当日两融交易流水', self.current_date)
        ))  # 两融账户交易流水
        for flow in flow_list:
            assert isinstance(flow, DailyMarginTradeFlow)
            self.log.debug(flow)
            flow_institution = flow.institution.replace('证券', '两融')
            # try:
            #     pos = self.security_position_list.find_value(
            #         product=flow.product, security_code=flow.security_code, volume_type=flow.trade_class,
            #         institution=flow.institution.replace('证券', '两融').replace('港股通', ''),
            #     )
            # except ValueError:
            #     pos = DailySecurityPosition(
            #         product=flow.product, date=self.current_date,
            #         institution=flow.institution.replace('证券', '两融').replace('港股通', ''),
            #         security_code=flow.security_code, security_name=flow.security_name,
            #         volume=0.0, volume_type=flow.trade_class,
            #     )
            #     self.security_position_list.append(pos)
            # if flow.trade_direction == TRADE_DIRECTION_BUY:
            #     pos.volume += abs(flow.trade_volume)
            # elif flow.trade_direction == TRADE_DIRECTION_SELL:
            #     pos.volume -= abs(flow.trade_volume)
            # else:
            #     raise NotImplementedError(flow)
            security_type, exchange_code = parse_security_code(flow.security_code)
            if security_type == '股票' and exchange_code == 'HK':
                security_type = '港股通'
            fee_sum = 0.0
            # 计算印花税
            if security_type == '股票':
                fee_sum += 0.00064 * abs(flow.trade_amount)
            elif security_type in ('ETF',):
                pass
            elif security_type == '港股通':
                fee_sum += 0.0001 * abs(flow.trade_amount)
            else:
                raise NotImplementedError('{}\n{}'.format(security_type, flow))
            # 计算过户费
            if security_type == '股票':
                fee_sum += 0.00002 * abs(flow.trade_amount)
            elif security_type in ('ETF',):
                pass
            elif security_type == '港股通':
                fee_sum += max(0.00002 * abs(flow.trade_amount), 2)
            else:
                raise NotImplementedError('{}\n{}'.format(security_type, flow))
            # elif security_type in ('')
            try:
                fee_rate = info_board.find_security_trade_fee(
                    flow.product, flow_institution, security_type, '佣金', date).fee_rate
            except AssertionError:
                fee_rate = 0.0003
            fee_sum += fee_rate * abs(flow.trade_amount)

            acc = self.account_deposition_list.find_value(
                product=flow.product, institution=flow_institution)

            if flow.currency == acc.currency:
                exchange_rate = 1.0
            elif (flow.currency, acc.currency) == ('HKD', 'RMB'):
                if date < datetime.date.today():
                    exchange_rate = self.market_board.exchange_settle_rate('HKD', 'CNY', 'HKS', date)
                else:
                    exchange_rate = self.market_board.float_field('close', 'HKDCNYSET.HKS', date)
            else:
                raise NotImplementedError((flow.currency, acc.currency))
            if flow.trade_class == '担保':
                if flow.trade_direction == TRADE_DIRECTION_BUY:
                    acc.volume = acc.volume - (abs(flow.trade_amount) + fee_sum) * exchange_rate
                elif flow.trade_direction == TRADE_DIRECTION_SELL:
                    acc.volume = acc.volume + (abs(flow.trade_amount) - fee_sum) * exchange_rate
                else:
                    raise NotImplementedError(flow)
            elif flow.trade_class == '融资':
                if flow.trade_direction == TRADE_DIRECTION_BUY:
                    acc.volume = acc.volume - (abs(flow.trade_amount) + fee_sum) * exchange_rate
                elif flow.trade_direction == TRADE_DIRECTION_SELL:
                    acc.volume = acc.volume + (abs(flow.trade_amount) - fee_sum) * exchange_rate
                else:
                    raise NotImplementedError(flow)
            else:
                raise NotImplementedError(flow)

        account_list = List.from_pd(RawNormalAccount, self.db.read_pd_query(
            DataBaseName.management, sql_template.format('原始两融账户资金记录', date)))
        # last_pos_list = List.from_pd(DailySecurityPosition, self.db.read_pd_query(DataBaseName.management, """
        # SELECT * FROM `当日证券持仓` WHERE 日期 = (SELECT MAX(日期) FROM `当日证券持仓` WHERE 日期 < '{}');""".format(date)))
        # last_pos_date_list = List(last_pos_list.collect_attr_set('date'))
        # assert len(last_pos_date_list) <= 1, str(last_pos_date_list)
        for acc in self.account_deposition_list.find_value_where(account_type='信用账户', ):
            # 计算并扣除港股通组合费
            if len(last_pos_date_list) == 0:
                continue
            else:
                last_pos_date = last_pos_date_list[0]
                assert isinstance(last_pos_date, datetime.date)
            days_count = (date - last_pos_date) / datetime.timedelta(days=1)
            sub_pos_list, sub_total_market_value = List(), 0.0
            for pos in last_pos_list.find_value_where(product=acc.product):
                if acc.institution not in pos.institution:
                    continue
                if 'HK' in pos.security_code.upper() and 'SWAP' not in pos.institution_combined:
                    self.log.debug(pos)
                    sub_pos_list.append(pos)
                    sub_total_market_value += pos.volume * self.market_board.float_field(
                        'close', pos.security_code, date)
            if len(sub_pos_list) > 0:
                try:
                    fee_rate = info_board.find_security_trade_fee(
                        acc.product, acc.institution, '每日计提', '港股通组合费', date).fee_rate
                except AssertionError:
                    fee_rate = 0.00008
                exchange_rate = self.market_board.float_field('close', 'HKDCNYSET.HKS', date)
                fee_amount = fee_rate * exchange_rate * sub_total_market_value * days_count / 360
                acc.volume = acc.volume - fee_amount
                self.log.debug('计提港股通组合费 {} \n {}'.format(fee_amount, acc))

        for acc in self.account_deposition_list.find_value_where(account_type='证券账户', ):
            # 检查资金状况
            check_list = account_list.find_value_where(product=acc.product, institution=acc.institution)
            if len(check_list) == 1:
                check_acc = check_list[0]
            elif len(check_list) == 0:
                # raise NotImplementedError()
                continue
            else:
                raise NotImplementedError('{}\n{}'.format(acc, check_list))
            if is_different_float(acc.volume, check_acc.cash_amount, gap=0.5):
                acc.volume = check_acc.cash_amount

        # TODO：检查和输入期货账户

        sql_template = "DELETE FROM {} WHERE 日期 = '{}';"
        self.log.info_running('储存当日账户余额')
        self.db.execute(DataBaseName.management, sql_template.format('当日账户余额', self.current_date))
        self.db.insert_data_list(DataBaseName.management, '当日账户余额', self.account_deposition_list)


if __name__ == '__main__':
    from jetend.structures import MySQL

    loader = TradeFlowLoader(
        MySQL('root', 'jm3389', '192.168.1.31', 3306),
        r'Z:\NutStore\久铭产品交割单\当日交易流水'
    )
    loader.load_simple_output_flow(datetime.date(2019, 9, 2))
    loader.log.info_running('前一日：{} 当前日：{} 后一日：{}'.format(
        loader.current_date - datetime.timedelta(days=1), loader.current_date,
        loader.current_date + datetime.timedelta(days=1)
    ))
    # loader.save_to_database()
