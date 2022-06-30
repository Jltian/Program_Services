# -*- encoding: UTF-8 -*-
import os
import datetime
import shutil

from sheets.Elements import AccountClass, BaseInfo
from utils.Constants import *

from jetend.DataCheck import *


def get_summary_result(date: datetime.date):
    from core.Environment import Environment
    from structures import DataList
    from sheets.entry.Account import EntryAccount
    from utils.Constants import DataBaseName
    env = Environment.get_instance()

    acc_list = DataList.from_pd(
        EntryAccount,
        env.data_base.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM `{}` WHERE `日期` = '{}';""".format('会计科目余额表', date)
        )
    )
    assert isinstance(acc_list, DataList)

    # out_folder = os.path.expanduser(os.path.join('~', 'Downloads', '科目余额表 {} 分级合并'.format(str(date))))
    out_folder = r'D:\Downloads\科目余额表 {} 分级合并'.format(str(date))
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    # 一级科目合并表
    for product, sub_acc_list in acc_list.group_by('product').items():
        out_acc_list = DataList(EntryAccount)
        assert isinstance(sub_acc_list, DataList)
        for account_name, sub_sub_acc_list in sub_acc_list.group_by('account_name').items():
            assert isinstance(sub_sub_acc_list, DataList)
            out_acc_list.append(EntryAccount(
                product=product, date=date, account_name=account_name,
                start_net_value=sub_sub_acc_list.sum_attr('start_net_value'),
                debit_amount_move=sub_sub_acc_list.sum_attr('debit_amount_move'),
                credit_amount_move=sub_sub_acc_list.sum_attr('credit_amount_move'),
                net_value=sub_sub_acc_list.sum_attr('net_value')
            ))
        out_acc_list.to_csv(os.path.join(out_folder, '{} 合并至一级科目.csv'.format(product)), encoding='gb18030')
    # 二级科目合并表
    for product, sub_acc_list in acc_list.group_by('product').items():
        out_acc_list = DataList(EntryAccount)
        assert isinstance(sub_acc_list, DataList)
        for account_name, sub_sub_acc_list in sub_acc_list.group_by('account_name').items():
            assert isinstance(sub_sub_acc_list, DataList)
            for sub_account, base_acc_list in sub_sub_acc_list.group_by('sub_account').items():
                assert isinstance(base_acc_list, DataList)
                out_acc_list.append(EntryAccount(
                    product=product, date=date, account_name=account_name,
                    sub_account=sub_account,
                    start_net_value=base_acc_list.sum_attr('start_net_value'),
                    debit_amount_move=base_acc_list.sum_attr('debit_amount_move'),
                    credit_amount_move=base_acc_list.sum_attr('credit_amount_move'),
                    net_value=base_acc_list.sum_attr('net_value')
                ))
        out_acc_list.to_csv(os.path.join(out_folder, '{} 合并至二级科目.csv'.format(product)), encoding='gb18030')
    # 三级科目合并表
    for product, sub_acc_list in acc_list.group_by('product').items():
        out_acc_list = DataList(EntryAccount)
        assert isinstance(sub_acc_list, DataList)
        for account_name, sub_sub_acc_list in sub_acc_list.group_by('account_name').items():
            assert isinstance(sub_sub_acc_list, DataList)
            for sub_account, base_acc_list in sub_sub_acc_list.group_by('sub_account').items():
                assert isinstance(base_acc_list, DataList)
                for sub_sub_account, sub_base_ac_list in base_acc_list.group_by('base_account').items():
                    assert isinstance(sub_base_ac_list, DataList)
                    out_acc_list.append(EntryAccount(
                        product=product, date=date, account_name=account_name,
                        sub_account=sub_account, base_account=sub_sub_account,
                        start_net_value=sub_base_ac_list.sum_attr('start_net_value'),
                        debit_amount_move=sub_base_ac_list.sum_attr('debit_amount_move'),
                        credit_amount_move=sub_base_ac_list.sum_attr('credit_amount_move'),
                        net_value=sub_base_ac_list.sum_attr('net_value')
                    ))
        out_acc_list.to_csv(os.path.join(out_folder, '{} 合并至三级科目.csv'.format(product)), encoding='gb18030')
    for product, sub_acc_list in acc_list.group_by('product').items():
        sub_acc_list.to_csv(os.path.join(out_folder, '{} 完整四级科目.csv'.format(product)), encoding='gb18030')


def get_period_summary_result(product: str, period_start: datetime.date, period_end: datetime.date, out_folder: str):
    from core.Environment import Environment
    from structures import DataList
    from sheets.entry.Account import EntryAccount
    from utils.Constants import DataBaseName
    env = Environment.get_instance()

    # acc_list = DataList.from_pd(
    #     EntryAccount,
    #     env.data_base.read_pd_query(
    #         DataBaseName.management,
    #         """SELECT * FROM `{}` WHERE `日期` = '{}';""".format('会计科目余额表', date)
    #     )
    # )
    acc_list = deploy_entry_account(product, period_start, period_end, output_path='')
    acc_list = DataList.from_pd(EntryAccount, acc_list.to_pd())
    # assert isinstance(acc_list, DataList)

    # out_folder = os.path.expanduser(os.path.join('~', 'Downloads', '科目余额表 {} 分级合并'.format(str(date))))
    out_folder = os.path.join(out_folder, '科目余额表 {} {} 分级合并'.format(period_start, period_end))
    # out_folder = r'D:\Downloads\科目余额表 {} 分级合并'.format(str(date))
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    # 一级科目合并表
    for product, sub_acc_list in acc_list.group_by('product').items():
        out_acc_list = DataList(EntryAccount)
        assert isinstance(sub_acc_list, DataList)
        for account_name, sub_sub_acc_list in sub_acc_list.group_by('account_name').items():
            assert isinstance(sub_sub_acc_list, DataList)
            out_acc_list.append(EntryAccount(
                product=product, date=period_end, account_name=account_name,
                start_net_value=sub_sub_acc_list.sum_attr('start_net_value'),
                debit_amount_move=sub_sub_acc_list.sum_attr('debit_amount_move'),
                credit_amount_move=sub_sub_acc_list.sum_attr('credit_amount_move'),
                net_value=sub_sub_acc_list.sum_attr('net_value')
            ))
        out_acc_list.to_csv(os.path.join(out_folder, '{} 合并至一级科目.csv'.format(product)), encoding='gb18030')
    # 二级科目合并表
    for product, sub_acc_list in acc_list.group_by('product').items():
        out_acc_list = DataList(EntryAccount)
        assert isinstance(sub_acc_list, DataList)
        for account_name, sub_sub_acc_list in sub_acc_list.group_by('account_name').items():
            assert isinstance(sub_sub_acc_list, DataList)
            for sub_account, base_acc_list in sub_sub_acc_list.group_by('sub_account').items():
                assert isinstance(base_acc_list, DataList)
                out_acc_list.append(EntryAccount(
                    product=product, date=period_end, account_name=account_name,
                    sub_account=sub_account,
                    start_net_value=base_acc_list.sum_attr('start_net_value'),
                    debit_amount_move=base_acc_list.sum_attr('debit_amount_move'),
                    credit_amount_move=base_acc_list.sum_attr('credit_amount_move'),
                    net_value=base_acc_list.sum_attr('net_value')
                ))
        out_acc_list.to_csv(os.path.join(out_folder, '{} 合并至二级科目.csv'.format(product)), encoding='gb18030')
    # 三级科目合并表
    for product, sub_acc_list in acc_list.group_by('product').items():
        out_acc_list = DataList(EntryAccount)
        assert isinstance(sub_acc_list, DataList)
        for account_name, sub_sub_acc_list in sub_acc_list.group_by('account_name').items():
            assert isinstance(sub_sub_acc_list, DataList)
            for sub_account, base_acc_list in sub_sub_acc_list.group_by('sub_account').items():
                assert isinstance(base_acc_list, DataList)
                for sub_sub_account, sub_base_ac_list in base_acc_list.group_by('base_account').items():
                    assert isinstance(sub_base_ac_list, DataList)
                    out_acc_list.append(EntryAccount(
                        product=product, date=period_end, account_name=account_name,
                        sub_account=sub_account, base_account=sub_sub_account,
                        start_net_value=sub_base_ac_list.sum_attr('start_net_value'),
                        debit_amount_move=sub_base_ac_list.sum_attr('debit_amount_move'),
                        credit_amount_move=sub_base_ac_list.sum_attr('credit_amount_move'),
                        net_value=sub_base_ac_list.sum_attr('net_value')
                    ))
        out_acc_list.to_csv(os.path.join(out_folder, '{} 合并至三级科目.csv'.format(product)), encoding='gb18030')
    for product, sub_acc_list in acc_list.group_by('product').items():
        sub_acc_list.to_csv(os.path.join(out_folder, '{} 完整四级科目.csv'.format(product)), encoding='gb18030')


def change_position_cost(product: str):
    """调整持仓成本"""
    import datetime
    from core.Environment import Environment
    from pandas import read_excel as pd_read_excel
    from structures import DataList
    from sheets.entry.Position import EntryPosition
    from utils.Constants import DataBaseName

    env = Environment.get_instance()

    pd_data = pd_read_excel(
        r'C:\NutStore\我的坚果云\工作\2018年报\2018jm33891非托管估值表.xlsx',
        sheet_name=product,
    )
    position_list = DataList(EntryPosition)
    sql_list = list()
    for i in pd_data.index:
        if pd_data.loc[i, '科目'] not in ('基金投资', '股票投资', '债券投资', '权证投资'):
            continue
        if pd_data.loc[i, '机构'] in ('美股收益互换', '港股收益互换'):
            continue
        print(pd_data.iloc[i, ])
        security_code = pd_data.loc[i, '标的代码']
        if isinstance(security_code, str):
            security_code = security_code.upper()
        this_pos = EntryPosition(
            product=product, date=datetime.date(2018, 12, 31), institution=pd_data.loc[i, '机构'],
            account_name=pd_data.loc[i, '科目'], weight_average_cost=pd_data.loc[i, '加权成本'],
            security_code=security_code, security_name=pd_data.loc[i, '标的名称'],
            hold_volume=pd_data.loc[i, '持有数量'],
            tax_cost=0, close_price=0,
        )
        print('this_pos', this_pos, )
        position_list.append(this_pos)

        data_pos = DataList.from_pd(EntryPosition, env.data_base.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM 会计产品持仓表 
            WHERE 日期 = '2018-12-31' AND 产品 = '{}' AND 标的名称 = '{}' AND 机构 = '{}';""".format(
                this_pos.product, this_pos.security_name, this_pos.institution
            )
        ))
        assert len(data_pos) == 1, str(data_pos)
        data_pos = data_pos[0]
        assert isinstance(data_pos, EntryPosition)
        if data_pos.weight_average_cost != data_pos.tax_cost:
            raise RuntimeError(str(data_pos))
        if data_pos.hold_volume != this_pos.hold_volume:
            raise RuntimeError(str('持仓数量差异：\n{}\n{}'.format(this_pos, data_pos)))
        print('data_pos', data_pos)

        sql = """UPDATE 会计产品持仓表 SET 加权成本 = {}
            WHERE 日期 = '2018-12-31' AND 产品 = '{}' AND 标的名称 = '{}' AND 机构 = '{}'""".format(
                this_pos.weight_average_cost, this_pos.product, this_pos.security_name, this_pos.institution
            )
        sql_list.append(sql)

    inputed = input('modify database ? : ')
    if str(inputed) == 'y':
        for sql in sql_list:
            print(sql)
            env.data_base.execute(DataBaseName.management, sql)


