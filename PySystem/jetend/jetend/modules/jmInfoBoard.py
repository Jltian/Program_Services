# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime

from jetend.Constants import DataBaseName
from jetend.structures import List
from jetend.jmSheets import *


class jmInfoBoard(object):

    def __init__(self, db):
        from jetend.structures import MySQL
        if isinstance(db, MySQL):
            self.db = db
        else:
            raise NotImplementedError(type(db))

        self.__product_info_list__ = None
        self.__product_name_range_01__ = (
            '久铭2号', '久铭3号', '久铭5号', '双盈1号', '稳利2号', '收益1号', '全球1号', '上证50指数', '沪深300指数',
            '中证500指数', '稳健2号', '稳健3号', '稳健5号', '稳健8号', '稳健9号', '稳健10号', '稳健11号', '稳健12号',
            '稳健15号', '稳健16号', '稳健17号', '稳健18号', '稳健19号', '稳健21号', '稳健22号', '稳健31号', '稳健32号',
            '稳健33号', '久铭1号', '久铭6号', '久铭7号', '久铭8号', '久铭9号', '久铭10', '稳健1号', '收益2号',
            '稳健23号', '稳健6号', '稳健7号', '久盈2号', '久铭50指数', '久铭300指数', '久铭500指数',
            '创新稳健1号', '创新稳健2号', '创新稳健5号', '创新稳健6号',
            '创新稳益1号', '全球丰收1号',
        )
        self.__product_trade_fee_list__ = None
        self.__product_account_interest_rate_list__ = None
        self.__product_account_liability_interest_rate_list__ = None
        self.__management_fee_return_rate__ = List()
        self.__security_info_list__ = None

        self.management_fee_dict = dict()
        self.__exchange_rate_list__ = List()

    # ------------------------ [property] ------------------------
    @property
    def product_info_list(self):
        if self.__product_info_list__ is None:
            self.__product_info_list__ = List.from_pd(ProductInfo, self.db.read_pd_query(
                DataBaseName.transfer_agent_new, """SELECT * FROM 最新产品要素表;"""
            )).change_attr(table={None: '产品要素表'})
            self.__product_info_list__.extend(List.from_pd(ProductInfo, self.db.read_pd_query(
                DataBaseName.jingjiu_ta, """SELECT * FROM 最新产品要素表;"""
            )).change_attr(table={None: '静久产品要素表'}))
            self.__product_info_list__.extend(List.from_pd(ProductInfo, self.db.read_pd_query(
                DataBaseName.management, """SELECT * FROM 补充产品要素表;"""
            )).change_attr(table={None: '补充产品要素表'}))
        assert isinstance(self.__product_info_list__, List)
        return self.__product_info_list__

    @property
    def security_info_list(self):
        if self.__security_info_list__ is None:
            self.__security_info_list__ = List.from_pd(SecurityInfo, self.db.read_pd_query(
                DataBaseName.management, """SELECT * FROM 证券代码名称规整表;"""
            ))
        assert isinstance(self.__security_info_list__, List)
        return self.__security_info_list__

    @property
    def product_trade_fee_list(self):
        if self.__product_trade_fee_list__ is None:
            self.__product_trade_fee_list__ = List.from_pd(TradeFeeRate, self.db.read_pd_query(
                DataBaseName.management, """SELECT * FROM 产品证券交易费率表;"""
            ))
        assert isinstance(self.__product_trade_fee_list__, List)
        return self.__product_trade_fee_list__

    @property
    def product_account_interest_rate_list(self):
        if self.__product_account_interest_rate_list__ is None:
            self.__product_account_interest_rate_list__ = List.from_pd(AccountInterestRate, self.db.read_pd_query(
                DataBaseName.management, """SELECT * FROM 产品账户资金利率表;"""
            ))
        assert isinstance(self.__product_account_interest_rate_list__, List)
        return self.__product_account_interest_rate_list__

    # ------------------------ [methods - finding information] ------------------------
    def find_product_mandatory(self, product: str):
        """获取产品托管人信息 -> str"""
        obj = self.product_info_list.find_value(name=product)
        assert isinstance(obj, ProductInfo)
        return obj.mandatory

    def find_product_info_by_code(self, code: str):
        try:
            obj = self.product_info_list.find_value(code=code)
        except ValueError:
            raise RuntimeError('未知产品代码：{}'.format(code))
        assert isinstance(obj, ProductInfo)
        return obj

    def find_net_value_by_code(self, code: str, date: datetime.date):
        from jetend.DataCheck import is_valid_float
        product_name = self.find_product_info_by_code(code).name
        if '静康' not in product_name and '静久康铭' not in product_name:
            net_value = self.db.read_pd_query(
                DataBaseName.transfer_agent_new, """
                SELECT `{}` as 单位净值 FROM `净值表` WHERE `日期` = (
                    SELECT MAX(日期) FROM `净值表` WHERE 日期 <= '{}'
                    );""".format(product_name, date)
            ).loc[0, '单位净值']
            assert is_valid_float(net_value), '{} {}'.format(product_name, date)
        else:
            net_value = self.db.read_pd_query(
                DataBaseName.jingjiu_ta, """
                SELECT `{}` as 单位净值 FROM `静久净值表` WHERE `日期` = (
                    SELECT MAX(日期) FROM `静久净值表` WHERE 日期 <= '{}'
                    );""".format(product_name, date)
            ).loc[0, '单位净值']
            assert is_valid_float(net_value), '{} {}'.format(product_name, date)
        return net_value

    def find_product_net_value_by_name(self, name: str, date: datetime.date, ta_read: bool = True):
        """用于测试，并非获取正式单位净值"""
        from jetend.DataCheck import is_valid_float
        if name in ('长安久铭浦睿1号', ):
            net_value = self.db.read_pd_query(
                DataBaseName.management,
                """SELECT `单位净值` FROM `补充净值表` WHERE `产品` = '{}' AND `日期` = '{}' AND `币种` = '{}';""".format(
                    name, date, 'RMB'
                )).loc[0, '单位净值']
            net_value = round(net_value, 3)
            assert is_valid_float(net_value), '{} {}'.format(name, date)
        elif name in self.__product_name_range_01__:
            try:
                if ta_read is True:
                    net_value = self.db.read_pd_query(
                        DataBaseName.transfer_agent_new,
                        """SELECT `{}` as 单位净值 FROM `净值表` WHERE `日期` = '{}';""".format(name, date)
                    ).loc[0, '单位净值']
                    assert is_valid_float(net_value), '{} {}'.format(name, date)
                else:
                    raise KeyError
            except (KeyError, AssertionError):
                if self.check_mandatory(name) is True:
                    value_list = List.from_pd(RawTrusteeshipValuation, self.db.read_pd_query(
                        DataBaseName.management,
                        """
                        SELECT * FROM `原始托管估值表净值表` 
                        WHERE `日期` = (SELECT MAX(日期) FROM `原始托管估值表净值表` WHERE `日期` <= '{}')
                        ;""".format(date)
                    ))
                    try:
                        net_value = float(value_list.find_value(product=name).net_value)
                    except ValueError:
                        raise RuntimeError('日期 {} 缺少 {} 估值表信息'.format(value_list.collect_attr_set('date'), name))
                else:
                    net_value = self.db.read_pd_query(
                        DataBaseName.management,
                        """SELECT 单位净值 FROM `会计凭证估值净值表` WHERE 日期 = '{}' AND 产品 = '{}';""".format(
                            date, name, )).loc[0, '单位净值']
                assert is_valid_float(net_value), '单位净值数据出错 {} {}'.format(name, date)
        else:
            raise NotImplementedError(name)
        return net_value

    def add_product_net_value(self, product: str, date: datetime.date, net_value: float, currency: str):
        from jetend.DataCheck import is_valid_float
        assert is_valid_float(net_value), '输入净值需要是有意义的数字 {}'.format(net_value)
        try:
            stored_nav = self.db.read_pd_query(
                DataBaseName.management,
                """SELECT `单位净值` FROM `补充净值表` WHERE `产品` = '{}' AND `日期` = '{}' AND `币种` = '{}';""".format(
                    product, date, currency
                )).loc[0, '单位净值']
            assert round(stored_nav, 3) == round(net_value, 3), '试图输入一个与已储存净值不同的数字 {} {}'.format(
                stored_nav, net_value)
            pass
        except KeyError:
            self.db.execute(
                DataBaseName.management,
                """INSERT INTO 补充净值表(产品, 日期, 单位净值, 币种) VALUES ('{}', '{}', '{}', '{}');""".format(
                    product, date, round(net_value, 6), currency
                ))

    def find_product_code_by_name(self, name: str):
        if '私募' in name or '证券' in name:
            search_list = self.product_info_list.find_value_where(full_name=name)
        else:
            search_list = self.product_info_list.find_value_where(name=name)
        if len(search_list) == 1:
            return search_list[0].code
        else:
            raise RuntimeError('{}\n{}'.format(name, search_list))

    def find_product_name_by_name(self, name: str):
        if '创新' in name:
            for obj in self.product_info_list:
                assert isinstance(obj, ProductInfo)
                if obj.name in name and '创新' in obj.name:
                    return obj.name
        elif '私募' in name or '资产' in name or '证券' in name:
            for obj in self.product_info_list:
                assert isinstance(obj, ProductInfo)
                if obj.full_name in name:
                    return obj.name
        elif '专享' in name:
            for obj in self.product_info_list:
                assert isinstance(obj, ProductInfo)
                if name in obj.name:
                    return obj.name
        else:
            try:
                obj = self.product_info_list.find_value(name=name)
            except ValueError:
                raise RuntimeError('未知产品名称：{}'.format(name))
            assert isinstance(obj, ProductInfo)
            return obj.name

    def __find_product_fee_rate__(self, product: str, date: datetime.date, fee_type: str):
        p_info = self.product_info_list.find_value(name=product)
        if p_info.table == '产品要素表':
            try:
                mfr = self.db.read_pd_query(
                    DataBaseName.transfer_agent_new,
                    """SELECT * FROM `产品要素修改表` 
                        WHERE `产品简称` = '{}' AND `修改类型` = '{}' AND `日期` <= '{}' 
                        ORDER BY 日期 DESC, 序号 DESC;
                        ;""".format(product, fee_type, date.strftime('%Y-%m-%d'))).loc[0, '修改信息']
            except KeyError:
                mfr = None
        elif p_info.table == '补充产品要素表':
            try:
                mfr = self.db.read_pd_query(
                    DataBaseName.management,
                    """SELECT * FROM `补充产品要素修改表` 
                        WHERE `产品简称` = '{}' AND `修改类型` = '{}' AND `日期` <= '{}' 
                        ORDER BY 日期 DESC, 序号 DESC;
                        ;""".format(product, fee_type, date.strftime('%Y-%m-%d'))).loc[0, '修改信息']
            except KeyError:
                mfr = None
        else:
            raise RuntimeError('未知错误 {} {}'.format(product, date))
        if mfr is None:
            raise ValueError('信息缺失 {} {} {}'.format(product, date, fee_type))
        else:
            mfr = float(mfr)
        assert isinstance(mfr, float), '{} {} {} {} {}'.format(mfr, type(mfr), product, date, fee_type)
        return mfr

    def find_product_mandate_fee_rate(self, product: str, date: datetime.date):
        """返回产品托管费率（注意仅适用于托管产品） -> float"""
        return self.__find_product_fee_rate__(product, date, '托管费率')

    def find_product_mandate_service_fee_rate(self, product: str, date: datetime.date):
        """返回产品外包服务费率（注意仅适用于托管产品） -> float"""
        return self.__find_product_fee_rate__(product, date, '外包服务费率')

    def find_product_sell_service_fee_rate(self, product: str, date: datetime.date):
        """返回产品销售服务费率（注意仅适用于托管产品） -> float"""
        return self.__find_product_fee_rate__(product, date, '销售服务费率')

    def find_product_management_fee_rate(self, product: str, date: datetime.date):
        fee_rate_dict = self.management_fee_dict.get(date, dict())
        try:
            mfr = fee_rate_dict[product]
        except KeyError:
            p_info = self.product_info_list.find_value(name=product)
            mfr = self.db.read_dict_query(
                DataBaseName.transfer_agent,
                """
                SELECT `fee_rate` as fee_rate FROM PRODUCT_FEE_RATE 
                WHERE `product_name` = '{}' AND fee_type = '管理费率' AND date = (
                    SELECT max(date) FROM PRODUCT_FEE_RATE 
                    WHERE `date` <= '{}' AND `fee_type` = '管理费率' AND `product_name` = '{}'
                );""".format(product, date, product))[0]['fee_rate']
            # if p_info.table == '产品要素表':
            #     try:
            #         mfr = self.db.read_pd_query(
            #             DataBaseName.transfer_agent_new,
            #             """SELECT * FROM `产品要素修改表`
            #                 WHERE `产品简称` = '{}' AND `修改类型` = '管理费率' AND `日期` <= '{}'
            #                 ORDER BY 日期 DESC, 序号 DESC;
            #                 ;""".format(product, date.strftime('%Y-%m-%d'))).loc[0, '修改信息']
            #     except KeyError:
            #         mfr = None
            # elif p_info.table == '补充产品要素表':
            #     try:
            #         mfr = self.db.read_pd_query(
            #             DataBaseName.management,
            #             """SELECT * FROM `补充产品要素修改表`
            #                 WHERE `产品简称` = '{}' AND `修改类型` = '管理费率' AND `日期` <= '{}'
            #                 ORDER BY 日期 DESC, 序号 DESC;
            #                 ;""".format(product, date.strftime('%Y-%m-%d'))).loc[0, '修改信息']
            #     except KeyError:
            #         mfr = None
            # else:
            #     raise RuntimeError('未知错误 {} {}'.format(product, date))
            if mfr is None:
                mfr = p_info.management_fee
            else:
                mfr = float(mfr)
            fee_rate_dict[product] = mfr
            self.management_fee_dict[date] = fee_rate_dict
        assert isinstance(mfr, float), '{} {} {} {}'.format(mfr, type(mfr), product, date)
        return mfr

    def find_product_management_return_rate(self, investor: str, invested: str, date: datetime.date):
        obj_list = self.__management_fee_return_rate__.find_value_where(
            investor_product=investor, fund_product=invested
        )
        if len(obj_list) == 1:
            obj = obj_list[0]
            assert isinstance(obj, ManagementFeeReturnRate), str(obj)
            assert obj.update_date <= date <= obj.limit_date, str(obj)
            return obj.rate
        elif len(obj_list) == 0:
            obj_list = List.from_pd(ManagementFeeReturnRate, self.db.read_pd_query(
                DataBaseName.management,
                """
                SELECT * FROM 产品管理费返还费率表 
                WHERE 产品 = '{}' and 被投产品 = '{}' and 更新日期 <= '{}'
                ;""".format(investor, invested, date)
            ))
            assert len(obj_list.collect_attr_set('update_date')) > 0, """产品管理费返还费率表缺少信息 
            invester: {} invested: {} {}""".format(investor, invested, date)
            obj = obj_list.find_value(update_date=max(obj_list.collect_attr_set('update_date')))
            assert isinstance(obj, ManagementFeeReturnRate)
            obj.limit_date = date
            self.__management_fee_return_rate__.append(obj)
            return self.find_product_management_return_rate(investor, invested, date)
        else:
            raise RuntimeError('{} {} {} \n {}'.format(investor, invested, date, obj_list))

    def find_security_full_code_by_code(self, code: str):
        try:
            if '.' in code:
                raise ValueError('code {} seems to be a full code.'.format(code))
            else:
                obj = self.security_info_list.find_value(code=code)
        except ValueError:
            raise RuntimeError('Found no code like {}'.format(code))
        assert isinstance(obj, SecurityInfo)
        return obj.name
    
    def find_security_name_by_code(self, code: str):
        try:
            if '.' in code:
                obj = self.security_info_list.find_value(full_code=code.upper())
            else:
                obj = self.security_info_list.find_value(code=code)
        except ValueError:
            raise RuntimeError('Found no code like {}'.format(code))
        assert isinstance(obj, SecurityInfo)
        return obj.name
    
    def find_security_type_by_code(self, code: str):
        try:
            if '.' in code:
                obj = self.security_info_list.find_value(full_code=code.upper())
            else:
                obj = self.security_info_list.find_value(code=code)
        except ValueError:
            raise RuntimeError('证券代码名称规整表 Found no code like {}'.format(code))
        assert isinstance(obj, SecurityInfo)
        return obj.security_type

    def find_exchange_rate(self, date: datetime.date, field: str, ):
        try:
            obj = self.__exchange_rate_list__.find_value(date=date, field=field)
        except ValueError:
            currency = field[:3].upper()
            obj_list = List.from_pd(ExchangeRate, self.db.read_pd_query(
                DataBaseName.management,
                """
                SELECT DISTINCT 日期, '{}' as 汇率代码, 汇率 FROM `原始中信收益互换账户资金记录` 
                WHERE 币种 = '{}' AND 日期 = (
                    SELECT MAX(`日期`) FROM `原始中信收益互换账户资金记录` WHERE `币种` = '{}' AND `日期` <= '{}'
                )
                ;""".format(field, currency, currency, date),
                # """SELECT * FROM 汇率表 WHERE 日期 = '{}' and 汇率代码 = '{}';""".format(date, field)
            ))
            if len(obj_list) == 1:
                obj = obj_list[0]
            elif len(obj_list) == 0:
                raise RuntimeError('数据库 jm_fundmanagement.原始中信收益互换账户资金记录 中缺少数据 {} {}'.format(date, field))
            else:
                raise RuntimeError('未知错误 {}'.format(obj_list))
            self.__exchange_rate_list__.append(obj)
        assert isinstance(obj, ExchangeRate)
        return obj

    def find_security_trade_fee(
            self, product: str, institution: str, security_type: str, fee_type: str, date: datetime.date
    ):
        info_tag = '{} - {} - {} - {} - {}'.format(product, institution, security_type, fee_type, date)
        sub_product_list = self.product_trade_fee_list.find_value_where(product=product)
        assert len(sub_product_list) > 0, '获取产品证券交易费率失败：没有录入该产品 {}'.format(info_tag)
        sub_list = sub_product_list.find_value_where(institution=institution)
        assert len(sub_list) > 0, '获取产品证券交易费率失败： 没有录入该券商信息 {}\n{}'.format(info_tag, sub_product_list)
        sub_list = sub_list.find_value_where(security_type=security_type)
        assert len(sub_list) > 0, '获取产品证券交易费率失败： 没有录入该证券类别 {}\n{}'.format(info_tag, sub_product_list)
        sub_list = sub_list.find_value_where(fee_type=fee_type)
        assert len(sub_list) > 0, '获取产品证券交易费率失败： 没有录入该费率类别 {}\n{}'.format(info_tag, sub_product_list)
        sub_list = sub_list.trim_include_between_attr_value('update_date', None, date, include_end=True, )
        assert len(sub_list) > 0, '获取产品证券交易费率失败： 没有录入该时间范围 {}\n{}'.format(info_tag, sub_product_list)
        obj = sub_list.find_value(update_date=max(sub_list.collect_attr_set('update_date')))
        assert isinstance(obj, TradeFeeRate)
        return obj

    # def find_security_trade_fee(self, product: str, institution: str, security_type: str, date: datetime.date):
    #     sub_list = self.product_trade_fee_list.find_value_where(product=product)
    #     if len(sub_list) == 0:
    #         raise RuntimeError('未知产品或者产品交易费用信息当中没有录入该产品 {}'.format(product))
    #     sub_list = sub_list.find_value_where(institution=institution)
    #     if len(sub_list) == 0:
    #         raise RuntimeError('产品{}交易费用信息当中没有录入该券商信息 {}'.format(product, institution))
    #     sub_list = sub_list.find_value_where(security_type=security_type)
    #     if len(sub_list) == 0:
    #         raise RuntimeError(
    #             '产品{}交易费用信息当中没有录入券商{}下该类证券类别信息 {}'.format(product, institution, security_type)
    #         )
    #     sub_list = sub_list.trim_include_between_attr_value('update_date', None, date, include_end=True, )
    #     if len(sub_list) == 0:
    #         raise RuntimeError('产品交易费用信息当中没有录入该券商下该类证券类别信息 {}'.format(date))
    #     elif len(sub_list) == 1:
    #         obj = sub_list[0]
    #     else:
    #         obj = sub_list.find_value(update_date=max(sub_list.collect_attr_set('update_date')))
    #     assert isinstance(obj, TradeFeeRate)
    #     return obj

    def find_product_account_interest_rate(
            self, product: str, account_type: str, institution: str, date: datetime.date
    ):
        """返回产品账户利率信息 -> float"""
        sub_list = self.product_account_interest_rate_list.find_value_where(product=product)
        if len(sub_list) == 0:
            raise RuntimeError('未知产品或者产品账户利率信息当中没有录入该产品 {}'.format(product))
        sub_list = sub_list.find_value_where(account_type=account_type)
        if len(sub_list) == 0:
            raise RuntimeError('产品 {} 账户利率信息当中没有录入账户 {} {} 信息'.format(product, account_type, institution))
        sub_list = sub_list.trim_include_between_attr_value('update_date', None, date, include_end=True, )
        obj = None
        for institution_tag, institution_list in sub_list.group_by_attr('institution').items():
            assert isinstance(institution_list, List)
            if institution_tag == institution or institution_tag == '-':
                if len(institution_list) == 0:
                    raise RuntimeError('产品{}账户利率信息中没有录入{}下机构{}信息'.format(product, account_type, institution))
                assert obj is None
                obj = institution_list.find_value(update_date=max(institution_list.collect_attr_set('update_date')))
                if institution_tag == '-' and institution != '-':
                    raise NotImplementedError('产品 {} 账户 {} 机构 {} 缺失信息 {} \n{}'.format(
                        product, account_type, institution_tag, institution, sub_list))
        assert isinstance(obj, AccountInterestRate), '产品 {} 账户 {} 机构 {} 缺失信息\n{}'.format(
            product, account_type, institution, sub_list,
        )
        return obj

    def find_dividend_info_list(self, date: datetime.date):
        return List.from_pd(DividendInfo, self.db.read_pd_query(
            DataBaseName.valuation,
            """
            SELECT * FROM 股利信息表 WHERE 除权日 <= '{}' AND 派息日 >= '{}';
            """.format(date, date)
        ))

    # ------------------------ [methods - using information] ------------------------
    def check_mandatory(self, product: str):
        """
        判断是否是托管产品 -> bool，True 托管产品，False 非托管产品
        :param product: 产品简称
        :return: bool，True 托管产品，False 非托管产品
        """
        if self.find_product_mandatory(product=product) == '非托管':
            return False
        else:
            return True

    def is_active_normal_account(self, product: str, institution: str, date: datetime.date):
        """判断一个证券账户是否不再使用"""
        acc_list = List.from_pd(RawNormalAccount, self.db.read_pd_query(DataBaseName.management, """
        SELECT * FROM 原始普通账户资金记录 WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}'
        ;""".format(product, date, institution)))
        if len(acc_list) == 1:
            return True
        elif len(acc_list) == 0:
            last_acc_list = List.from_pd(RawNormalAccount, self.db.read_pd_query(
                DataBaseName.management,
                """
                SELECT * FROM 原始普通账户资金记录 WHERE 产品 = '{product}' AND 机构 = '{institution}' AND 日期 = (
                    SELECT MAX(日期) FROM 原始普通账户资金记录 WHERE 产品 = '{product}' AND 机构 = '{institution}' 
                    AND 日期 < '{date}'
                );""".format(product=product, date=date, institution=institution)))
            if len(last_acc_list) == 0:
                raise RuntimeError('未知账户 {} {} {}'.format(product, institution, date))
            elif len(last_acc_list) == 1:
                last_acc_obj = last_acc_list[0]
                assert isinstance(last_acc_obj, RawNormalAccount), str(last_acc_obj)
                if date - last_acc_obj.date < datetime.timedelta(days=15):
                    # 处理利息结转 利息结转过去一个月当中只有一次资金记录
                    last_acc_list = List.from_pd(RawNormalAccount, self.db.read_pd_query(DataBaseName.management, """
                    SELECT * FROM 原始普通账户资金记录 WHERE 产品 = '{}' AND 机构 = '{}' AND 日期 > '{}'
                    ;""".format(product, institution, date - datetime.timedelta(days=30))))
                    if len(last_acc_list) <= 1:
                        return False
                    else:
                        return True
                else:
                    return False
            else:
                raise RuntimeError(last_acc_list)
        else:
            raise RuntimeError(acc_list)

    def is_active_margin_account(self, product: str, institution: str, date: datetime.date):
        """判断一个信用证券账户是否不再使用"""
        acc_list = List.from_pd(RawNormalAccount, self.db.read_pd_query(DataBaseName.management, """
        SELECT * FROM 原始两融账户资金记录 WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}'
        ;""".format(product, date, institution)))
        if len(acc_list) == 1:
            return True
        elif len(acc_list) == 0:
            last_acc_list = List.from_pd(RawNormalAccount, self.db.read_pd_query(
                DataBaseName.management,
                """
                SELECT * FROM 原始两融账户资金记录 WHERE 产品 = '{product}' AND 机构 = '{institution}' AND 日期 = (
                    SELECT MAX(日期) FROM 原始两融账户资金记录 WHERE 产品 = '{product}' AND 机构 = '{institution}' 
                    AND 日期 < '{date}'
                );""".format(product=product, date=date, institution=institution)))
            if len(last_acc_list) == 0:
                raise RuntimeError('未知账户 {} {} {}'.format(product, institution, date))
            elif len(last_acc_list) == 1:
                last_acc_obj = last_acc_list[0]
                assert isinstance(last_acc_obj, RawNormalAccount), str(last_acc_obj)
                if date - last_acc_obj.date < datetime.timedelta(days=15):
                    last_acc_list = List.from_pd(RawNormalAccount, self.db.read_pd_query(
                        DataBaseName.management,
                        """
                        SELECT * FROM 原始两融账户资金记录 WHERE 产品 = '{}' AND 机构 = '{}' AND 日期 > '{}';""".format(
                            product, institution, date - datetime.timedelta(days=30))))
                    if len(last_acc_list) <= 1:
                        return False
                    else:
                        return True
                else:
                    return False
            else:
                raise RuntimeError(last_acc_list)
        else:
            raise RuntimeError(acc_list)
    
    def is_active_future_account(self, product: str, institution: str, date: datetime.date):
        """判断一个信用证券账户是否不再使用"""
        acc_list = List.from_pd(RawFutureAccount, self.db.read_pd_query(DataBaseName.management, """
        SELECT * FROM 原始期货账户资金记录 WHERE 产品 = '{}' AND 日期 = '{}' AND 机构 = '{}'
        ;""".format(product, date, institution)))
        if len(acc_list) == 1:
            return True
        elif len(acc_list) == 0:
            last_acc_list = List.from_pd(RawFutureAccount, self.db.read_pd_query(
                DataBaseName.management,
                """
                SELECT * FROM 原始期货账户资金记录 WHERE 产品 = '{product}' AND 机构 = '{institution}' AND 日期 = (
                    SELECT MAX(日期) FROM 原始期货账户资金记录 WHERE 产品 = '{product}' AND 机构 = '{institution}' 
                    AND 日期 < '{date}'
                );""".format(product=product, date=date, institution=institution)))
            if len(last_acc_list) == 0:
                return False
                # raise RuntimeError('未知账户 {} {} {}'.format(product, institution, date))
            elif len(last_acc_list) == 1:
                last_acc_obj = last_acc_list[0]
                assert isinstance(last_acc_obj, RawFutureAccount), str(last_acc_obj)
                if date - last_acc_obj.date < datetime.timedelta(days=15):
                    last_acc_list = List.from_pd(RawFutureAccount, self.db.read_pd_query(
                        DataBaseName.management,
                        """
                        SELECT * FROM 原始期货账户资金记录 WHERE 产品 = '{}' AND 机构 = '{}' AND 日期 > '{}';""".format(
                            product, institution, date - datetime.timedelta(days=30))))
                    if len(last_acc_list) <= 1:
                        return False
                    else:
                        return True
                else:
                    return False
            else:
                raise RuntimeError(last_acc_list)
        else:
            raise RuntimeError(acc_list)

    # ------------------------ [methods - functional] ------------------------
    def calculate_security_trade_fee(
            self, product: str, date: datetime.date, institution: str, security_code: str, trade_amount: float,
            trade_name: str = None,
    ):
        """计算交易流水的费用"""
        assert '.' in security_code, security_code
        if security_code.split('.')[-1].upper() in ('SH', 'SZ'):
            if security_code[:3] in ('110', '113', '128'):
                security_type = '转债'
            elif security_code[:3] in ('127', '132', ):
                security_type = '债券'
            elif security_code[:3] in ('510', ):
                security_type = 'ETF'
            else:
                security_type = '股票'
        elif security_code.split('.')[-1].upper() in ('HK',):
            security_type = '港股通'
        elif security_code.split('.')[-1].upper() in ('CFE', ):
            security_type = '期货'
        else:
            raise NotImplementedError(security_code)

        if trade_name is None:
            pass
        else:
            security_type = trade_name

        if '港股通' in institution:
            institution = institution.replace('港股通', '')
        else:
            pass

        fee_rate = self.find_security_trade_fee(product, institution, security_type, date)
        return fee_rate.fee_rate * trade_amount
