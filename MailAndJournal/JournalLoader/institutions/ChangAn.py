# -*- encoding: UTF-8 -*-
import datetime
import os
import re
import xlrd

from jetend.Interface import AttributeObject

from Abstracts import AbstractInstitution
from Checker import *


class PuRui(AttributeObject):
    inner2outer_map = {
        'product': '产品', 'date': '日期',
        'net_value': '单位净值', 'net_value_a': '单位净值A类', 'net_value_b': '单位净值B类',
        'fund_shares': '基金份额', 'fund_shares_a': '基金份额A类', 'fund_shares_b': '基金份额B类',
        'net_asset': '净资产', 'net_asset_a': '净资产A类', 'net_asset_b': '净资产B类',
    }



class ChangAn(AbstractInstitution):

    valuation_line = {
        'account_code': ['科目代码', ], 'account_name': ['科目名称', ], 'currency': ['币种', ],
        'exchange_rate': ['汇率', ], 'hold_volume': ['数量', ], 'average_cost': ['单位成本', ],
        'total_cost': ['成本-本币', '成本', '成本本币'], 'market_price': ['行情', '市价'],
        'total_market_value': ['市值-本币', '市值', '市值本币'],
        'None': [
            '成本占比', '市值占比', '估值增值-本币', '停牌信息', '权益信息', '市值占净值', '成本占净值', '估值增值', '估值增值本币',
        ]
    }

    @staticmethod
    def load_valuation_table(file_path: str):
        from jetend.structures import ExcelMapper
        file_name = file_path.split(os.path.sep)[-1]
        ChangAn.log.debug_running('读取托管估值表', file_name)
        # 文件名：证券投资基金估值表_长安久铭浦睿1号资产管理计划_2019-08-28
        try:
            date_str = re.search(r'\w+_\w+_(\d+-\d+-\d+)', file_name).group(1)
        except AttributeError:
            raise RuntimeError(file_name)
        assert '浦睿1号' in file_name, file_path
        product = '浦睿1号'

        date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        # assert date.strftime('%Y%m%d') in file_path, '{}\n{}'.format(date, file_path)

        hand_dict = {'product': product, 'date': date, }
        result_dict = dict()
        mapper = ExcelMapper(ChangAn.valuation_line, hand_dict, )
        mapper.set_duplicated_tolerance(True).set_force_vertical(True)
        m_list = mapper.map(xlrd.open_workbook(file_path).sheet_by_index(0))
        assert len(m_list) > 0, '估值表 {} 读取失败！'.format(file_path)
        # 读取净值、份额、净资产、税费
        for m_dict in m_list:
            assert isinstance(m_dict, dict)
            account_code = check_str_element(m_dict, 'account_code', '科目代码')
            account_name = m_dict.get('account_name', '')
            # account_name = check_str_element(m_dict, 'account_name', '科目名称')
            if '今日单位净值' in account_code:
                if 'A类' in account_code:
                    result_dict['net_value_a'] = float_check(m_dict['account_name'])
                elif 'B类' in account_code:
                    result_dict['net_value_b'] = float_check(m_dict['account_name'])
                else:
                    result_dict['net_value'] = float_check(m_dict['account_name'])
            if '资产净值' in account_code:
                if 'A类' in account_code:
                    result_dict['net_asset_a'] = float_check(m_dict['total_market_value'])
                elif 'B类' in account_code:
                    result_dict['net_asset_b'] = float_check(m_dict['total_market_value'])
                    if not is_valid_float(result_dict['net_asset_b']):
                        result_dict['net_asset_b'] = 0.0
                else:
                    result_dict['net_asset'] = float_check(m_dict['total_market_value'])

            # if re.sub(r'\W', '', account_code) == '基金资产净值':
            #     result_dict['net_asset'] = float_check(m_dict['total_market_value'])
            # if re.sub(r'\W', '', account_code) == '基金资产净值741184长安久铭浦睿A类':
            #     result_dict['net_asset_a'] = float_check(m_dict['total_market_value'])
            # if re.sub(r'\W', '', account_code) == '基金资产净值741185长安久铭浦睿B类':
            #     result_dict['net_asset_b'] = float_check(m_dict['total_market_value'])
            if '实收资本' in account_code:
                if 'A类' in account_code:
                    result_dict['fund_shares_a'] = float_check(m_dict['total_market_value'])
                elif 'B类' in account_code:
                    result_dict['fund_shares_b'] = float_check(m_dict['total_market_value'])
                else:
                    result_dict['fund_shares'] = float_check(m_dict['total_market_value'])

            # if re.sub(r'\W', '', account_code) == '实收资本':
            #     result_dict['fund_shares'] = float_check(m_dict['total_market_value'])
            # if re.sub(r'\W', '', account_code) == '实收资本741184长安久铭浦睿A类':
            #     result_dict['fund_shares_a'] = float_check(m_dict['total_market_value'])
            # if re.sub(r'\W', '', account_code) == '实收资本741185长安久铭浦睿B类':
            #     result_dict['fund_shares_b'] = float_check(m_dict['total_market_value'])
            # if '税' in account_name:
            #     if len(str_check(account_code)) == 4:
            #         assert 'tax_payable' not in result_dict, str('重复读取应交税费 {} {}'.format(file_path, m_dict))
            #         result_dict['tax_payable'] = float_check(m_dict['total_market_value'])
            #     elif len(str_check(m_dict['account_code'])) > 4:
            #         pass
            #     else:
            #         raise NotImplementedError('{} {}'.format(file_path, m_dict))
        check_float_element(result_dict, 'net_value', '单位净值')
        try:
            check_float_element(result_dict, 'net_value_a', '单位净值A')
        except AssertionError as a_error:
            if not is_different_float(result_dict['net_value'], 1.0):
                result_dict['net_asset_a'] = 0.0
            else:
                raise a_error
        try:
            check_float_element(result_dict, 'net_value_b', '单位净值B')
        except AssertionError as a_error:
            if not is_different_float(result_dict['net_value'], 1.0):
                result_dict['net_value_b'] = 0.0
            else:
                raise a_error
        check_float_element(result_dict, 'net_asset', '净资产')
        # check_float_element(result_dict, 'net_asset_a', '净资产A')
        try:
            check_float_element(result_dict, 'net_asset_a', '净资产A')
        except AssertionError as a_error:
            if not is_different_float(result_dict['net_value'], 1.0):
                result_dict['net_asset_a'] = 0.0
            else:
                raise a_error
        try:
            check_float_element(result_dict, 'net_asset_b', '净资产B')
        except AssertionError as a_error:
            if not is_different_float(result_dict['net_value_b'], 1.0):
                result_dict['net_asset_b'] = 0.0
            elif not is_different_float(result_dict['net_asset_a'], 0.0):
                result_dict['net_asset_b'] = 0.0
            else:
                raise a_error
        check_float_element(result_dict, 'fund_shares', '基金份额')
        try:
            check_float_element(result_dict, 'fund_shares_a', '基金份额A')
        except AssertionError as a_error:
            if not is_different_float(result_dict['net_value'], 1.0):
                result_dict['fund_shares_a'] = 0.0
            else:
                raise a_error
        try:
            check_float_element(result_dict, 'fund_shares_b', '基金份额B')
        except AssertionError as a_error:
            if not is_different_float(result_dict['net_value_b'], 1.0):
                result_dict['fund_shares_b'] = 0.0
            elif not is_different_float(result_dict['net_value_b'], 0.0):
                result_dict['fund_shares_b'] = 0.0
            else:
                raise a_error
        result_dict.update(hand_dict)
        return result_dict


if __name__ == '__main__':
    from jetend.structures import List
    folder = r'D:\Downloads\浦睿1号'

    result_list = List()
    for file_name in os.listdir(folder):
        if file_name.startswith('.') or file_name.startswith('~'):
            continue
        result_list.append(PuRui.from_dict(ChangAn.load_valuation_table(os.path.join(folder, file_name))))
    result_list.to_pd().to_csv(os.path.join(r'D:\Downloads', '浦睿1号.csv'), encoding='gb18030')

    # print(PuRui.from_dict(ChangAn.load_valuation_table(
    #     r'W:\整理产品对账单\浦睿1号\托管估值表\证券投资基金估值表_长安久铭浦睿1号资产管理计划_2019-08-28.xls'
    # )))
