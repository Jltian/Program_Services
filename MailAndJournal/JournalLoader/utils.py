# -*- encoding: UTF-8 -*-
import os

from collections import defaultdict

from Checker import *


def identify_valuation_records(m_list: list, hand_dict: dict):
    """
    识别托管估值表内容
    m_list: 匹配字段行的字典列表, 列表键：
        account_code
    """
    check_str_element(hand_dict, 'product_code', '产品代码')
    check_str_element(hand_dict, 'product_name', '产品简称')
    check_str_element(hand_dict, 'file_name', '文件名')
    check_str_element(hand_dict, 'institution', '托管')
    assert 'date' in hand_dict, hand_dict
    brief_info_dict = dict()
    brief_info_dict.update(hand_dict)
    flag = False
    count = 0
    for m_dict in m_list:
        assert isinstance(m_dict, dict)
        account_code = check_str_element(m_dict, 'account_code', '科目代码', blank_skip=True)
        account_code = re.sub(r'\W', '', account_code)
        if account_code in ('昨日单位净值',''):
            flag = False
        if account_code in ('单位净值', '今日单位净值', '基金单位净值'):
            brief_info_dict['net_value'] = float_check(m_dict['account_name'])
        if '今日单位净值其中' in account_code and 'B' not in account_code:
            brief_info_dict['net_value_a'] = float_check(m_dict['account_name'])
        # if count == 70 and 'B' not in account_code: －－单位净值其中
        if flag and 'B' not in account_code:
            brief_info_dict['net_value_a'] = float_check(m_dict['account_name'])
        # brief_info_dict['net_value_a'] = float_check(m_dict['account_name'])
        if '今日单位净值其中' in account_code and 'B' in account_code:
            brief_info_dict['net_value_b'] = float_check(m_dict['account_name'])
        if flag and 'B' in account_code:
            brief_info_dict['net_value_b'] = float_check(m_dict['account_name'])


        # if count == 70 and 'B' in account_code:
        #     brief_info_dict['net_value_b'] = float_check(m_dict['account_name'])
        if flag == True:
            count = count + 1
        def load_mv_or_tmv(m_dict: dict):
            try:
                return float_check(m_dict['market_value'])
            except KeyError:
                return float_check(m_dict['total_market_value'])
        if account_code in ('资产净值', '基金资产净值', ):
            brief_info_dict['net_asset'] = load_mv_or_tmv(m_dict)
            # try:
            #     brief_info_dict['net_asset'] = float_check(m_dict['market_value'])
            # except KeyError:
            #     brief_info_dict['net_asset'] = float_check(m_dict['total_market_value'])
        if '资产净值其中' in account_code and 'B' not in account_code:
            brief_info_dict['net_asset_a'] = load_mv_or_tmv(m_dict)
        if '资产净值其中' in account_code and 'B' in account_code:
            brief_info_dict['net_asset_b'] = load_mv_or_tmv(m_dict)
        if account_code == '实收资本':
            try:
                brief_info_dict['fund_shares'] = float_check(m_dict['market_value'])
            except KeyError:
                brief_info_dict['fund_shares'] = float_check(m_dict['total_market_value'])
        if '实收资本其中' in account_code and 'B' not in account_code:
            brief_info_dict['fund_shares_a'] = load_mv_or_tmv(m_dict)
        if '实收资本其中' in account_code and 'B' in account_code:
            brief_info_dict['fund_shares_b'] = load_mv_or_tmv(m_dict)
        if account_code in ('资产合计', '资产类合计', ):
            try:
                brief_info_dict['total_asset'] = float_check(m_dict['market_value'])
            except KeyError:
                brief_info_dict['total_asset'] = float_check(m_dict['total_market_value'])
        if account_code in ('负债合计', '负债类合计', ):
            try:
                brief_info_dict['total_liability'] = float_check(m_dict['market_value'])
            except KeyError:
                brief_info_dict['total_liability'] = float_check(m_dict['total_market_value'])
        if account_code in ('单位净值', '今日单位净值', '基金单位净值'):
            flag = True
    brief_info_dict.update(hand_dict)#把 hand_dict 中的键值对添加到 brief_info_dict中
    check_float_element(brief_info_dict, 'net_value', '单位净值')
    check_float_element(brief_info_dict, 'net_asset', '净资产')
    check_float_element(brief_info_dict, 'fund_shares', '基金份额')
    check_float_element(brief_info_dict, 'total_asset', '资产总值')
    try:
        check_float_element(brief_info_dict, 'total_liability', '负债合计')
    except AssertionError as error_assert:
        if is_different_float(brief_info_dict['net_asset'], brief_info_dict['total_asset'], gap=1.0):
            raise error_assert
        else:
            brief_info_dict['total_liability'] = 0.0
    # 检查单位净值、基金份额和资产净值是否自洽
    check_multiply_match(
        brief_info_dict['net_value'], brief_info_dict['fund_shares'], brief_info_dict['net_asset'],
        error_percent=0.001,
    )
    check_addition_match(
        abs(brief_info_dict['total_asset']), - abs(brief_info_dict['total_liability']),
        brief_info_dict['net_value'], error_abs=10.0,
    )
    # 检查A、B类份额是否自洽
    try:
        check_float_element(brief_info_dict, 'net_value_b', '单位净值')
    except AssertionError:
        try:
            check_float_element(brief_info_dict, 'net_value_a', '单位净值')
        except AssertionError:
            brief_info_dict['net_value_b'] = math.nan
            brief_info_dict['net_asset_b'] = math.nan
            brief_info_dict['fund_shares_b'] = math.nan
            brief_info_dict['net_value_a'] = math.nan
            brief_info_dict['net_asset_a'] = math.nan
            brief_info_dict['fund_shares_a'] = math.nan
    try:
        if is_valid_float(brief_info_dict['net_value_b']):
            check_float_element(brief_info_dict, 'net_value_b', '单位净值B')
            check_float_element(brief_info_dict, 'net_asset_b', '净资产B')
            check_float_element(brief_info_dict, 'fund_shares_b', '基金份额B')
            try:
                check_float_element(brief_info_dict, 'net_value_a', '单位净值A')
            except AssertionError:
                brief_info_dict['net_value_a'] = 0
            try:
                check_float_element(brief_info_dict, 'net_asset_a', '净资产A')
            except AssertionError:
                brief_info_dict['net_asset_a'] = 0
            try:
                check_float_element(brief_info_dict, 'fund_shares_a', '基金份额A')
            except AssertionError:
                brief_info_dict['fund_shares_a'] = 0
            check_addition_match(
                brief_info_dict['net_asset_a'], brief_info_dict['net_asset_b'], brief_info_dict['net_asset'],
                error_abs=10.0,
            )
            check_addition_match(
                brief_info_dict['fund_shares_a'], brief_info_dict['fund_shares_b'], brief_info_dict['fund_shares'],
                error_abs=10.0,
            )
    except KeyError:
        if is_valid_float(brief_info_dict['net_value_a']):
            check_float_element(brief_info_dict, 'net_value_a', '单位净值A')
            check_float_element(brief_info_dict, 'net_asset_a', '净资产A')
            check_float_element(brief_info_dict, 'fund_shares_a', '基金份额A')
            try:
                check_float_element(brief_info_dict, 'net_value_b', '单位净值B')
            except AssertionError:
                brief_info_dict['net_value_b'] = 0
            try:
                check_float_element(brief_info_dict, 'net_asset_b', '净资产B')
            except AssertionError:
                brief_info_dict['net_asset_b'] = 0
            try:
                check_float_element(brief_info_dict, 'fund_shares_b', '基金份额B')
            except AssertionError:
                brief_info_dict['fund_shares_b'] = 0
            check_addition_match(
                brief_info_dict['net_asset_a'], brief_info_dict['net_asset_b'], brief_info_dict['net_asset'],
                error_abs=10.0,
            )
            check_addition_match(
                brief_info_dict['fund_shares_a'], brief_info_dict['fund_shares_b'], brief_info_dict['fund_shares'],
                error_abs=10.0,
            )
    def derive_detail_dict(d_dict: dict):
        r_dict = dict()
        r_dict['account_name'] = check_str_element(d_dict, 'account_name', '科目名称')
        r_dict['exchange_rate'] = float_check(d_dict['exchange_rate'])
        r_dict['hold_volume'] = float_check(d_dict['hold_volume'])
        r_dict['average_cost'] = float_check(d_dict['average_cost'])
        r_dict['total_cost'] = float_check(d_dict['total_cost'])
        # r_dict['total_cost'] = check_float_element(d_dict, 'total_cost', '本币成本')
        r_dict['market_price'] = float_check(d_dict['market_price'])
        r_dict['market_value'] = check_float_element(d_dict, 'market_value', '本币市值')
        r_dict['value_changed'] = float_check(d_dict['value_changed'])
        r_dict['suspension_info'] = str_check(d_dict['suspension_info'])
        r_dict['currency'] = str_check(d_dict['currency'])
        return r_dict
    # if hand_dict['institution'] in ('招商证券', ):
    if hand_dict['institution'] in ():
        detail_info_list = list()
        # stock_code_set = set()
        stock_tag = '普通'
        for m_dict in m_list:
            assert isinstance(m_dict, dict)
            account_code = check_str_element(m_dict, 'account_code', '科目代码', blank_skip=True)
            # 跳过空代码和非数字组成代码
            if len(re.sub(r'\W', '', account_code)) == 0:
                continue
            if not re.match(r'\d+', re.sub(r'\W', '', account_code)[:4]):
                continue
            detail_dict = derive_detail_dict(m_dict)
            detail_dict.update(hand_dict)
            detail_dict.pop('institution')
            account_code_list = account_code.split('.')
            detail_dict['account_code'] = account_code_list[0]
            detail_dict['security_code'] = account_code_list[0]
            # 银行存款 1002 三级科目
            if account_code_list[0] == '1002' and len(account_code_list) == 3:
                detail_dict['institution'] = detail_dict['account_name'].split('_')[2]
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
            # 结算备付金 1021 三级科目
            if account_code_list[0] == '1021' and len(detail_dict['account_name'].split('_')) == 3:
                detail_dict['institution'] = detail_dict['account_name'].split('_')[2]
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
            # 存储保证金 1031 三级科目
            if account_code_list[0] == '1031' and len(detail_dict['account_name'].split('_')) == 3:
                detail_dict['institution'] = detail_dict['account_name'].split('_')[2]
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
            # 股票投资 1102 四级科目
            if account_code_list[0] == '1102' and len(account_code_list) == 3:
                if detail_dict['account_name'].split('_')[2] in ('普通',):
                    pass
                elif detail_dict['account_name'].split('_')[2] in ('信用', ):
                    stock_tag = '信用'
                else:
                    raise RuntimeError(m_dict)
            if account_code_list[0] == '1102' and len(account_code_list) == 4:
                detail_dict['institution'] = stock_tag
                try:
                    detail_dict['security_code'] = account_code_list[3].replace(' ', '.')
                except IndexError as error_index:
                    print('{} \n {}'.format(detail_dict, m_dict))
                    raise error_index
                detail_dict['security_name'] = detail_dict['account_name']
            # 理财投资 1108 四级科目
            if account_code_list[0] == '1108' and len(account_code_list) > 3:
                detail_dict['security_code'] = account_code_list[3].replace(' ', '.')
                detail_dict['security_name'] = detail_dict['account_name']
                if '久铭' in detail_dict['account_name']:
                    detail_dict['institution'] = '久铭'
                else:
                    raise NotImplementedError(detail_dict)
            # 其他应收款 1221 二级科目
            if account_code_list[0] == '1221' and len(account_code_list) == 2:
                detail_dict['institution'] = detail_dict['account_name'].split('_')[1]
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
            # 短期借款 2001 三级科目
            if account_code_list[0] == '2001' and len(account_code_list) == 3:
                detail_dict['institution'] = detail_dict['account_name'].split('_')[1]
                detail_dict['security_code'] = '-'
                detail_dict['market_value'] = - abs(detail_dict['market_value'])
                detail_dict['hold_volume'] = 0.0
            # 应付管理人报酬 2206 二级科目
            if account_code_list[0] == '2206' and len(account_code_list) == 2:
                detail_dict['institution'] = '-'
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
                detail_dict['market_value'] = - abs(detail_dict['market_value'])
            # 应付托管费 2207 二级科目
            if account_code_list[0] == '2207' and len(account_code_list) == 2:
                detail_dict['institution'] = '-'
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
                detail_dict['market_value'] = - abs(detail_dict['market_value'])
            # 应付运营服务费 2211 二级科目
            if account_code_list[0] == '2211' and len(account_code_list) == 2:
                detail_dict['institution'] = '-'
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
                detail_dict['market_value'] = - abs(detail_dict['market_value'])
            # 应付利息 2231 二级科目
            if account_code_list[0] == '2231' and len(account_code_list) == 2:
                detail_dict['institution'] = detail_dict['account_name'].split('_')[1]
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
                detail_dict['market_value'] = - abs(detail_dict['market_value'])
            # 其他应付款 2241 二级科目
            if account_code_list[0] == '2241' and len(account_code_list) == 2:
                detail_dict['institution'] = detail_dict['account_name'].split('_')[1]
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
                detail_dict['market_value'] = - abs(detail_dict['market_value'])
            # 应付税费 2331 二级科目
            if account_code_list[0] == '2331' and len(account_code_list) == 2:
                detail_dict['institution'] = detail_dict['account_name'].split('_')[1]
                detail_dict['security_code'] = '-'
                detail_dict['hold_volume'] = 0.0
                detail_dict['market_value'] = - abs(detail_dict['market_value'])
            # 证券清算款 3003 三级科目
            if account_code_list[0] == '3003' and len(account_code_list) == 3:
                detail_dict['institution'] = detail_dict['account_name']
                detail_dict['security_code'] = '-'
                detail_dict['security_name'] = '-'
                detail_dict['hold_volume'] = 0.0
            # 衍生工具 3102 一级科目
            if account_code_list[0] == '3102' and len(account_code_list) == 4:
                detail_dict['institution'] = '-'
                detail_dict['security_code'] = account_code_list[3].replace(' ', '.')
                detail_dict['security_name'] = detail_dict['account_name']
                # detail_dict['market_value'] = - abs(detail_dict['market_value'])

            if 'institution' in detail_dict:
                detail_info_list.append(detail_dict)
        total_fund_value = 0.0
        for obj in detail_info_list:
            total_fund_value += obj['market_value']
        assert not is_different_float(total_fund_value, brief_info_dict['net_asset'], gap=0.5), '{}\n{}\n{}'.format(
            total_fund_value - brief_info_dict['net_asset'], brief_info_dict,
            '\n'.join([str(var) for var in detail_info_list])
        )
        brief_info_dict['detail_info_list'] = detail_info_list

    return brief_info_dict


