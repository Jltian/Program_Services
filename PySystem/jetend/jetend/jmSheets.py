# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
from jetend.Interface import AttributeObject


class JiuMingTA:

    class InvestorFeeProvision(AttributeObject):
        """
        transfer_agent.INVESTOR_FEE_PROVISION_RECORDS
        """
        inner2outer_map = {
            'date': 'date', 'investor_code': 'investor_code',
            'product_code': 'product_code', 'fee_type': 'fee_type',
            'fee_amount': 'fee_amount', 'purchase_id': 'purchase_id'
        }

    class InvestorHolding(AttributeObject):
        """
        transfer_agent.INVESTOR_HOLDING_RECORDS
        """
        inner2outer_map = {
            'date': 'date', 'investor_code': 'investor_code',
            'product_code': 'product_code', 'performace_date': 'performace_date',
            'hold_volume': 'hold_volume', 'performace_cost': 'performace_cost',
            'purchase_id': 'purchase_id'
        }

    class TransferAgentFlow(AttributeObject):
        """
        jiuming_ta_new.申赎流水表
        """
        inner2outer_map = {
            'name': 'name', 'idnumber': 'idnumber', 'date': 'date', 'product_name': 'product_name',
            'type': 'type', 'amount': 'amount', 'netvalue': 'netvalue', 'share': 'share',
            'fee': 'fee', 'sales_agency': 'sales_agency', 'sales_manager': 'sales_manager',
            'purchase_id': 'purchase_id', 'journal_id': 'journal_id',
            'confirmation_date': 'confirmation_date',
        }

        @property
        def investor_code(self):
            return self.idnumber.strip()


class HashableElement(AttributeObject):

    @property
    def hash_key(self):
        from random import random
        from jetend.DataCheck import str_check, is_valid_str
        hash_key = str_check(self.get_attr('hash_key'))
        if is_valid_str(hash_key):
            return hash_key
        else:
            return '{}-{}-{}'.format(self.date.strftime('%Y%m%d'), hash(str(self.__dict__)), random())


class AccountInterestRate(AttributeObject):
    """账户资金利率 - management.产品账户资金利率表"""
    inner2outer_map = {
        'product': '产品', 'account_type': '账户类型', 'institution': '机构', 'interest_rate': '利率',
        'yearly_accrued_days': '计息日长', 'update_date': '更新日期', 'notes': '备注',
    }


class AccountLiabilityInterestRate(AttributeObject):
    """产品融资融券利率 - management.产品融资融券利率表"""
    inner2outer_map = {
        'product': '产品', 'institution': '机构', 'interest_type': '利率类型', 'interest_rate': '利率',
        'update_date': '更新日期',
    }


class AccountPosition(AttributeObject):
    """账户余额和持仓 - management.产品余额持仓表"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'account_name': '科目名称', 'institution': '机构',
        'security_code': '证券代码', 'security_name': '证券名称',
        'volume': '数量', 'market_price_origin': '原始市场价', 'currency_origin': '原始货币',
        'exchange_rate': '汇率', 'market_price': '市场价', 'market_value': '市值', 'currency': '货币',
    }


class RawAccountPosition(AttributeObject):
    """托管估值表余额和持仓 - management."""


class BankFlow(AttributeObject):
    """银行标准流水 - journal.银行标准流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '银行', 'trade_class': '类型',
        'opposite': '对方', 'subject': '标的', 'trade_amount': '发生金额', 'extra_info': '备注',
        'extra_tag': '程序化标识',
    }

    @property
    def product(self):
        product = self.get_attr('product')
        if product in ('久铭全球丰收1号',):
            return product.replace('久铭', '')
        else:
            return product


class DividendInfo(AttributeObject):
    inner2outer_map = {
        'security_code': '股票代码', 'security_name': '股票名称', 'dividend_mode': '派息方式',
        'cash_dividend': '每股份股利_原始币种', 'dividend_unit': '股份', 'currency': '币种', 'stock_dividend': '每股红股',
        'capital_stock': '每股转增', 'benchmark_date': '股本基准日期', 'announcement_date': '股东大会公告日',
        'registration_date': '股权登记日', 'ex_date': '除权日', 'dividend_date': '派息日', 'listing_date': '红股上市日',
    }

    @property
    def security_code(self):
        return self.get_attr('security_code').upper()

    @property
    def exchange_code(self):
        return self.security_code.split('.')[-1]