# def load_deploy_accounts():
#     from core.Environment import Environment
#     from pandas import read_excel as pd_read_excel
#     from structures import DataList
#     from sheets.entry.Account import EntryAccount
#     from utils.Constants import DataBaseName, is_valid_str
#
#     env = Environment.get_instance()
#
#     env.data_base.execute(DataBaseName.management, """DELETE FROM 会计科目余额表 WHERE 日期 = '2018-12-31'""")
#
#     pd_data = pd_read_excel(r'C:\NutStore\我的坚果云\工作\2018年底会计科目余额表.xlsx', sheet_name='Sheet2',)
#     pd_data = pd_data.fillna('')
#     # pd_data['二级科目'] = pd_data['二级科目'].fillna('').astype('str')
#
#     accounts_list = DataList.from_pd(EntryAccount, pd_data)
#     for acc in accounts_list:
#         assert isinstance(acc, EntryAccount)
#         acc.debit_amount_move, acc.credit_amount_move = 0.0, 0.0
#         if not is_valid_str(acc.sub_account):
#             acc.sub_account = ''
#         if not is_valid_str(acc.base_account):
#             acc.base_account = ''
#         print(acc.sub_account, type(acc.sub_account), acc)
#
#         env.data_base.execute(DataBaseName.management, acc.form_insert_sql('会计科目余额表'))


