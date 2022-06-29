# -*- encoding: UTF-8 -*-
import datetime
import re

from sqlalchemy.orm.exc import NoResultFound

from structures.MailDetail import ImapMailDetail
from structures.MailReceiveInfo import MailReceiveInfo

from jetend.structures import List, Sqlite


def __parse_file_postfix__(file_name: str):
    return file_name.lower().split('.')[-1]


def __parse_file_product__(file_name: str, name_range: tuple):
    if '创新' in file_name:
        raise NotImplementedError(file_name)
    elif '静康' in file_name:
        for product in name_range:
            if product in file_name and '静康' in product:
                return product
    else:
        for product in name_range:
            if product in file_name:
                return product
    raise NameError(file_name)


def __exist_key_word__(file_name: str, word_range: tuple):
    for word in word_range:
        try:
            if word in file_name:
                return True
        except TypeError:
            return False
    return False


def __parse_folder_type__(file_name: str):
    if __exist_key_word__(file_name, ('融资', '融券', '信用', '两融', '双融')):
        return '两融'
    elif __exist_key_word__(file_name, ('期权', )):
        return '期权'
    elif __exist_key_word__(file_name, ('期货', )):
        return '期货'
    elif __exist_key_word__(file_name, ('普通', )):
        return '普通'
    else:
        return '普通'


def __parse_file_date__(file_name: str, mail_date: datetime.date):
    end_date = mail_date - datetime.timedelta(days=30)
    date = mail_date + datetime.timedelta(days=4)
    while date >= end_date:
        if str(date.year) in file_name and str(date.month) in file_name and str(date.day) in file_name:
            if date.strftime('%Y%m%d') in file_name:
                return date
            if date.strftime('%Y-%m-%d') in file_name:
                return date
            if date.strftime('%Y/%m/%d') in file_name:
                return date
            if '{}/{}/{}'.format(date.year, date.month, date.day) in file_name:
                return date
            if date.strftime('%Y{}%m{}%d{}').format('年', '月', '日') in file_name:
                return date
            if '{}年{}月{}日'.format(date.year, date.month, date.day) in file_name:
                return date
        else:
            pass
        date -= datetime.timedelta(days=1)
    raise NoResultFound('找不到日期 {}'.format(file_name))


