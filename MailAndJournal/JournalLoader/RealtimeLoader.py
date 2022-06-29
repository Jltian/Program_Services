# -*- encoding: UTF-8 -*-
import datetime
import os
import shutil
import time

from JournalLoader.Move import Move
from jetend import get_logger
from jetend.Constants import DataBaseName
from jetend.structures import List, MySQL
from jetend.DataCheck import *
from jetend.jmSheets import *

from Abstracts import AbstractInstitution
from institutions.AnXin import AnXin
from institutions.CaiTong import CaiTong
from institutions.ChangJiang import ChangJiang
from institutions.DeBang import DeBang
from institutions.DongFang import DongFang
from institutions.GuoJun import GuoJun
from institutions.GuoXin import GuoXin
from institutions.HaiTong import HaiTong
from institutions.HuaChuang import HuaChuang
from institutions.HuaJing import HuaJing
from institutions.HuaTai import HuaTai
from institutions.JianXin import JianXin
from institutions.ShenWan import ShenWan
from institutions.XingYe import XingYe
from institutions.YinHe import YinHe
from institutions.YongAn import YongAn
from institutions.ZhaoShang import ZhaoShang
from institutions.ZhongJin import ZhongJin
from institutions.ZhongJinCaiFu import ZhongJinCaiFu
from institutions.ZhongTai import ZhongTai
from institutions.ZhongXin import ZhongXin
from institutions.ZhongXinJianTou import ZhongXinJianTou
from institutions.ZhongYinGuoJi import ZhongYinGuoJi
from institutions.GuangFa import GuangFa
from Limits import *