class DailyAccountDeposition(AttributeObject):
    """当日账户余额"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'account_type': '账户类型', 'institution': '机构',
        'volume': '余额', 'currency': '币种', 'institution_combined': '券商',
    }

    @property
    def institution_combined(self):
        if self.account_type == '银行活期':
            if self.product == '创新稳健1号':
                return '-'.join([self.account_type, self.institution])
            else:
                return self.account_type
        else:
            if self.institution in ('中信建投', ):
                return '{}({})'.format(self.account_type, self.institution[:4])
            else:
                return '{}({})'.format(self.account_type, self.institution[:2])


class DailyFutureTradeFlow(AttributeObject):
    """当日期货交易流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'security_code': '证券代码', 'trade_direction': '交易方向', 'trade_offset': '交易开平',
        'trade_time': '交易时间', 'trade_price': '成交价格', 'trade_volume': '成交数量', 'trade_tag': '投保'
    }


class DailyMarginTradeFlow(AttributeObject):
    """当日两融交易流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'trade_direction': '交易方向', 'trade_time': '交易时间', 'trade_class': '交易类别', 
        'security_code': '证券代码', 'security_name': '证券名称', 
        'trade_price': '成交价格', 'trade_volume': '成交数量', 'trade_amount': '成交金额', 
    }


class DailyNormalTradeFlow(AttributeObject):
    """当日普通交易流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'trade_time': '交易时间',
        'security_code': '证券代码', 'security_name': '证券名称', 'trade_direction': '交易方向',
        'trade_price': '成交价格', 'trade_volume': '成交数量', 'trade_amount': '成交金额',
        'currency': '币种',
    }


class DailyOptionTradeFlow(AttributeObject):
    """当日期权交易流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'security_code': '证券代码', 'security_name': '证券名称',
        'trade_direction': '交易方向', 'trade_offset': '交易开平',
        'trade_price': '成交价格', 'trade_volume': '成交数量', 'trade_amount': '成交金额',
        'trade_tag': '备兑标志', 'trade_time': '交易时间',
    }


class DailySecurityPosition(AttributeObject):
    """当日证券持仓"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'security_code': '证券代码', 'security_name': '证券名称',
        'volume': '持仓数量', 'volume_type': '持仓类型', 'institution_combined': '券商',
    }

    @property
    def institution_combined(self):
        if '港股通' in self.institution:
            self.institution = self.institution.replace('港股通', '')
            # raise RuntimeError(self.__dict_data__)
        if '两融' in self.institution:
            return '-'.join([self.institution, self.volume_type])
        elif self.product == '开曼全球' and self.institution == '中信香港':
            return '-'.join([self.institution, self.volume_type])
        elif self.institution in ('中信美股', '中信港股', ):
            return '中信SWAP'
        else:
            return self.institution


class EstimatedMarginTradeFlow(AttributeObject):
    """当日两融交易流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'security_code': '证券代码', 'security_name': '证券名称',
        'trade_class': '交易类别', 'trade_time': '交易时间', 'trade_price': '成交价格',
        'trade_volume': '成交数量', 'trade_amount': '成交金额', 'cash_move': '资金发生数',
        'trade_name': '业务名称', 'trade_status': '成交状态',
    }


class EstimatedNormalTradeFlow(AttributeObject):
    """估计普通交易流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'security_code': '证券代码', 'security_name': '证券名称',
        'trade_class': '交易类别', 'trade_time': '交易时间', 'trade_price': '成交价格',
        'trade_volume': '成交数量', 'trade_amount': '成交金额', 'cash_move': '资金发生数',
        'trade_name': '业务名称', 'trade_status': '成交状态',
    }


class EntryAccount(AttributeObject):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'account_name': '科目名称', 'account_code': '科目代码',
        'sub_account': '二级科目', 'base_account': '三级科目', 'note_account': '四级科目',
        'start_net_value': '期初净额',
        'debit_amount_move': '本期借方发生额', 'credit_amount_move': '本期贷方发生额',
        'net_value': '期末净额',
    }


class EntryPosition(AttributeObject):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构',
        'account_code': '科目编号', 'account_name': '科目',
        'security_name': '标的名称', 'security_code': '标的代码',
        'hold_volume': '持有数量', 'contract_multiplier': '合约乘数',
        'weight_average_cost': '加权成本', 'tax_cost': '计税成本', 'total_cost': '成本',
        'close_price': '收盘价', 'market_value': '市值',
    }

    @property
    def exchange_code(self):
        return self.security_code.split('.')[-1].upper()