def classify_mail_contents(m_detail: ImapMailDetail, db: Sqlite):
    """排列顺序 (日期，账户类型)"""
    classify_dict = dict()

    if m_detail.message_id is None:
        if m_detail.from_account in ('000qs@citics.com', 'E_signature@citics.com'):
            pass
        else:
            for file_name in m_detail.content:
                classify_dict[file_name] = (None, None)
            return classify_dict
    else:

        if len(m_detail.message_id.replace(' ', '')) == 0 and m_detail.from_account not in (
                '000qs@citics.com', 'E_signature@citics.com',
        ):
            for file_name in m_detail.content:
                classify_dict[file_name] = (None, None)
            return classify_dict

    try:
        mail_from_account = m_detail.from_account.strip()
        ins_list = db.session.query(MailReceiveInfo).filter_by(mail_account=mail_from_account).all()
        assert isinstance(ins_list, list)
        if len(ins_list) == 0:
            ins_list.extend(
                db.session.query(MailReceiveInfo).filter_by(mail_account=mail_from_account.lower()).all())
    except NoResultFound:
        raise NotImplementedError('缺失发件人 {} 数据\n{}'.format(m_detail.from_account, m_detail.__repr__()))

    if len(ins_list) == 1:
        mail_rece = ins_list[0]
        assert isinstance(mail_rece, MailReceiveInfo)
        folder_type_subject = __parse_folder_type__(m_detail.subject)
        try:
            date_subject = __parse_file_date__(m_detail.subject, m_detail.received_time.date())
        except NoResultFound:
            date_subject = None
        for file_name in m_detail.content:
            try:
                date_file = __parse_file_date__(file_name, m_detail.received_time.date())
            except NoResultFound:
                if date_subject is None:
                    if mail_rece.institution in ('手动分类', '托管估值表', '未知数据', '浦睿1号', '清算数据'):
                        date_file = None
                    else:
                        date_file = None
                        # raise RuntimeError('{}\n{}'.format(file_name, m_detail.__repr__()))
                else:
                    date_file = date_subject
            if folder_type_subject != '普通':
                folder_type = folder_type_subject
            else:
                folder_type = __parse_folder_type__(file_name)
            if mail_rece.institution[-2:] in ('普通', '两融', '期货', '期权'):
                folder_name = '{}账户'.format(mail_rece.institution)
                try:
                    if folder_type == '两融':
                        try:
                            assert '融资' in folder_name or '两融' in folder_name, '{} {} {}\n{}'.format(
                                folder_type, folder_name, file_name, m_detail.__repr__())
                        except AssertionError:
                            folder_name = '手动分类'
                    else:
                        # assert folder_type in folder_name, '发件人 MailReceInfo 可能存在缺失 {} {} {}\n{}'.format(
                        #     folder_type, folder_name, file_name, m_detail.__repr__())
                        pass
                except AssertionError as a_name_error:
                    if mail_rece.institution in ('永安期货', '建信期货', '长江期货', '安信期货', ):
                        pass
                    else:
                        raise a_name_error
            else:
                folder_name = mail_rece.institution
            classify_dict[file_name] = (date_file, folder_name)
    elif len(ins_list) > 1:
        folder_type_subject = __parse_folder_type__(m_detail.subject)
        try:
            date_subject = __parse_file_date__(m_detail.subject, m_detail.received_time.date())
        except NoResultFound:
            date_subject = None
        for file_name in m_detail.content:
            try:
                date_file = __parse_file_date__(file_name, m_detail.received_time.date())
            except NoResultFound:
                if date_subject is None:
                    date_file = datetime.date.today()
                else:
                    date_file = date_subject
                # assert date_subject is not None, '{}\n{}'.format(file_name, m_detail.__repr__())
            if folder_type_subject != '普通' and '普通' not in m_detail.subject:
                folder_type = folder_type_subject
            else:
                folder_type = __parse_folder_type__(file_name)
            mail_rece = None
            for obj in ins_list:
                if folder_type in obj.institution:
                    mail_rece = obj
            assert isinstance(mail_rece, MailReceiveInfo), '{}\n{}\n{}'.format(folder_type, ins_list, str(m_detail))

            folder_name = '{}账户'.format(mail_rece.institution)
            # assert __parse_folder_type__(file_name) in folder_name, '{}\n{}'.format(file_name, m_detail.__repr__())
            classify_dict[file_name] = (date_file, folder_name)
    else:
       # pass
        raise NotImplementedError('缺失发件人 {} 数据\n{}'.format(m_detail.from_account, ins_list))

    # if m_detail.from_account in ('10000@qq.com', ):
    #     return classify_dict
    #
    # elif m_detail.from_account in (
    #         'cleardata@citics.com',
    # ) and m_detail.received_time.year < 2019:           # 未知数据
    #     for file_name in m_detail.content:
    #         classify_dict[file_name] = (None, '未知数据',)
    #
    # elif m_detail.from_account in ('xtcp@cjsc.com', 'fa@hs.fund', 'hemengjie@jiumingfunds.com'):      # 未知数据
    #     for file_name in m_detail.content:
    #         classify_dict[file_name] = (None, None)
    #
    # elif m_detail.from_account in ('EQ_quant@citics.com', ):    # 未知数据
    #     date_str = re.match(r'Fx已经导入GDMM (\d+-\d+-\d+)', m_detail.subject).group(1)
    #     date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    #     for file_name in m_detail.content:
    #         classify_dict[file_name] = (date, None,)
    #
    # elif m_detail.from_account in ('gz@jingjiukm.com', ):           # 静康行情邮件
    #     if '静久公司' in m_detail.subject:
    #         return classify_dict
    #     else:
    #         raise RuntimeError(m_detail)
    #
    # elif m_detail.from_account in (
    #         'xzyyfw@xyzq.com.cn', 'yywbfa@cmschina.com.cn', 'wbgz@zts.com.cn', 'mqw9360@htsec.com',
    #         'oawbfwyw@message.guosen.com.cn', 'jjtgb_scyx@htsec.com', 'yywb@cmschina.com.cn',
    #         'wbgz@htsc.com', 'zctgsjfs@tg.gtja.com',
    # ):      # 托管估值表
    #     for file_name in m_detail.content:
    #         if '估值表' in file_name or '估值表' in m_detail.subject:
    #             folder_name = '托管估值表'
    #         else:
    #             if __parse_file_postfix__(file_name) not in ('xls', 'xlsx'):
    #                 folder_name = '未知数据'
    #             else:
    #                 raise RuntimeError(file_name)
    #         classify_dict[file_name] = (None, folder_name,)
    #
    # # elif m_detail.from_account in (
    # #         'htzqyyzx01@htsc.com', 'trustdata@csc.com.cn', 'qscgb@tebon.com.cn',
    # # ):    # 清算数据
    # #     for file_name in m_detail.content:
    # #         classify_dict[file_name] = (None, '清算数据',)
    #
    # elif m_detail.from_account in ('zh01@changanfunds.com', ):      # 浦睿1号
    #     assert '浦睿' in m_detail.subject, m_detail.__repr__()
    #     date_str = None
    #     for file_name in m_detail.content:
    #         if '估值表' in file_name:
    #             try:
    #                 date_str = re.match(r'\w+_\w+\d+\w+_(\d+-\d+-\d+)', file_name).group(1)
    #             except AttributeError:
    #                 raise RuntimeError(file_name)
    #         else:
    #             pass
    #     assert date_str is not None, str(m_detail.content)
    #     date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    #     for file_name in m_detail.content:
    #         classify_dict[file_name] = (date, '浦睿1号',)
    #
    # elif m_detail.from_account in (     # 安信
    #     '971281380@qq.com',
    # ):
    #     date_str = re.match(r'[久铭静康]+\d+[号指数]+[^\d]*(\d+)[^\d]+', m_detail.subject).group(1)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '安信{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name, )
    #
    # elif m_detail.from_account in (
    #     'weizih@ctsec.com',
    # ):      # 财通
    #     date_str = re.match(r'(\d+)[久铭稳健]+', m_detail.subject.replace('回复: ', '')).group(1)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '财通{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name,)
    #
    # elif m_detail.from_account in ('zhouwei4@cjsc.com.cn', ):       # 长江
    #     date_str = re.match(r'\d*[久铭稳健]+\d+[号指数]+[^\d]*(\d+)', m_detail.subject).group(1)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '长江{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name,)
    #
    # elif m_detail.from_account in ('zhangjh@tebon.com.cn', 'taochen@tebon.com.cn', ):       # 德邦
    #
    #     for file_name in m_detail.content:
    #         try:
    #             date_str = re.match(r'[久铭创新稳健静康]+\d+[号指数]+[^\d]*(\d+)', file_name).group(1)
    #         except AttributeError:
    #             raise RuntimeError(file_name)
    #         date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #         # assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '德邦{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name,)
    #
    # elif m_detail.from_account in ('qhgsjssjfs@gtjas.com', ):       # 国君期货
    #     year, month, day = re.match(r'国泰君安期货 (\d+)年(\d+)月(\d+)日', m_detail.subject).groups()
    #     date = datetime.date(year=int(year), month=int(month), day=int(day))
    #     assert '期货' in m_detail.subject, str(m_detail)
    #     for file_name in m_detail.content:
    #         file_type = __parse_file_postfix__(file_name)
    #         if file_type == 'rar':
    #             assert date.strftime('%Y%m%d') in file_name, file_name
    #         else:
    #             pass
    #         folder_name = '国君期货账户'
    #         classify_dict[file_name] = (date, folder_name,)
    #
    # elif m_detail.from_account in ('shbdnk@message.guosen.com.cn', ):   # 国信
    #     for file_name in m_detail.content:
    #         file_type = __parse_file_postfix__(file_name)
    #         if file_type == 'rar':
    #             classify_dict[file_name] = (None, '清算数据')
    #         elif file_type == 'xls':
    #             date_str = re.match(r'(\d+)', file_name.split('~')[1].strip()).group(1)
    #             date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #             folder_name = '国信普通账户'
    #             classify_dict[file_name] = (date, folder_name, )
    #
    # elif m_detail.from_account in (     # 海通
    #     'zjw11162@htsec.com',
    # ):
    #     try:
    #         date_str = re.match(r'久铭(\d+)', m_detail.subject).group(1)
    #     except AttributeError:
    #         raise RuntimeError(m_detail.subject)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         # assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '海通{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name,)
    #
    # elif m_detail.from_account in (  # 华泰
    #     'qiepengju@htsc.com', 'liuyang@htsc.com', 'shenxiaomeng@htsc.com',
    # ):
    #     try:
    #         date_str = re.match(r'[久铭稳健]+\d+[号指数]+(\d+)', m_detail.subject).group(1)
    #     except AttributeError:
    #         raise RuntimeError(m_detail.subject)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '华泰{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name, )
    #
    # elif m_detail.from_account in ('jsfkb-zd@ccbfutures.com', ):    # 建信期货
    #     try:
    #         date_str = re.match(r'[久铭稳健]+\d+[号指数]+_\d+_(\d+)', m_detail.subject).group(1)
    #     except AttributeError:
    #         raise RuntimeError(m_detail.subject)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         assert '建信期货' in m_detail.main_text, str(m_detail)
    #         folder_name = '建信期货账户'
    #         classify_dict[file_name] = (date, folder_name, )
    #
    # elif m_detail.from_account in ('yeqiong@swhysc.com', ):     # 申万
    #     try:
    #         date_str = m_detail.subject[-8:]
    #     except AttributeError:
    #         raise RuntimeError(m_detail.subject)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '申万{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name,)
    #
    # elif m_detail.from_account in ('zhanxiang@xyzq.com.cn', ):      # 兴业
    #     date_str = re.match(r'\w+\+\w+\+(\d+)', m_detail.subject).group(1)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         # assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '兴业{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name,)
    #
    # elif m_detail.from_account in ('js@yaqh.com', ):    # 永安
    #     try:
    #         date_str = re.match(r'[久铭收益]+\d+号(\d+).rar', m_detail.subject).group(1)
    #     except AttributeError:
    #         raise RuntimeError(m_detail.subject)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     assert '永安期货' in m_detail.main_text, str(m_detail)
    #     for file_name in m_detail.content:
    #         assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '永安期货账户'
    #         classify_dict[file_name] = (date, folder_name, )
    #
    # elif m_detail.from_account in ('duming@cmschina.com.cn', ):     # 招商数据
    #     if '清算数据' in m_detail.subject:
    #         date_str = re.match(r'[久铭稳健]+\d+[号清算数据]+(\d+)', m_detail.subject).group(1)
    #     else:
    #         date_str = re.match(r'(\d+)', m_detail.subject).group(1)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         assert __parse_file_postfix__(file_name) == 'rar', str(m_detail)
    #         folder_name = '清算数据'
    #         classify_dict[file_name] = (date, folder_name,)
    #
    # elif m_detail.from_account in ('cicc_ops_mail@cicc.com.cn', ):      # 中金
    #     try:
    #         year, month, day = re.match(r'(\d+)年(\d+)月(\d+)日', m_detail.subject.split('-')[-1].strip()).groups()
    #     except AttributeError:
    #         raise RuntimeError(m_detail.subject)
    #     date = datetime.date(int(year), int(month), int(day))
    #     for file_name in m_detail.content:
    #         assert date.strftime('%Y%m%d') in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '中金{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name, )
    #
    # elif m_detail.from_account in (  # 中泰
    #         'yuanjiang@zts.com.cn',
    # ):
    #     try:
    #         date_str = re.match(r'[久铭稳健]+\d+[号指数]+[^\d]*(\d+)', m_detail.subject).group(1)
    #     except AttributeError:
    #         raise RuntimeError(m_detail.subject)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         assert date_str in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '中泰{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name, )
    #
    # elif m_detail.from_account in (
    #         '006khb@citics.com', 'fangss@citics.com', 'xhyu@citics.com', 'shfgs526@citics.com',
    # ):  # 中信
    #     try:
    #         assert m_detail.subject.count('_') == 1, str(m_detail)
    #         date_str = m_detail.subject.strip().split('_')[1]
    #         # date_str = re.match(r'[^_]_(\d+)', m_detail.subject).group(1)
    #     except AttributeError:
    #         raise RuntimeError(m_detail.subject)
    #     date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
    #     for file_name in m_detail.content:
    #         assert date.strftime('%Y%m%d') in file_name, '{} {}'.format(file_name, m_detail)
    #         folder_name = '中信{}账户'.format(__parse_folder_type__(file_name))
    #         classify_dict[file_name] = (date, folder_name, )
    #
    # elif m_detail.from_account in ('000qs@citics.com', 'E_signature@citics.com', ):       # 中信 收益互换
    #     try:
    #         date_str = re.match(r'(\d+-\d+-\d+)\W+\w+', m_detail.subject.strip()).group(1)
    #     except AttributeError:
    #         raise NotImplementedError(m_detail.subject)
    #     date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    #     for file_name in m_detail.content:
    #         assert date.strftime('%Y%m%d') in file_name, '{} {}'.format(file_name, m_detail)
    #         if 'USD' in file_name:
    #             folder_name = '中信美股'
    #         elif 'HKD' in file_name:
    #             folder_name = '中信港股'
    #         else:
    #             raise RuntimeError(file_name)
    #         classify_dict[file_name] = (date, folder_name, )
    #
    # else:
    #     raise NotImplementedError(m_detail.__repr__())

    return classify_dict