product_key_list = ['Service Type', 'Operation Level', 'Service Domain', 'Data']
normal_table_map = {
    'position': '原始普通持仓记录', 'account': '原始普通账户资金记录', 'flow': '原始普通流水记录'
}
margin_table_map = {
    'position': '原始两融持仓记录', 'account': '原始两融账户资金记录',
    'liabilities': '原始两融负债记录', 'flow': '原始两融流水记录'
}
future_table_map = {
    'position': '原始期货持仓记录', 'account': '原始期货账户资金记录', 'flow': '原始期货流水记录'
}


def get_data_dict(folder_name, **kwargs):
    product_name = kwargs.get('product_name', None)
    pos_list = kwargs.get('pos_list', None)
    acc_obj = kwargs.get('acc_obj', None)
    flow_list = kwargs.get('flow_list', None)
    assert product_name != None, 'Instruction data missing product name info. \n {}'.format(kwargs)
    data_dict = defaultdict()
    data_dict['product'] = product_name
    data_dict['position'] = pos_list
    data_dict['account'] = acc_obj
    data_dict['flow'] = flow_list
    if '两融' in folder_name:
        liability_list = kwargs.get('liability', None)
        data_dict['liabilities'] = liability_list
    else:
        pass
    return data_dict


def get_journal(data_dict):
   product_dict = defaultdict()
   product_dict['Service Type'] = 'Insert into db'
   # product_dict['Operation Level'] =
   product_dict['Service Domain'] = os.path.dirname(__file__)
   product_dict['Data'] = data_dict
   return product_dict