class EstimatedFutureTradeFlow(AttributeObject):
    """当日期货交易流水"""
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'security_code': '证券代码',
        'trade_class': '交易方向', 'trade_offset': '交易开平',
        'trade_time': '交易时间', 'trade_price': '成交价格',
        'trade_volume': '成交数量', 'trade_amount': '成交金额', 'trade_fee': '交易费用',
        'trade_name': '交易类型', 'trade_tag': '投保'
    }


# class EstimatedMarginTradeFlow(AttributeObject):
#     """当日两融交易流水"""
#     inner2outer_map = {
#         'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
#         'security_code': '证券代码', 'security_name': '证券名称',
#         'trade_class': '交易类别', 'trade_time': '交易时间', 'trade_price': '成交价格',
#         'trade_volume': '成交数量', 'trade_amount': '成交金额', 'cash_move': '资金发生数',
#         'trade_name': '业务名称', 'trade_status': '成交状态',
#     }
# 
# 
# class EstimatedNormalTradeFlow(AttributeObject):
#     """估计普通交易流水"""
#     inner2outer_map = {
#         'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
#         'security_code': '证券代码', 'security_name': '证券名称',
#         'trade_class': '交易类别', 'trade_time': '交易时间', 'trade_price': '成交价格',
#         'trade_volume': '成交数量', 'trade_amount': '成交金额', 'cash_move': '资金发生数',
#         'trade_name': '业务名称', 'trade_status': '成交状态',
#     }


class ExchangeRate(AttributeObject):
    inner2outer_map = {
        'date': '日期', 'field': '汇率代码', 'value': '汇率',
    }


class ManagementFeeReturnRate(AttributeObject):
    inner2outer_map = {
        'investor_product': '产品', 'fund_product': '被投产品', 'rate': '返还费率', 'update_date': '更新日期',
    }


class ProductInfo(AttributeObject):
    inner2outer_map = {
        'index': '产品_id', 'name': '产品简称', 'full_name': '产品全称', 'code': '产品代码', 'mandatory': '托管及外包',
        'management_fee': '管理费率', 'confirm_delay': '确认日', 'table': '归属表格',
    }


class RawFutureAccount(HashableElement):
    inner2outer_map = {
        'hash_key': '流水编号', 'account_type': '账户类型',
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'capital_sum': '当日结存', 'last_capital_sum': '前日结存', 'cash_amount': '可用资金',
        'out_in_cash': '出入金', 'trade_fee': '手续费',
        'market_sum': '保证金占用', 'market_pl': '盯市盈亏', 'realized_pl': '平仓盈亏',
    }


class RawFutureFlow(HashableElement):
    """期货交易流水导入"""
    inner2outer_map = {
        'hash_key': '流水编号', 'product': '产品', 'institution': '机构', 'date': '日期', 'currency': '币种',
        'security_code': '期货合约', 'security_name': '期货品种',
        'trade_class': '交易行为', 'offset': '开平方向', 'investment_tag': '投保',
        'trade_price': '成交价格', 'trade_amount': '成交金额', 'trade_volume': '成交数量',
        'trade_fee': '手续费', 'realize_pl': '平仓盈亏', 'cash_move': '金额变动',
    }


class RawFuturePosition(HashableElement):
    inner2outer_map = {
        'hash_key': '流水编号', 'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'security_name': '期货品种', 'security_code': '期货合约', 'long_position': '买持', 'short_position': '卖持',
        'buy_average_cost': '买均价', 'sell_average_cost': '卖均价',
        'prev_settlement': '昨结算', 'settlement_price': '结算价',
        'market_pl': '盯市盈亏', 'investment_tag': '投保',
        'margin': '保证金占用', 'long_mkv': '多头期权市值', 'short_mkv': '空头期权市值',
    }


class RawMarginAccount(HashableElement):
    inner2outer_map = {
        'account_type': '账户类型', 'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'capital_account': '资金账号', 'customer_id': '客户号',
        'market_sum': '市值总额', 'capital_sum': '资产总额', 'cash_amount': '现金资产',
        'cash_available': '可用资金', 'net_asset': '净资产',
        'total_liability': '融资负债', 'liability_principal': '融资本金', 'liability_amount_interest': '融资应付利息',
        'liability_amount_fee': '融资费用', 'liability_amount_for_pay': '待扣收',
    }