class RealTimeLoader(object):
    normal_loader_map = {
        '安信普通账户': AnXin,
        '财通普通账户': CaiTong,
        '长江普通账户': ChangJiang,
        '国君普通账户': GuoJun,
        '国信普通账户': GuoXin,
        '海通普通账户': HaiTong,
        '华创普通账户': HuaChuang,
        '华菁普通账户': HuaJing,
        '华泰普通账户': HuaTai,
        '申万普通账户': ShenWan,
        '兴业普通账户': XingYe,
        '银河普通账户': YinHe,  # 读出来乱码
        '招商普通账户': ZhaoShang,
        '中金普通账户': ZhongJin,
        '中金财富普通账户': ZhongJinCaiFu,
        '中泰普通账户': ZhongTai, '中信普通账户': ZhongXin, '中信建投普通账户': ZhongXinJianTou,
        '东方普通账户': DongFang,
        '德邦普通账户': DeBang,
        '中银国际普通账户': ZhongYinGuoJi,
    }
    margin_loader_map = {
        '安信两融账户': AnXin,
        '长江两融账户': ChangJiang,
        '德邦两融账户': DeBang,
        '东方两融账户': DongFang,  # excel文件排版问题
        '华创两融账户': HuaChuang,
        '华泰两融账户': HuaTai,
        '国君两融账户': GuoJun,  # 读出来乱码
        '申万两融账户': ShenWan,  # 读出来乱码
        '银河两融账户': YinHe,  # 待读
        '招商两融账户': ZhaoShang,
        '中金两融账户': ZhongJin,
        '中金财富两融账户': ZhongJinCaiFu,
        '中信两融账户': ZhongXin,
        '中银国际两融账户': ZhongYinGuoJi,
    }
    swap_loader_map = {
        '华泰互换': HuaTai,
        '中信港股': ZhongXin, '中信美股': ZhongXin,
    }
    future_loader_map = {
        '安信期货账户': AnXin,
        '长江期货账户': ChangJiang,
        '海通期货账户': HaiTong,
        '国君期货账户': GuoJun,
        '建信期货账户': JianXin,
        '银河期货账户': YinHe,
        '永安期货账户': YongAn,
        '中信期货账户': ZhongXin,
    }
    option_loader_map = {
        '安信期权账户': AnXin,
        '东方期权账户': DongFang,
        '国君客户结算单': GuoJun,
        '国君期权账户': GuoJun,
        '海通期权账户': HaiTong,
        '华创期权账户': HuaChuang,
        '华泰期权账户': HuaTai,
        '申万期权账户': ShenWan,
        '兴业期权账户': XingYe,
        '招商期权账户': ZhaoShang,  # 招商期权excel文件乱码
        '中泰期权账户': ZhongTai,
        '中金期权账户': ZhongJin,
        '中金财富期权账户': ZhongJinCaiFu,
        '中信期权账户': ZhongXin,
        '中银国际期权账户': ZhongYinGuoJi,
       # '长江期权账户' : ChangJiang,
    }
    valuation_loader_map = {
        # 安信证券
        '专享1号': AnXin,
        # 国君证券
        '稳健1号': GuoJun, '专享5号': GuoJun,
        # 国信证券
        '稳健22号': GuoXin,
        # 华泰证券
        '久铭9号': HuaTai,
        # 招商证券
        '久铭50指数': ZhaoShang, '久铭300指数': ZhaoShang, '久铭500指数': ZhaoShang, '全球1号': ZhaoShang,
        '久铭1号': ZhaoShang, '久铭5号': ZhaoShang, '久铭10号': ZhaoShang,
        '创新稳健1号': ZhaoShang, '创新稳禄1号': ZhaoShang, '创新稳健2号': ZhaoShang, '创新稳健3号': ZhaoShang,
        '创新稳健5号': ZhaoShang, '创新稳健6号': ZhaoShang, '创新稳益1号': ZhaoShang,
        '价值1号': ZhaoShang, '全球丰收1号': ZhaoShang, '稳健23号': ZhaoShang, '稳健6号': ZhaoShang,
        '久盈2号': ZhaoShang, '收益2号': ZhaoShang, '成长1号': ZhaoShang,
        '专享6号': ZhaoShang, '专享7号': ZhaoShang, '专享8号': ZhaoShang, '专享9号': ZhaoShang, '专享10号': ZhaoShang,
        '专享11号': ZhaoShang,
        '静康1号': ZhaoShang, '静康稳健1号': ZhaoShang, '静康全球1号': ZhaoShang, '静康创新稳健1号': ZhaoShang,
        '静康创新稳禄1号': ZhaoShang, '静康稳健3号': ZhaoShang, '静久康铭稳健5号': ZhaoShang, '静康稳健2号': ZhaoShang,
        '稳禄1号': ZhaoShang,'静久康铭2号': GuangFa,
        # 中泰证券
        '久铭8号': ZhongTai,
        # 海通证券
        '久铭6号': HaiTong,
        # 兴业证券
        '久铭7号': XingYe, '专享21号': XingYe, '专享22号': XingYe, '专享23号': XingYe, '专享18号': XingYe, '专享19号': XingYe,
        '专享17号': XingYe,
        # 中信证券
        '信利1号': ZhongXin, '久铭信利': ZhongXin, '信利2号': ZhongXin, '专享15号': ZhongXin, '专享16号': ZhongXin,
         '专享2号': ZhongXin,'专享26号':ZhongXin,'专享28号':ZhongXin,'专享29号':ZhongXin,
        '创新稳禄2号': ZhongXin, '创新稳禄3号': ZhongXin, '创新稳禄12号': ZhongXin,
        '创新稳禄14号': ZhongXin, '专享20号': ZhongXin, '专享25号': ZhongXin, '专享27号': ZhongXin,
    }
    non_loader_map = {
        '多余',
        '国信互换',
        '东北普通账户',
        '恒泰普通账户',
    }

    def __init__(self, db: MySQL, path_view: str, path_collection: str, path_valuation_copy: str):
        self.log = get_logger(self.__class__.__name__)
        self.__path__ = None
        self.__filename__ = None
        self.__path_view__ = path_view
        self.__path_collection__ = path_collection
        self.__path_valuation_copy__ = path_valuation_copy
        self.current_date, self.last_date = None, None  # 当前日期
        self.db = db

        self.__critical_log__ = list()  # 储存需要严重注意的信息，在结束时日志输出

    def loading(self, folder: str, current_date: datetime.date, last_date: datetime.date):
        # assert os.path.exists(folder), '监测读取路径 {} 不存在'.format(folder)

        self.__path__ = folder
        assert current_date > last_date, '当前日期 {} 落后于前日日期 {}'.format(current_date, last_date)
        self.current_date, self.last_date = current_date, last_date  # 当前日期

        while True:

            self.log.debug('-' * 50)
            if not os.path.exists(self.__path__):
                self.log.debug('PATH DOES NOT EXIST: {}'.format(self.__path__))
                return 0
                # os.makedirs(self.__path__)
            institution_folder_list = ['托管估值表', '中信美股', '中信港股', ]
            institution_folder_list_beta = os.listdir(self.__path__)
            institution_folder_list_beta.sort()
            institution_folder_list.extend(institution_folder_list_beta)
            for sub_folder in institution_folder_list:
                if len(sub_folder) == 0:
                    continue
                if not os.path.isdir(os.path.join(self.__path__, sub_folder)):
                    continue

                folder_content = list()
                for file_name in os.listdir(os.path.join(self.__path__, sub_folder)):
                    self.__filename__ = file_name
                    if file_name.startswith('.') or file_name.startswith('~'):
                        continue
                    if os.path.isdir(os.path.join(self.__path__, sub_folder, file_name)):
                        continue
                    folder_content.append(file_name)

                if len(folder_content) == 0:
                    try:
                        os.removedirs(os.path.join(self.__path__, sub_folder))
                    except PermissionError:
                        pass
                    continue
                else:
                    pass

                self.log.debug_running(sub_folder, str(folder_content))
                if sub_folder in self.normal_loader_map:
                    method = self.normal_loader_map[sub_folder]
                    assert issubclass(method, AbstractInstitution), '未知数据类型 {}'.format(method)
                    assert sub_folder in method.folder_institution_map, '未知文件夹 {}'.format(sub_folder)
                    loaded_result, p_f_map = method.load_normal(
                        os.path.join(self.__path__, sub_folder), self.current_date
                    )
                    if len(loaded_result) == 0:  # @wave
                        continue
                    institution = method.folder_institution_map[sub_folder]  # sub_folder,诸如“中信建投普通账户”
                    if isinstance(loaded_result, dict):
                        for product, sub_loaded in loaded_result.items():
                            if sub_loaded is None:
                                self.move_to(product, self.current_date, sub_folder, p_f_map[product])
                                continue
                            assert isinstance(sub_loaded, dict), sub_loaded
                            assert product in PRODUCT_NAME_RANGE, product
                            flow_list = List.from_dict_list(RawNormalFlow, sub_loaded['flow'])
                            pos_list = List.from_dict_list(RawNormalPosition, sub_loaded['position'])
                            last_pos_list = List.from_pd(RawNormalPosition, self.__fetch_last_pos_list__(
                                '原始普通持仓记录', product, self.last_date, institution
                            ))
                            self.check_flow_pos_match(sub_folder, product, flow_list, pos_list, last_pos_list) #比对上一日的持仓记录和当前日的持仓记录（流水列表也传入了）
                            acc_obj = RawNormalAccount.from_dict(sub_loaded['account'])
                            last_acc_list = List.from_pd(RawNormalAccount, self.__fetch_last_acc__(
                                '原始普通账户资金记录', product, self.last_date, institution, sub_folder
                            ))
                            self.check_flow_acc_match(sub_folder, product, flow_list, acc_obj, last_acc_list)#比对上一日的账户资金记录和当前日的持仓记录（流水列表也传入了）

                            self.db.execute(DataBaseName.management, """DELETE FROM `原始普通持仓记录` WHERE 产品 = '{}' 
                            AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                            self.db.execute(DataBaseName.management, """DELETE FROM `原始普通流水记录` WHERE 产品 = '{}' 
                            AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                            self.db.execute(DataBaseName.management, """DELETE FROM `原始普通账户资金记录` WHERE 产品 = '{}' 
                            AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                            self.insert_to_db('原始普通持仓记录', pos_list)
                            self.insert_to_db('原始普通流水记录', flow_list)
                            self.db.execute(DataBaseName.management, acc_obj.form_insert_sql('原始普通账户资金记录'))
                            self.move_to(product, self.current_date, sub_folder, p_f_map[product])

                    elif isinstance(loaded_result, list):
                        for sub_loaded in loaded_result:
                            assert isinstance(sub_loaded, dict), sub_loaded
                            product = sub_loaded['Data']['product']
                            last_pos_list = List.from_pd(RawNormalPosition, self.__fetch_last_pos_list__(
                                '原始普通持仓记录', product, self.last_date, institution))
                            self.check_flow_pos_match(
                                sub_folder, product,
                                List.from_dict_list(RawNormalFlow, sub_loaded['Data']['flow']),
                                List.from_dict_list(RawNormalPosition, sub_loaded['Data']['position']), last_pos_list)
                            last_acc_list = List.from_pd(RawNormalAccount, self.__fetch_last_acc__(
                                '原始普通账户资金记录', product, self.last_date, institution, sub_folder))
                            self.check_flow_acc_match(
                                sub_folder, product,
                                List.from_dict_list(RawNormalFlow, sub_loaded['Data']['flow']),
                                RawNormalAccount.from_dict(sub_loaded['Data']['account']), last_acc_list)
                            # print(loaded_result)
                            # for sub_key in sub_loaded['Data']:
                            #   if sub_key in normal_table_map:
                            #    # self.db.execute(DataBaseName.management,
                            #    """DELETE FROM normal_table_map[sub_key] WHERE 产品 = '{}'
                            #    #                       AND 日期 = '{}' AND 机构 = '{}';""".format(
                            #    product, self.current_date, institution))
                            #     if sub_key == 'account':
                            #      # self.db.execute(DataBaseName.management, acc_obj.form_insert_sql(
                            #      normal_table_map[sub_key]))
                            #     else:
                            #      # self.insert_to_db(normal_table_map[sub_key],sub_loaded['Data'][sub_key]
                            #   elif sub_key == 'product':
                            #     continue
                            #   else:
                            #     raise NotImplementedError(sub_key)
                            # # self.move_to(product, self.current_date, sub_folder, p_f_map[product])

                elif sub_folder in self.margin_loader_map:
                    method = self.margin_loader_map[sub_folder]
                    assert issubclass(method, AbstractInstitution), '未知数据类型 {}'.format(method)
                    assert sub_folder in method.folder_institution_map, '未知文件夹 {}'.format(sub_folder)
                    loaded_result, p_f_map = method.load_margin(
                        os.path.join(self.__path__, sub_folder), self.current_date
                    )
                    assert isinstance(loaded_result, dict), loaded_result
                    institution = method.folder_institution_map[sub_folder]

                    for product, sub_loaded in loaded_result.items():
                        if sub_loaded is None:
                            self.move_to(product, self.current_date, sub_folder, p_f_map[product])
                            continue
                        assert isinstance(sub_loaded, dict), sub_loaded
                        assert product in PRODUCT_NAME_RANGE, product
                        flow_list = List.from_dict_list(RawMarginFlow, sub_loaded['flow'])
                        pos_list = List.from_dict_list(RawMarginPosition, sub_loaded['position'])
                        last_pos_list = List.from_pd(RawMarginPosition, self.__fetch_last_pos_list__(
                            '原始两融持仓记录', product, self.last_date, institution
                        ))
                        flag = self.check_flow_pos_match(sub_folder, product, flow_list, pos_list, last_pos_list)
                        if flag == 0:
                            print(self.__filename__)
                            # if p_f_map[product] == self.__filename__:
                            #     del p_f_map[product]
                            for item in p_f_map:  # 来一招偷梁换柱 @waves
                                if p_f_map[item] == self.__filename__:
                                    product = item
                            del p_f_map[product]
                            continue
                        acc_obj = RawMarginAccount.from_dict(sub_loaded['account'])
                        last_acc_list = List.from_pd(RawMarginAccount, self.__fetch_last_acc__(
                            '原始两融账户资金记录', product, self.last_date, institution, sub_folder
                        ))
                        lia_list = List.from_dict_list(RawMarginLiability, sub_loaded['liabilities'])
                        self.check_flow_acc_match(sub_folder, product, flow_list, acc_obj, last_acc_list)

                        self.db.execute(DataBaseName.management, """DELETE FROM `原始两融持仓记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.db.execute(DataBaseName.management, """DELETE FROM `原始两融流水记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.db.execute(DataBaseName.management, """DELETE FROM `原始两融负债记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.db.execute(DataBaseName.management, """DELETE FROM `原始两融账户资金记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.insert_to_db('原始两融持仓记录', pos_list)
                        self.insert_to_db('原始两融流水记录', flow_list)
                        self.insert_to_db('原始两融负债记录', lia_list)
                        self.db.execute(DataBaseName.management, acc_obj.form_insert_sql('原始两融账户资金记录'))
                        self.move_to(product, self.current_date, sub_folder, p_f_map[product])  # 这个方法是调用还是被跳过看情况（waves）

                elif sub_folder in self.option_loader_map:
                    # TODO: 非托管暂时没有期权交易，尽快完成
                    method = self.option_loader_map[sub_folder]
                    assert issubclass(method, AbstractInstitution), '未知数据类型 {}'.format(method)
                    assert sub_folder in method.folder_institution_map, '未知文件夹 {}'.format(sub_folder)
                    loaded_result, p_f_map = method.load_option(
                        os.path.join(self.__path__, sub_folder), self.current_date
                    )
                    assert isinstance(loaded_result, dict), loaded_result
                    institution = method.folder_institution_map[sub_folder]

                    for product, sub_loaded in loaded_result.items():
                        if sub_loaded is None:
                            self.move_to(product, self.current_date, sub_folder, p_f_map[product])
                            continue
                        assert isinstance(sub_loaded, dict), sub_loaded
                        assert product in PRODUCT_NAME_RANGE, product
                        flow_list = List.from_dict_list(RawOptionFlow, sub_loaded['flow'])
                        pos_list = List.from_dict_list(RawOptionPosition, sub_loaded['position'])
                        acc_obj = RawOptionAccount.from_dict(sub_loaded['account'])

                        self.db.execute(DataBaseName.management, """DELETE FROM `原始期权持仓记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.db.execute(DataBaseName.management, """DELETE FROM `原始期权流水记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.db.execute(DataBaseName.management, """DELETE FROM `原始期权账户资金记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.insert_to_db('原始期权持仓记录', pos_list)
                        self.insert_to_db('原始期权流水记录', flow_list)
                        self.db.execute(DataBaseName.management, acc_obj.form_insert_sql('原始期权账户资金记录'))
                        self.move_to(product, self.current_date, sub_folder, p_f_map[product])

                elif sub_folder in self.swap_loader_map:
                    method = self.swap_loader_map[sub_folder]
                    assert issubclass(method, AbstractInstitution), '未知数据类型 {}'.format(method)
                    assert sub_folder in method.folder_institution_map, '未知文件夹 {}'.format(sub_folder)
                    loaded_result, p_f_map = method.load_swap(
                        os.path.join(self.__path__, sub_folder), self.current_date
                    )
                    assert isinstance(loaded_result, dict), loaded_result
                    institution = method.folder_institution_map[sub_folder]
                    if '中信' in sub_folder:
                        for product, sub_loaded in loaded_result.items():
                            if not isinstance(sub_loaded, dict):
                                continue
                            assert product in PRODUCT_NAME_RANGE, product
                            acc_obj = RawSwapCiticAccount(**sub_loaded['balance_dict'])
                            acc_obj.update(sub_loaded['calculation_dict'])
                            pos_list = List.init_from(sub_loaded['underlying_list'])
                            pos_list = List.from_dict_list(RawSwapCiticPosition, pos_list)

                            self.db.execute(DataBaseName.management, """
                            DELETE FROM `原始中信收益互换持仓记录` WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}'
                            ;""".format(product, self.current_date, institution))
                            self.db.execute(DataBaseName.management, """
                            DELETE FROM `原始中信收益互换账户资金记录` WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}'
                            ;""".format(product, self.current_date, institution))
                            self.insert_to_db('原始中信收益互换持仓记录', pos_list)
                            self.db.execute(DataBaseName.management, acc_obj.form_insert_sql('原始中信收益互换账户资金记录'))
                            self.move_to(product, self.current_date, sub_folder, p_f_map[product])
                        if len(loaded_result) <= 1:
                            for product in p_f_map.keys():
                                self.move_to(product, self.current_date, sub_folder, p_f_map[product])
                        # if 'attachments' in p_f_map:
                        #     attachment_list = p_f_map
                        #     for attach_name, product in p_f_map
                    else:
                        for product, sub_loaded in loaded_result.items():
                            if not isinstance(sub_loaded, dict):
                                continue
                            assert product in PRODUCT_NAME_RANGE, product
                            acc_list = List.from_dict_list(RawSwapHtscAccount, sub_loaded['account_list'])
                            pos_list = List.from_dict_list(RawSwapHtscPosition, sub_loaded['underlying_list'])
                            self.db.execute(DataBaseName.management, """
                            DELETE FROM `原始华泰收益互换持仓记录` WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}'
                            ;""".format(product, self.current_date, institution))
                            self.db.execute(DataBaseName.management, """
                            DELETE FROM `原始华泰收益互换账户资金记录` WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}'
                            ;""".format(product, self.current_date, institution))
                            self.insert_to_db('原始华泰收益互换持仓记录', pos_list)
                            self.insert_to_db('原始华泰收益互换账户资金记录', acc_list)
                            self.move_to(product, self.current_date, sub_folder, p_f_map[product])

                elif sub_folder in self.future_loader_map:
                    method = self.future_loader_map[sub_folder]
                    assert issubclass(method, AbstractInstitution), '未知数据类型 {}'.format(method)
                    assert sub_folder in method.folder_institution_map, '未知文件夹 {}'.format(sub_folder)
                    loaded_result, p_f_map = method.load_future(
                        os.path.join(self.__path__, sub_folder), self.current_date
                    )
                    assert isinstance(loaded_result, dict), loaded_result
                    institution = method.folder_institution_map[sub_folder]

                    for product, sub_loaded in loaded_result.items():
                        if sub_loaded is None:
                            self.move_to(product, self.current_date, sub_folder, p_f_map[product])
                            continue
                        assert isinstance(sub_loaded, dict), sub_loaded
                        assert product in PRODUCT_NAME_RANGE, product
                        flow_list = List.from_dict_list(RawFutureFlow, sub_loaded['flow'])
                        pos_list = List.from_dict_list(RawFuturePosition, sub_loaded['position'])
                        last_pos_list = List.from_pd(RawFuturePosition, self.__fetch_last_pos_list__(
                            '原始期货持仓记录', product, self.last_date, institution
                        ))
                        # self.check_flow_pos_match(sub_folder, product, flow_list, pos_list, last_pos_list)
                        acc_obj = RawFutureAccount.from_dict(sub_loaded['account'])
                        # last_acc_list = List.from_pd(RawFutureAccount, self.__fetch_last_acc__(
                        #     '原始期货账户资金记录', product, self.last_date, institution, sub_folder
                        # ))
                        # self.check_flow_acc_match(sub_folder, product, flow_list, acc_obj, last_acc_list)
                        self.db.execute(DataBaseName.management, """DELETE FROM `原始期货持仓记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.db.execute(DataBaseName.management, """DELETE FROM `原始期货流水记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.db.execute(DataBaseName.management, """DELETE FROM `原始期货账户资金记录` WHERE 产品 = '{}' 
                        AND 日期 = '{}' AND 机构 = '{}';""".format(product, self.current_date, institution))
                        self.insert_to_db('原始期货持仓记录', pos_list)
                        self.insert_to_db('原始期货流水记录', flow_list)
                        self.db.execute(DataBaseName.management, acc_obj.form_insert_sql('原始期货账户资金记录'))
                        self.move_to(product, self.current_date, sub_folder, p_f_map[product])

                elif sub_folder == '托管估值表':
                    from jetend.Constants import PRODUCT_CODE_NAME_MAP
                    for file_name in os.listdir(os.path.join(self.__path__, sub_folder)):
                        if file_name.startswith('.') or file_name.startswith('~') or file_name.endswith('db'):
                            continue
                        if file_name in ('集合计划每日净值表.xls', '附4：行情提供函.docx',) or file_name.startswith('SGW875') or file_name.startswith('SS0569') or '国信托管' in file_name:
                            os.remove(os.path.join(self.__path__, sub_folder, file_name))
                            continue
                        if file_name.startswith('资产净值公告_') or file_name.startswith('【基金净值表现估算】') or file_name.startswith('模板'):
                            os.remove(os.path.join(self.__path__, sub_folder, file_name))
                            continue
                        if file_name.startswith('SW8251') and file_name.endswith('净值表.xls'):
                            os.remove(os.path.join(self.__path__, sub_folder, file_name))
                            continue
                        if '发送每日净值' in file_name:
                            os.remove(os.path.join(self.__path__, sub_folder, file_name))
                            continue
                        if '纳税申报表' in file_name or '.jpg' in file_name or '.pdf' in file_name:
                            os.remove(os.path.join(self.__path__, sub_folder, file_name))
                            continue
                        pro_id = None
                        for tag in PRODUCT_CODE_NAME_MAP.keys():
                            if tag in file_name:
                                pro_id = tag
                        if pro_id is None:
                            product = None
                            if '创新' in file_name:
                                for name in PRODUCT_NAME_RANGE:
                                    if '创新' in name and name in file_name:
                                        product = name
                            else:
                                for name in PRODUCT_NAME_RANGE:
                                    if name in file_name:
                                        product = name
                            if product is None:  # @wavezhou
                                # os.remove(os.path.join(self.__path__, sub_folder, file_name))
                                assert product is not None, file_name
                        else:
                            product = PRODUCT_CODE_NAME_MAP[pro_id]
                        if product in self.valuation_loader_map:
                            method = self.valuation_loader_map[product] #通过该产品名称匹配到对应的读取该产品托管估值表里数据的类
                        else:
                            # raise NotImplementedError(file_name)
                            pass
                        assert issubclass(method, AbstractInstitution), '{}'.format(method)
                        try:#就在这个方法里读取托管估值表中的键值对到一个obj对象中
                            loaded_result = method.load_valuation_table(os.path.join(folder, sub_folder, file_name))
                        except Exception as loaded_result:  # @waves
                            raise Exception(loaded_result)
                            # m = Move(os.path.join(folder, sub_folder, file_name))
                            # m.output_log(loaded_result)
                            # continue
                        # folder,subfolder,file_name
                        loaded_date = loaded_result['date']
                        if 'product' in loaded_result:
                            raise NotImplementedError(loaded_result)
                            # product = loaded_result['product']
                            # self.db.execute(DataBaseName.management, """DELETE FROM `原始托管估值表净值表`
                            #     WHERE 产品 = '{}' AND 日期 = '{}';""".format(product, loaded_date))
                            # self.db.execute(DataBaseName.management, RawTrusteeshipValuation(
                            #     **loaded_result).form_insert_sql('原始托管估值表净值表'))
                            # self.move_valuation_sheets_to(product, loaded_date, file_name)
                        else:
                            self.db.execute(DataBaseName.management, """DELETE FROM `原始托管估值表净值表` 
                            WHERE 产品 = '{}' AND 日期 = '{}';""".format(loaded_result['product_name'], loaded_date))
                            loaded_result['product'] = loaded_result['product_name']
                            self.db.execute(DataBaseName.management, RawTrusteeshipValuation(
                                **loaded_result).form_insert_sql('原始托管估值表净值表'))
                            self.db.execute(DataBaseName.management, """DELETE FROM `原始托管估值表简表` WHERE 
                                产品代码 = '{}' AND 日期 = '{}';""".format(loaded_result['product_code'], loaded_date))
                            self.db.execute(DataBaseName.management, RawTrusteeshipValuationSheet(
                                **loaded_result).form_insert_sql('原始托管估值表简表'))
                            # os.remove(os.path.join(self.__path__, '托管估值表', file_name))
                            # if 'detail_info_list' in loaded_result:
                            #     self.db.execute(DataBaseName.management, """DELETE FROM `原始托管估值表明细表` WHERE
                            #         产品代码 = '{}' AND 日期 = '{}';""".format(
                            #         loaded_result['product_code'], loaded_date))
                            #     self.insert_to_db('原始托管估值表明细表', List.from_dict_list(
                            #         RawTrusteeshipValuationDetail, loaded_result['detail_info_list']
                            #     ))
                            # raise NotImplementedError
                            self.move_valuation_sheets_to(loaded_result['product_name'], loaded_date, file_name)

                elif sub_folder == '浦睿1号':
                    for file_name in os.listdir(os.path.join(self.__path__, sub_folder)):
                        if file_name.startswith('.') or file_name.startswith('~'):
                            continue
                        else:
                            self.move_to('浦睿1号', self.current_date, '浦睿1号', file_name)
                elif sub_folder in self.non_loader_map:
                    continue
                elif sub_folder == '收益互换':
                    for file_name in os.listdir(os.path.join(self.__path__, sub_folder)):
                        if file_name.startswith('.') or file_name.startswith('~'):
                            continue
                        elif file_name.lower().endswith('xlsx') or file_name.lower().endswith('pdf'):
                            if 'USD' in file_name:
                                target_path = os.path.join(self.__path__, '中信美股')
                            elif 'HKD' in file_name:
                                target_path = os.path.join(self.__path__, '中信港股')
                            elif '南向互换' in file_name:
                                target_path = os.path.join(self.__path__, '华泰互换')
                            else:
                                raise NotImplementedError('{} {}'.format(sub_folder, file_name))
                            if not os.path.exists(target_path):
                                os.makedirs(target_path)
                            shutil.move(os.path.join(self.__path__, sub_folder, file_name), target_path)
                        elif file_name.lower().endswith('docx'):
                            if file_name.__contains__('补充交易确认书'):
                                os.remove(os.path.join(self.__path__, sub_folder, file_name))
                                continue
                            else:
                                raise NotImplementedError(file_name)
                        else:
                            raise NotImplementedError(file_name)
                elif sub_folder == '华泰互换':
                    continue
                elif sub_folder == '中金互换':
                    continue
                elif sub_folder == '清算数据':
                    for file_name in os.listdir(os.path.join(self.__path__, sub_folder)):
                        if file_name.startswith('.') or file_name.startswith('~'):
                            continue
                        elif file_name.lower().endswith('rar'):
                            os.remove(os.path.join(self.__path__, sub_folder, file_name))
                        elif file_name.lower().endswith('zip'):
                            os.remove(os.path.join(self.__path__, sub_folder, file_name))
                        else:
                            raise NotImplementedError(file_name)
                elif sub_folder == '手动分类':
                    wait_to_dellist = ['31681742久铭专享18号20210923.RAR', '31681745久铭专享21号20210923.RAR',
                                       '31681747久铭专享19号20210923.RAR',
                                       '31681750久铭专享22号20210923.RAR', '31681752久铭专享10号20210923.RAR',
                                       '31681753久铭专享23号20210923.RAR',
                                       '31681756久铭1号20210923.RAR', '31681758久铭专享7号20210923.RAR',
                                       '131681742rzrq20210923.rar', '131681742久铭专享18号-信用20210923.RAR',
                                       '131681745rzrq20210923.rar', '131681745久铭专享21号-信用20210923.RAR']
                    for f in os.listdir(os.path.join(self.__path__, sub_folder)):
                        if f in wait_to_dellist:
                            os.remove(os.path.join(self.__path__, sub_folder, f))
                elif sub_folder == '未知数据':
                    wait_to_dellist = ['久铭10号2920273120210923.zip', '久铭10号信用92920273120210923.zip']
                    for f in os.listdir(os.path.join(self.__path__, sub_folder)):
                        if f in wait_to_dellist:
                            os.remove(os.path.join(self.__path__, sub_folder, f))
                else:
                    import Move
                    Move.Move(os.path.join(folder, sub_folder))
                    # raise NotImplementedError(sub_folder)
                    self.log.debug("移动未读成功的目录{}到手工处理DebugOut目录".format(sub_folder))

            time.sleep(2)

    def move_to(self, product: str, date: datetime.date, folder_institution: str, file_name: str):
        source_file = os.path.join(self.__path__, folder_institution, file_name)

        folder_view = os.path.join(
            self.__path_view__, '{}年'.format(date.year),
            '久铭产品交割单{}'.format(date.strftime('%Y%m%d')), folder_institution, )
        if not os.path.exists(folder_view):
            os.makedirs(folder_view, exist_ok=True)
        target_path = os.path.join(folder_view, file_name)
        if os.path.exists(target_path):
            os.remove(target_path)
        self.log.debug('copy to {}'.format(target_path))
        shutil.copy(source_file, folder_view)

        folder_collection = os.path.join(self.__path_collection__, product, folder_institution, date.strftime('%Y%m%d'))
        os.makedirs(folder_collection, exist_ok=True)
        target_path = os.path.join(folder_collection, file_name)
        if os.path.exists(target_path):
            os.remove(target_path)
        self.log.debug('copy to {}'.format(target_path))
        shutil.copy(source_file, folder_collection)

        os.remove(source_file)

    def move_valuation_sheets_to(self, product: str, date: datetime.date, file_name: str, ):
        source_file = os.path.join(self.__path__, '托管估值表', file_name)

        folder_view = os.path.join(
            self.__path_view__, '{}年'.format(date.year),
            '久铭产品交割单{}'.format(date.strftime('%Y%m%d')), '托管估值表', )
        try:
            os.makedirs(folder_view, exist_ok=True)
        except FileExistsError:
            pass
        target_path = os.path.join(folder_view, file_name)
        self.log.debug('copy to {}'.format(target_path))
        if os.path.exists(target_path):
            os.remove(target_path)
        shutil.copy(source_file, folder_view)

        # os.makedirs(folder_collection, exist_ok=True)
        # target_path = os.path.join(folder_collection, file_name)
        # self.log.debug('copy to {}'.format(target_path))
        # if os.path.exists(target_path):
        #     pass
        # else:
        #     shutil.copy(source_file, folder_collection)

        folder_collection = os.path.join(self.__path_collection__, product, '托管估值表')
        # folder_collection = os.path.join(ValuationSheetCollectionPath, product)
        os.makedirs(folder_collection, exist_ok=True)
        target_path = os.path.join(folder_collection, file_name)
        self.log.debug('copy to {}'.format(target_path))
        if os.path.exists(target_path):
            os.remove(target_path)
        shutil.copy(source_file, folder_collection)

        if '静康' in product or '静久康铭' in product:
            folder_collection = os.path.join(self.__path_valuation_copy__, '托管产品估值表 静久', product)
        else:
            folder_collection = os.path.join(self.__path_valuation_copy__, '托管产品估值表 久铭', product)
        target_path = os.path.join(folder_collection, file_name)
        self.log.debug('copy to {}'.format(target_path))
        if os.path.exists(target_path):
            os.remove(target_path)
        shutil.copy(source_file, folder_collection)

        os.remove(source_file)
        # raise NotImplementedError

    def __fetch_last_acc__(self, table_name: str, product: str, date: datetime.date, institution: str,
                           account_type: str):
        return self.db.read_pd_query(
            DataBaseName.management,
            """
            SELECT * FROM `{}` 
            WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}' AND 账户类型 = '{}'
            ;""".format(table_name, product, date, institution, account_type)
        )

    def __fetch_last_pos_list__(self, table_name: str, product: str, date: datetime.date, institution: str):
        return self.db.read_pd_query(
            DataBaseName.management,
            """
            SELECT * FROM `{}` 
            WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}'
            ;""".format(table_name, product, date, institution)
        )

    def check_flow_pos_match(self, folder: str, product: str, flow_list: List, pos_list: List, last_pos_list: List):
        """验证前日持仓模拟流水操作后与今日持仓比较"""
        security_code_set = set()
        security_code_set.update(pos_list.collect_attr_set('security_code'))
        security_code_set.update(last_pos_list.collect_attr_set('security_code'))

        if '' in security_code_set:
            security_code_set.remove('')
        if None in security_code_set:
            security_code_set.remove(None)

        for security_code in security_code_set:
            if security_code is None or security_code == '':
                continue

            this_pos = pos_list.find_value_where(security_code=security_code)
            if len(this_pos) == 1:
                this_pos = this_pos[0]
                if isinstance(this_pos, RawNormalPosition):
                    end_position = float_check(this_pos.hold_volume)
                elif isinstance(this_pos, RawFuturePosition):
                    assert abs(float_check(this_pos.short_position)) < 0.01, this_pos
                    end_position = float_check(this_pos.long_position)
                else:
                    raise NotImplementedError(this_pos)
            elif len(this_pos) == 0:
                this_pos = None
                end_position = 0.0
            else:
                print(folder, product)
                print(this_pos)
                raise RuntimeError('存在重复持仓信息')

            last_pos = last_pos_list.find_value_where(security_code=security_code)
            if len(last_pos) == 1:
                last_pos = last_pos[0]
                if isinstance(last_pos, RawNormalPosition):
                    calculate_position = float_check(last_pos.hold_volume)
                elif isinstance(last_pos, RawFuturePosition):
                    calculate_position = float_check(last_pos.long_position)
                else:
                    raise NotImplementedError(last_pos)
            elif len(last_pos) == 0:
                if this_pos is None:
                    raise RuntimeError('出现不应该出现的证券代码：{}'.format(security_code))
                else:
                    last_pos = None
                    calculate_position = 0.0
            else:
                print(folder, product)
                print(last_pos)
                raise RuntimeError('存在重复持仓信息')

            for flow in flow_list.find_value_where(security_code=security_code):
                if isinstance(flow, RawNormalFlow):
                    if '买入' in flow.trade_class or flow.trade_class in NORMAL_DIRECTION_BUY_TRADE_CLASS:
                        calculate_position += abs(float_check(flow.trade_volume))
                    elif '卖出' in flow.trade_class \
                            or '托管转出' in flow.trade_class \
                            or flow.trade_class in NORMAL_DIRECTION_SELL_TRADE_CLASS:
                        calculate_position -= abs(float(flow.trade_volume))
                    elif '过户' in flow.trade_class or '新股' in flow.trade_class or '申购' in flow.trade_class:
                        calculate_position += flow.trade_volume
                    elif flow.trade_class in NORMAL_DIRECTION_NONE_TRADE_CLASS:
                        pass
                    else:
                        print("==========")  # waves
                        m = Move(os.path.join(self.__path__, folder, self.__filename__))
                        m.output_log("{}NotImplementedError : 未实现的的交易类型\n===================".format(flow))
                        return 0
                        # raise NotImplementedError(flow)
                elif isinstance(flow, RawFutureFlow):
                    if '买' in flow.trade_class or flow.trade_class in FUTURE_DIRECTION_BUY_TRADE_CLASS:
                        calculate_position += abs(flow.trade_volume)
                    elif '卖' in flow.trade_class or flow.trade_class in FUTURE_DIRECTION_SELL_TRADE_CLASS:
                        calculate_position -= abs(flow.trade_volume)
                    else:
                        raise NotImplementedError(flow)
                else:
                    raise NotImplementedError(flow)

            if is_different_float(calculate_position, end_position):
                info = "\n\treaded: {},\n\tcalculated: {},\n\tlast: {},\n\tflow: {}".format(
                    this_pos, calculate_position, last_pos, flow_list.find_value_where(security_code=security_code)
                )
                if last_pos is None:
                    self.log.warning('读取账户持仓与流水计算持仓差距过大，可能源于没有前日持仓历史 {}'.format(info))
                else:
                    self.log.warning('读取账户持仓与流水计算持仓差距超过0.1%  {}'.format(security_code) + info)

    def check_flow_acc_match(self, folder: str, product: str, flow_list: List, acc_obj, last_acc_list: List):
        """验证前日资金经过流水操作后与今日资金比较"""
        if len(last_acc_list) == 1:
            last_acc = last_acc_list[0]
            if isinstance(last_acc, (RawNormalAccount, RawMarginAccount)):
                calculation_cash = last_acc.cash_amount
            else:
                raise NotImplementedError(last_acc)
        elif len(last_acc_list) == 0:
            last_acc = None
            calculation_cash = 0.0
        else:
            print(product, folder)
            raise RuntimeError('出现重复账户信息')

        if isinstance(acc_obj, (RawNormalAccount, RawMarginAccount, RawFutureAccount)):
            end_cash = float_check(acc_obj.cash_amount)
        else:
            raise NotImplementedError(acc_obj)
        assert is_valid_float(end_cash), str(acc_obj)

        for flow in flow_list:
            if isinstance(flow, (RawNormalFlow, RawMarginFlow)):
                calculation_cash += float_check(flow.cash_move)
            else:
                raise NotImplementedError(flow)

        info = "\n\treaded: {},\n\tcalculated: {},\n\tlast: {}, \n\tflow: {}".format(
            acc_obj, calculation_cash, last_acc, flow_list)
        if calculation_cash < - 0.5:
            self.log.error('计算账户现金为负 {}'.format(info))
        elif is_different_float(calculation_cash, end_cash, gap=max(0.001 * end_cash, 1)):
            self.log.error('读取账户现金与流水计算差距超过0.1% -> {} {}'.format(calculation_cash - end_cash, info))
        else:
            pass

    def insert_to_db(self, table_name: str, data_list: List):
        if len(data_list) > 0:
            # self.to_csv(table_name, data_list)
            for obj in data_list:
                sql = getattr(obj, 'form_insert_sql').__call__(table_name)
                try:
                    self.db.execute(DataBaseName.management, sql)
                except BaseException as i_e:
                    print(obj)
                    raise i_e
        # self.log.info_running('储存当日', table_name)

    def clear_duplicated_in_db(self, table_name: str):
        # pass
        self.db.execute(
            DataBaseName.management,
            "DELETE FROM {} WHERE 日期 = '{}'".format(table_name, self.current_date),
        )

    def to_csv(self, table_name: str, data: List):
        if len(data) > 0:
            root_path = os.path.abspath(os.path.dirname(__file__))
            data.to_pd().to_csv(os.path.join(root_path, 'temp', '{}_{}.csv').format(
                self.current_date.strftime('%Y-%m-%d'), table_name,
            ), encoding='gb18030')


if __name__ == '__main__':
    # base_folder = r'C:\NutStore\久铭产品交割单\2019年'
    base_folder = r'C:\Users\Administrator.SC-201606081350\Downloads'
    current_day, last_day = datetime.date(2019, 8, 1), datetime.date(2019, 7, 31)

    loader = RealTimeLoader(
        db=MySQL('root', 'jm3389', '192.168.1.31', 3306),
        path_view=r'Z:\NutStore\久铭产品交割单',
        path_collection=r'Z:\NutStore\实习生\对账单记录备份'
    )
    # ---- ---- #

    loader.loading(
        os.path.join(base_folder, '久铭产品交割单{}'.format(current_day.strftime('%Y%m%d'))),
        current_day, last_day,
    )