def deploy_journal_entry(year: int, month: int):
    from core.Environment import Environment
    from structures import DataList
    from sheets.entry.Entry import JournalEntry
    from utils.Constants import DataBaseName

    env = Environment.get_instance()

    month_journal_list = DataList(JournalEntry)
    iter_date = datetime.date(year=year, month=month, day=1)
    while iter_date.year == year and iter_date.month <= month:
        for obj in DataList.from_pd(JournalEntry, env.data_base.read_pd_query(
            DataBaseName.management,
            """SELECT * FROM 会计分录凭证表 WHERE 日期 = '{}';""".format(iter_date)
        )):
            assert isinstance(obj, JournalEntry)
            # if obj.product != '稳健22号':
            #     continue
            month_journal_list.append(obj)
        iter_date += datetime.timedelta(days=1)

    folder_path = r'C:\Users\Administrator.SC-201606081350\Downloads\{}年{}月'.format(year, month)
    # folder_path = r'Y:\产品会计相关备份\分录凭证\{}年{}月'.format(year, month)
    os.makedirs(folder_path, exist_ok=True)
    for product, sub_list in month_journal_list.group_by('product').items():
        assert isinstance(sub_list, DataList)
        sub_list.to_csv(
            os.path.join(folder_path, '{}年{}月 {} 分录凭证.csv'.format(year, month, product, )),
            encoding='gb18030',
        )
    print('{}年{}月导出成功'.format(year, month))

    env.exit()