class RawMarginLiability(HashableElement):
    inner2outer_map = {
        'hash_key': '流水编号',
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'contract_date': '合约日期', 'security_name': '证券名称', 'security_code': '证券代码',
        'contract_type': '合约类型', 'contract_volume': '合约数量', 'contract_amount': '合约金额',
        'interest_payable': '应付利息', 'fee_payable': '应付费用', 'payback_date': '截止日',
    }


class RawNormalAccount(HashableElement):
    inner2outer_map = {
        'hash_key': '流水编号', 'account_type': '账户类型',
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'capital_account': '资金账号', 'customer_id': '客户号',
        'market_sum': '市值总额', 'capital_sum': '资产总额', 'cash_amount': '现金资产', 'cash_available': '可用资金',
    }


class RawNormalFlow(HashableElement):
    inner2outer_map = {
        'hash_key': '流水编号',
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'customer_id': '客户号', 'capital_account': '资金账号', 'shareholder_code': '股东代码',
        'security_code': '证券代码', 'security_name': '证券名称',
        'trade_class': '交易类别', 'trade_price': '成交价格',
        'trade_amount': '成交金额', 'trade_volume': '成交数量',
        'cash_move': '资金发生数',
    }


RawMarginFlow = RawNormalFlow


class RawNormalPosition(HashableElement):
    inner2outer_map = {
        'hash_key': '流水编号',
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'customer_id': '客户号', 'cash_account': '资金账号', 'shareholder_code': '证券账号',
        'security_name': '证券名称', 'security_code': '证券代码',
        'hold_volume': '持有数量', 'weight_average_cost': '加权成本', 'total_cost': '总成本',
        'close_price': '收盘价', 'market_value': '市值', 'offset': '多空方向',
    }


RawMarginPosition = RawNormalPosition


class RawOptionAccount(HashableElement):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'capital_sum': '总权益', 'cash_amount': '现金资产', 'market_sum': '期权市值',
        'cash_available': '可用资金',
    }


class RawOptionFlow(HashableElement):
    inner2outer_map = {
        'hash_key': '流水编号', 'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'customer_id': '客户号', 'capital_account': '资金账号',
        'security_code': '合约代码', 'security_name': '合约名称',
        'warehouse_class': '持仓类别', 'trade_class': '交易类型', 'offset': '开平方向',
        'trade_price': '成交价格', 'trade_volume': '成交数量', 'trade_amount': '成交金额',
        'trade_fee': '手续费', 'cash_move': '资金发生数', 'reserve_tag': '备兑标志',
    }


class RawOptionPosition(HashableElement):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'warehouse_class': '持仓类别', 'security_code': '合约代码', 'security_name': '合约名称',
        'hold_volume': '持仓数量', 'average_cost': '均价', 'settlement_price': '结算价',
        'market_value': '市值',
    }


class RawSwapCiticAccount(AttributeObject):
    inner2outer_map = {
        'account_type': '账户类型', 'customer_id': '客户号',
        'product': '产品', 'date': '日期', 'institution': '机构', 'currency': '币种',
        'prepaid_balance_origin': '预付金余额原始货币', 'capital_sum': '盯市金额',
        'capital_sum_origin': '盯市金额原始货币',
        'exchange_rate': '汇率', 'initial_margin_origin': '初始保障金原始货币',
        'notional_principle_origin': '名义本金额原始货币',
        'maintenance_margin_origin': '维持保障金原始货币', 'accumulated_interest_accrued': '累计利息原始货币',
        'accumulated_interest_payed': '应付已付利息原始货币', 'accumulated_withdrawal': '累计支取预付金净额',
        'carryover_balance_origin': '结转预付金余额原始货币', 'available_balance': '可用保障金余额',
        # 'notional_principle': '名义金额', 'swap_value': '合约价值', 'net_value': '净值',
    }

    @property
    def currency(self):
        return self.trade_currency


class RawSwapCiticPosition(AttributeObject):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'trade_currency': '交易货币', 'customer_id': '客户号',
        'security_code': '证券代码', 'security_name': '证券名称',
        'hold_volume': '持有数量', 'offset': '持仓类型', 'contract_multiplier': '标的乘数',
        'total_cost_origin': '成本交易货币', 'close_price_origin': '收盘交易货币',
        'accumulated_realized_profit': '累计实现收益交易货币', 'accumulated_unrealized_profit': '待实现收益交易货币',
        'market_value_origin': '市值交易货币',
    }