def deploy_entry_account(product: str, begin_date: datetime.date, end_date: datetime.date, output_path: str):
    class JournalEntry(AccountClass, BaseInfo):
        """
        录入凭证
        银行存款 - 机构 - 存款性质
        结算备付金 - 账户性质 - 机构
        存出保证金 - 账户性质 - 机构
        股票投资 - 成本/增值 - 机构 - 标的
        债券投资 - 成本/增值 - 机构 - 标的
        基金投资 - 成本/增值 - 机构 - 标的
        权证投资 - 成本/增值 - 机构 - 标的
        收益互换 - 成本/增值 - 机构
        应收股利 - 机构 - 标的
        应收利息 - 利息性质 - 机构 - 标的
        应收申购款 - 对方
        短期借款 - 借款原因 - 机构
        其他应收款 - 收款原因 - 对方
        应付赎回款 - 对方
        应付管理人报酬 - 报酬类别
        应交税费 - 税费类别 - 交税原因 - 标的
        应付利息 - 付息原因 - 对方
        其他应付款 - 付款原因 - 对方
        证券清算款 - 清算原因 - 机构 - 标的
        实收基金
        损益平准金 - 实现情况
        利息收入 - 利息收入原因 - 机构 - 标的
        公允价值变动损益 - 机构 - 标的
        投资收益 - 投资种类 - 机构 - 标的
        管理人报酬 - 报酬类别
        交易费用 - 机构 - 标的
        利息支出 - 利息支出原因 - 机构 - 标的
        其他费用 - 缴费原因 - 机构
        所得税费用 - 交税原因 - 机构 - 标的
        税金及附加 - 税费类别 - 交税原因 - 标的
        """
        inner2outer_map = {
            'entry_no': '凭证号', 'product': '产品', 'date': '日期', 'abstract': '摘要',
            'account_code': '科目编码', 'account_name': '科目名称',
            'account_level_2': '二级科目', 'account_level_3': '三级科目',
            'account_level_4': '四级科目', 'account_level_5': '五级科目',
            'debit_credit': '借贷', 'amount': '金额', 'buy_sell': '买卖', 'volume': '数量',
        }
        __id_count__ = 0

        @property
        def entry_no(self):
            """凭证号"""
            entry_no = str_check(self.get_attr('entry_no'))
            if not is_valid_str(entry_no):
                JournalEntry.__id_count__ = JournalEntry.__id_count__ + 1
                entry_no = '{}-{}-{}'.format(self.date.strftime('%Y%m%d'), self.product, JournalEntry.__id_count__)
                self.set_attr('entry_no', entry_no)
            assert is_valid_str(entry_no), str(self.__dict__)
            return entry_no

        @property
        def institution(self):
            raise RuntimeError('凭证没有institution属性')

        @property
        def abstract(self):
            abstract = str_check(self.get_attr('abstract'))
            assert is_valid_str(abstract), '凭证缺失摘要信息 {}'.format(self.__dict__)
            return abstract

        def update(
                self, abstract='', account_name='', account_level_2='', account_level_3='',
                account_level_4='', account_level_5='', debit_credit='', amount=None,
                buy_sell: str = '', volume: float = None,
        ):
            if is_valid_str(abstract):
                self.set_attr('abstract', str_check(abstract))
            else:
                pass
            self.set_attr('account_name', str_check(account_name))
            self.set_attr('account_level_2', str_check(account_level_2))
            self.set_attr('account_level_3', str_check(account_level_3))
            self.set_attr('account_level_4', str_check(account_level_4))
            self.set_attr('account_level_5', str_check(account_level_5))
            self.set_attr('debit_credit', str_check(debit_credit))
            self.set_attr('amount', float_check(amount))
            self.set_attr('buy_sell', str_check(buy_sell))
            self.set_attr('volume', str_check(volume))
            return self

        @property
        def debit_credit(self):
            debit_credit = str_check(self.get_attr('debit_credit'))
            assert is_valid_str(debit_credit), '凭证缺失借贷方向 {}'.format(self.__dict__)
            assert debit_credit in (SIDE_CREDIT_CN, SIDE_DEBIT_CN), str(self.__dict__)
            return debit_credit

        @property
        def amount(self):
            amount = float_check(self.get_attr('amount'))
            assert is_valid_float(amount), '凭证缺失金额信息 {}'.format(self.__dict__)
            return round(amount, 4)

        @property
        def buy_sell(self):
            buy_sell = str_check(self.get_attr('buy_sell'))
            assert buy_sell in (DIRECTION_BUY, DIRECTION_SELL, EMPTY_STRING), str(self.__dict__)
            return buy_sell

        @property
        def volume(self):
            return round(float_check(self.get_attr('volume')), 2)

        @property
        def account_name(self):
            account_name = str_check(self.get_attr('account_name'))
            assert is_valid_str(account_name), str(self.__dict__)
            return account_name

        @property
        def account_level_2(self):
            account_level_2 = str_check(self.get_attr('account_level_2'))
            # if self.account_name not in ACCOUNT_NAME_LEVEL_ONE:
            #     assert is_valid_str(account_level_2), str(self.__dict__)
            # else:
            #     assert not is_valid_str(account_level_2), '该凭证二级科目必须为空 {}'.format(self.__dict__)
            return account_level_2

        @property
        def account_level_3(self):
            account_level_3 = str_check(self.get_attr('account_level_3'))
            # if self.account_name in ACCOUNT_NAME_LEVEL_THREE or self.account_name in ACCOUNT_NAME_LEVEL_FOUR:
            #     assert is_valid_str(account_level_3), str(self.__dict__)
            # else:
            #     assert not is_valid_str(account_level_3), '该凭证三级科目必须为空 {}'.format(self.__dict__)
            return account_level_3

        @property
        def account_level_4(self):
            account_level_4 = str_check(self.get_attr('account_level_4'))
            # if self.account_name in ACCOUNT_NAME_LEVEL_FOUR:
            #     assert is_valid_str(account_level_4), str(self.__dict__)
            # else:
            #     assert not is_valid_str(account_level_4), '该凭证四级科目必须为空 {}'.format(self.__dict__)
            return account_level_4

        def force_match(self):
            self.set_attr('force_match', True)
            return self

        @property
        def is_force_match(self):
            try:
                return self.get_attr('force_match')
            except AttributeError:
                return False

    # from pandas import read_excel
    from jetend.Constants import DataBaseName
    from jetend.structures import MySQL, List
    # from __depreciated__.EntryAccountList import EntryAccount
    from sheets.entry.Account import EntryAccount
    # from sheets.entry.Entry import JournalEntry
    # from __depreciated__.EntryAccountList import EntryAccountList
    sql_db = MySQL(username='root', passwd='jm3389', server='192.168.1.31', port=3306)
    if begin_date == datetime.date(2019, 6, 1):
        entry_account_list = List.from_pd(EntryAccount, sql_db.read_pd_query(
            DataBaseName.management,
            """
            SELECT * FROM 会计科目余额表
            WHERE 产品 = '{}' AND 日期 = '{}'
            ;""".format(product, begin_date)
        ))
        for acc in entry_account_list:
            assert isinstance(acc, EntryAccount)
            acc.set_attr('debit_amount_move', 0.0)
            acc.set_attr('credit_amount_move', 0.0)
            acc.set_attr('net_value', acc.start_net_value)
    else:
        entry_account_list = List.from_pd(EntryAccount, sql_db.read_pd_query(
            DataBaseName.management,
            """
            SELECT * FROM 会计科目余额表
            WHERE 产品 = '{}' AND 日期 = '{}'
            ;""".format(product, begin_date - datetime.timedelta(days=1))
        ))
        for acc in entry_account_list:
            assert isinstance(acc, EntryAccount)
            acc.init_to_next_date()
    # elif begin_date == datetime.date(2019, 5, 31):
    #     entry_account_list = EntryAccountList.from_pd(EntryAccount, read_excel(
    #         r'C:\NutStore\产品会计相关备份\产品会计科目余额表\调整后会计科目余额表 2019-05-31.xlsx',
    #         sheet_name='Sheet2',
    #     ))
    #     for acc in entry_account_list:
    #         assert isinstance(acc, EntryAccount)
    #         acc.set_attr('start_net_value', acc.net_value)
    #         acc.set_attr('debit_amount_move', 0.0)
    #         acc.set_attr('credit_amount_move', 0.0)
    #         print(acc)
        # entry_account_list = EntryAccountList.from_pd(EntryAccount, sql_db.read_pd_query(
        #     DataBaseName.management,
        #     """
        #     SELECT * FROM 会计科目余额表
        #     WHERE 产品 = '{}' AND 日期 = '{}'
        #     ;""".format(product, begin_date)
        # ))
        # for acc in entry_account_list:
        #     assert isinstance(acc, EntryAccount)
        #     acc.debit_amount_move, acc.credit_amount_move = 0.0, 0.0
        #     acc.net_value = 0.0
    date = begin_date
    while date <= end_date:
        print('processing {} {}'.format(product, date))
        for acc in entry_account_list:
            assert isinstance(acc, EntryAccount)
            acc.set_attr('date', date)
            print(acc)
        daily_entry_list = List.from_pd(JournalEntry, sql_db.read_pd_query(
            DataBaseName.management,
            """
            SELECT * FROM 会计分录凭证表
            WHERE 产品 = '{}' AND 日期 = '{}'
            ;""".format(product, date)
        ))
        # # 三级科目更新方式
        # for entry in daily_entry_list:
        #     assert isinstance(entry, JournalEntry)
        #     acc_list = entry_account_list.find_value_where(
        #         product=entry.product, date=entry.date, account_name=entry.account_name,
        #     )
        #     try:
        #         acc = acc_list.find_value(
        #             sub_account=entry.account_level_2, base_account=entry.account_level_3,
        #         )
        #         acc.update_by(entry)
        #     except ValueError:
        #         if entry.is_force_match is True and abs(entry.amount) > 0.01:
        #             raise NotImplementedError('{}'.format(entry))
        #         else:
        #             acc = EntryAccount(
        #                 product=entry.product, date=entry.date,
        #                 account_name=entry.account_name, sub_account=entry.account_level_2,
        #                 base_account=entry.account_level_3,
        #                 start_net_value=0.0, net_value=0.0, debit_amount_move=0.0, credit_amount_move=0.0,
        #             )
        #             acc.update_by(entry)
        #             entry_account_list.append(acc)
        # 四级科目更新方式
        for entry in daily_entry_list:
            assert isinstance(entry, JournalEntry)
            acc_list = entry_account_list.find_value_where(
                product=entry.product, date=entry.date, account_name=entry.account_name,
            )
            try:
                acc = acc_list.find_value(
                    sub_account=entry.account_level_2, base_account=entry.account_level_3,
                    note_account=entry.account_level_4,
                )
                acc.update_by(entry)
            except ValueError:
                if entry.is_force_match is True and abs(entry.amount) > 0.01:
                    raise NotImplementedError('{}'.format(entry))
                else:
                    acc = EntryAccount(
                        product=entry.product, date=entry.date,
                        account_name=entry.account_name, sub_account=entry.account_level_2,
                        base_account=entry.account_level_3, note_account=entry.account_level_4,
                        start_net_value=0.0, net_value=0.0, debit_amount_move=0.0, credit_amount_move=0.0,
                    )
                    acc.update_by(entry)
                    entry_account_list.append(acc)
        date += datetime.timedelta(days=1)
    # output_path = os.path.expanduser(os.path.join('~', 'Downloads', '{} 科目余额表 {} {}.csv'.format(product, begin_date, end_date)))
    # print(output_path)
    # file_path = os.path.join(output_path, '{} 科目余额表 {}-{}.csv'.format(product, begin_date, end_date))
    # entry_account_list.to_pd().to_csv(file_path, encoding='gbk')
    return entry_account_list


# def copy_to_target_path(source_path: str, target_folder: str):
#     from shutil import copy as shutil_copy
#     os.makedirs(target_folder, exist_ok=True)
#     target_path = os.path.join(target_folder, source_path.split(os.path.sep)[-1])
#     if os.path.exists(target_path):     # 文件已存在跳过
#         return
#     shutil_copy(source_path, target_folder)


# def refolder_journal(begin_date: datetime.date, end_date: datetime.date):
#     # TODO: 根据需要修改
#     source_base_folder = r'C:\NutStore\久铭产品交割单'
#     target_base_folder = r'C:\Users\Administrator.SC-201606081350\Downloads'
#     assert os.path.exists(source_base_folder), '来源路径不存在 {}'.format(source_base_folder)
#     assert os.path.exists(target_base_folder), '目的地路径不存在 {}'.format(target_base_folder)
#     assert begin_date < end_date, '{} >? {}'.format(begin_date, end_date)
#     date = begin_date
#     while date <= end_date:
#         # 获取当日日期对应路径
#         if date.year == 2019:
#             date_path = os.path.join(source_base_folder, '久铭产品交割单{}'.format(date.strftime('%Y%m%d')))
#         else:
#             # TODO: 2017和2018年根据实际情况修改
#             raise NotImplementedError(date)
#
#         if not os.path.exists(date_path):   # 当日对账单不存在，跳过
#             continue
#
#         # 搜索日期路径下文件夹
#         for folder_name in os.listdir(date_path):
#             if folder_name.startswith('.'):   # 跳过隐藏文件
#                 continue
#             if not os.path.isdir(os.path.join(date_path, folder_name)):  # 跳过非文件夹
#                 continue
#             if folder_name == '安信两融账户':
#                 for file_name in os.listdir(os.path.join(date_path, folder_name)):
#                     if file_name.startswith('.'):
#                         continue
#                     # TODO: 根据文件夹内对账单文件用正则表达式获取 【产品】 信息，假设获得当前文件为 久铭2号 的对账单并赋值给变量 product
#                     raise NotImplementedError(folder_name)
#                     target_path = os.path.join(target_base_folder, product, folder_name, date.strftime('%Y%m%d'))
#                     copy_to_target_path(os.path.join(date_path, folder_name, file_name), target_path)
#             else:
#                 # TODO: 根据实际情况增加文件夹
#                 raise NotImplementedError(folder_name)