class RawSwapHtscAccount(AttributeObject):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'customer_id': '客户号',
        'trade_currency': '交易货币', 'trade_market': '交易市场',
        'exchange_rate': '汇率', 'margin_balance': '保证金余额', 'net_asset': '资产净值',
        'long_position_principle': '多头名义本金', 'short_position_principle': '空头名义本金',
        'long_market_pl': '多头浮动盈亏', 'short_market_pl': '空头浮动盈亏',
        'long_accumulated_interest_payable': '多头累计利息', 'short_accumulated_interest_payable': '空头累计利息',
        'balance_interest_receivable': '保证金累计利息', 'accumulated_loan_fee': '累计借券费',
        'initial_margin': '期初保证金', 'maintenance_margin': '维持保证金',
    }


class RawSwapHtscPosition(AttributeObject):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'institution': '机构', 'customer_id': '客户号',
        'trade_currency': '交易货币', 'trade_market': '交易市场',
        'security_code': '证券代码', 'hold_volume': '持有数量', 'avg_cost': '持仓成本',
        'close_price': '收盘价格', 'market_pl': '浮动盈亏', 'hold_interest': '券息',
    }


class RawTrusteeshipValuation(AttributeObject):
    """托管估值表 -> 原始托管估值表净值表"""
    inner2outer_map = {
        'product': '产品', 'date': '日期',
        'net_value': '单位净值', 'fund_shares': '基金份额', 'net_asset': '净资产',
        'net_value_a': '单位净值A', 'fund_shares_a': '基金份额A', 'net_asset_a': '净资产A',
        'net_value_b': '单位净值B', 'fund_shares_b': '基金份额B', 'net_asset_b': '净资产B',
    }


class RawTrusteeshipValuationSheet(AttributeObject):
    """托管估值表 -> 原始托管估值表"""
    inner2outer_map = {
        'product_code': '产品代码', 'product_name': '产品简称', 'date': '日期',
        'net_value': '单位净值', 'fund_shares': '基金份额', 'net_asset': '净资产',
        'total_asset': '资产总值', 'total_liability': '负债总值',
        'net_value_a': '单位净值A', 'fund_shares_a': '基金份额A', 'net_asset_a': '净资产A',
        'net_value_b': '单位净值B', 'fund_shares_b': '基金份额B', 'net_asset_b': '净资产B',
    }


class RawTrusteeshipValuationDetail(AttributeObject):
    """托管估值表 -> 原始托管估值表明细表"""
    inner2outer_map = {
        'product_code': '产品代码', 'product_name': '产品简称', 'date': '日期',
        'account_code': '科目代码', 'account_name': '科目名称', 'institution': '机构',
        'security_code': '证券代码', 'security_name': '证券名称', 'exchange_rate': '汇率',
        'hold_volume': '数量', 'average_cost': '单位成本', 'total_cost': '本币成本',
        'market_price': '市场价', 'market_value': '本币市值', 'value_changed': '本币估值增值',
        'suspension_info': '停牌信息', 'currency': '货币',
    }


# RawEntryValuation = RawTrusteeshipValuation
class RawEntryValuation(AttributeObject):
    """托管估值表 -> 原始托管估值表净值表"""
    inner2outer_map = {
        'product': '产品', 'date': '日期',
        'net_value': '单位净值', 'fund_shares': '基金份额', 'net_asset': '净资产',
        'total_asset': '资产总值', 'total_liability': '负债总值',
    }


class SecurityInfo(AttributeObject):
    inner2outer_map = {
        'full_code': '合约识别代码', 'code': '合约代码', 'name': '合约简称', 'investment_type': '类型',
        'security_type': '证券类型', 'exchange': '交易所',
    }


class TradeFeeRate(AttributeObject):
    """证券交易费率"""
    inner2outer_map = {
        'update_date': '更新日期', 'product': '产品',  'institution': '券商',
        'security_type': '证券类型', 'fee_type': '费率类型', 'fee_rate': '费率',
        'agreed_payment_day': '港股通组合费扣款日',
    }


class ValueAddedTaxPayable(AttributeObject):
    inner2outer_map = {
        'product': '产品', 'date': '日期', 'tax_type': '增值税类型', 'vat': '预提增值税',
        'vat_building': '预提城建税', 'vat_education': '预提教育费附加', 'vat_local_education': '预提地方教育费附加',
        'total_tax': '预提税金',
    }