if __name__ == '__main__':
    pass
    # get_summary_result(datetime.date(2020, 3, 10))
    # load_deploy_accounts()
    # change_position_cost('稳健6号')
    # deploy_journal_entry(2019, 8,)
    for product in (  # 非托管的产品范围
        # '稳健6号', '稳健22号', '全球1号',
        # '久铭2号', '久铭3号',
        # '收益1号',
        # '稳健2号', '稳健3号',
        '稳健15号',
        # '稳健6号', '稳健7号', '稳健8号', '稳健9号','稳健10号',
        # '稳健11号', '稳健12号', '稳健15号', '稳健16号', '稳健17号', '稳健18号', '稳健19号',
        # '稳健21号', '稳健31号', '稳健32号', '稳健33号',
        # '稳利2号',
        # '双盈1号',
    ):
        # deploy_entry_account(
        #     # product, datetime.date(2018, 1, 1), datetime.date(2019, 5, 31),
        #     # product, datetime.date(2019, 6, 1), datetime.date(2019, 12, 31),
        #     # product, datetime.date(2020, 7, 1), datetime.date(2020, 9, 30),
        #     product, datetime.date(2020, 1, 1), datetime.date(2020, 12, 31),
        #     output_path=r'D:\Downloads',
        # )
        get_period_summary_result(
            product=product, period_start=datetime.date(2022, 3, 1), period_end=datetime.date(2022, 4, 25),
            # out_folder=r'D:\Downloads',
            #out_folder=r'D:\Documents',
            out_folder=r'D:\temp_ha',
        )

    # 导出所有流水
    # from jetend.structures import MySQL, List
    # from jetend.Constants import DataBaseName
    #
    # sql_db = MySQL(username='root', passwd='jm3389', server='192.168.1.31', port=3306)
    #
    # product = '稳健9号'
    # out_foler = r'D:\Documents\实习生 - 金融工程\程序文件输出'
    #
    # # from jetend.jmSheets import RawNormalFlow, RawMarginFlow, RawFutureFlow, RawOptionFlow
    # pd_data = sql_db.read_pd_query(
    #     DataBaseName.management, """SELECT * FROM `原始普通流水记录` WHERE `产品` = '{}';""".format(product))
    # pd_data.to_csv(os.path.join(out_foler, '{} 普通流水.csv'.format(product)), encoding='gbk')
    # pd_data = sql_db.read_pd_query(
    #     DataBaseName.management, """SELECT * FROM `原始两融流水记录` WHERE `产品` = '{}';""".format(product))
    # pd_data.to_csv(os.path.join(out_foler, '{} 两融流水.csv'.format(product)), encoding='gbk')
    # pd_data = sql_db.read_pd_query(
    #     DataBaseName.management, """SELECT * FROM `原始期货流水记录` WHERE `产品` = '{}';""".format(product))
    # pd_data.to_csv(os.path.join(out_foler, '{} 期货流水.csv'.format(product)), encoding='gbk')
    # pd_data = sql_db.read_pd_query(
    #     DataBaseName.management, """SELECT * FROM `原始期权流水记录` WHERE `产品` = '{}';""".format(product))
    # pd_data.to_csv(os.path.join(out_foler, '{} 期权流水.csv'.format(product)), encoding='gbk')

    # import re
    # from jetend.Constants import PRODUCT_CODE_NAME_MAP
    # last_path = r'D:\Downloads\非托管估值表表单'
    # target_folder = r'D:\Documents\投资管理部-唐铭\产品估值表副本\非托管产品估值表 久铭'
    # for date_str in os.listdir(last_path):
    #     if '年' in date_str:
    #         continue
    #     for file_name in os.listdir(os.path.join(last_path, date_str)):
    #         if file_name.startswith('~'):
    #             continue
    #         print(os.path.join(last_path, date_str, file_name))
    #         product_code = re.match(r'([0-9a-zA-Z]+)', file_name).group(1)
    #         product = PRODUCT_CODE_NAME_MAP[product_code]
    #         product_target_folder = os.path.join(target_folder, product)
    #         if not os.path.exists(product_target_folder):
    #             os.makedirs(product_target_folder)
    #         if os.path.exists(os.path.join(product_target_folder, file_name)):
    #             continue
    #         try:
    #             shutil.copy(os.path.join(last_path, date_str, file_name), product_target_folder)
    #         except PermissionError:
    #             pass

    # for product in os.listdir(last_path):
    #     if product in ('启元18号', ):
    #         continue
    #     if '静康' in product or '静久康铭' in product:
    #         target_folder = r'D:\Documents\投资管理部-唐铭\产品估值表副本\托管产品估值表 静久'
    #     else:
    #         target_folder = r'D:\Documents\投资管理部-唐铭\产品估值表副本\托管产品估值表 久铭'
    #
    #     if '托管估值表' in os.listdir(os.path.join(last_path, product)):
    #         for file_name in os.listdir(os.path.join(last_path, product, '托管估值表')):
    #             print(os.path.join(last_path, product, '托管估值表', file_name))
    #             if os.path.exists(os.path.join(product_target_folder, file_name)):
    #                 continue
    #             try:
    #                 shutil.copy(os.path.join(last_path, product, '托管估值表', file_name), product_target_folder)
    #             except PermissionError:
    #                 pass
