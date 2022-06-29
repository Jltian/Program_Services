# -*- encoding: UTF-8 -*-
import datetime
import os
import shutil

from sqlalchemy.orm.exc import NoResultFound

from jetend import get_logger
from jetend.structures import Sqlite, MailInfo, PopMailWrapper

# from core.MailClassification import classify_mail_contents
# from structures.MailDetail import MailDetail
# from structures.MailReceiveInfo import MailReceiveInfo
# from structures.Tencent import parse_tencent_email_details


class MailLoader(object):
    def __init__(self, config: dict):
        self.log = get_logger(self.__class__.__name__)
        self.db = Sqlite(config['db_path'])
        self.config = config
        self.identify_tag = config['identify_tag']

        # ---- [预处理] ----
        self.db.map(MailInfo, MailInfo.define_sqlalchemy_table(
            self.db.metadata, '{}_MailInfo'.format(self.identify_tag)
        ))
        # self.db.map(MailDetail, MailDetail.define_sqlalchemy_table(self.db.metadata))
        # self.db.map(MailReceiveInfo, MailReceiveInfo.define_sqlalchemy_table(self.db.metadata))

    @staticmethod
    def root_path():
        r_path = os.path.abspath(os.path.dirname(__file__)).split(os.path.sep)
        r_path.pop()
        r_path = os.path.sep.join(r_path)
        return r_path

    def update_mail_data_base(self):
        try:
            start_number = self.db.session.query(MailInfo).order_by(MailInfo.index.desc()).limit(1)[0].index - 200
        except IndexError:
            start_number = - 1
        start_number = max(0, start_number)
        self.mail = PopMailWrapper(
            server_address=self.config['server_address'], user_account=self.config['user_account'],
            user_password=self.config['user_password'],
            server_debug_level=self.config.get('server_debug_level', 0),
        )
        self.mail.login()
        self.mail.fetch_mail_list()
        start_number = min(start_number, self.mail.mail_list[-1].index - 1000)
        # print(self.mail.mail_list[-1].index)
        self.log.info_running('更新邮件原始数据', '{}'.format(datetime.datetime.now()))
        for mail_info in self.mail.mail_list[start_number:]:
            try:
                obj = self.db.session.query(MailInfo).filter_by(index=mail_info.index).one()
                if obj.lsize == mail_info.lsize:
                    pass
                else:
                    self.db.session.delete(obj)
                    self.db.execute("""DELETE FROM `{}_MailInfo` WHERE `index` > '{}';""".format(
                        self.identify_tag, mail_info.index))
                    # self.db.execute("""DELETE FROM `MailDetail` WHERE `index` >= '{}';""".format(mail_info.index))
                    raise NoResultFound('size: {} {} index: {} '.format(obj.lsize, mail_info.lsize, mail_info.index))
            except NoResultFound:
                self.log.debug_running('fetch mail bit', '{}'.format(mail_info.index))
                mail_info = self.mail.fetch_mail_detail(mail_info)
                self.__put_mail_bit__(mail_info.index, mail_info.data_bytes)
                self.db.add(mail_info)
        for mail_index in range(0, start_number - 5000, 1):
            self.__remove_mail_bit__(mail_index)
        self.mail.logout()

    # def initiate_mail_content_cache(self):
    #     max_index = self.db.session.query(MailInfo).order_by(MailInfo.index.desc()).limit(1)[0].index
    #     # min_index = self.db.session.query(MailDetail).order_by(MailDetail.index.desc()).limit(1)[0].index
    #     # for i in range(len(self.db.session.query(MailDetail).all()) - 20, max_index, 1):
    #     for i in range(0, max_index, 1):
    #         self.log.debug_running('convert mail bit', '{}'.format(i + 1))
    #         mail_bit = self.__get_mail_bit__(i + 1)
    #         parsed_dict = parse_tencent_email_details(mail_bit)
    #         mail_detail = MailDetail.init_from(i + 1, parsed_dict=parsed_dict)
    #         for obj_dict in mail_detail.content:
    #             assert isinstance(obj_dict, dict)
    #             if obj_dict['content_disposition'] == 'attachment':
    #                 # 储存附件
    #                 if obj_dict['name'] is None:
    #                     obj_dict['name'] = 'None'
    #                 elif len(obj_dict['name'].replace(' ', '')) == 0:
    #                     obj_dict['name'] = 'NoName'
    #                 else:
    #                     pass
    #                 self.__put_mail_cache__(i + 1, obj_dict['name'], obj_dict['data'])
    #             elif obj_dict['content_disposition'] in (None, 'inline'):
    #                 if obj_dict.get('data', None) is None:
    #                     pass
    #                 elif obj_dict.get('content_type', '').startswith('image'):
    #                     pass
    #                 else:
    #                     if len(obj_dict.get('data', '')) > 0:
    #                         self.__put_mail_text__(i + 1, obj_dict['data'])
    #                     else:
    #                         pass
    #             else:
    #                 raise NotImplementedError('{}'.format(obj_dict))

    # def update_mail_content_cache(self):
    #     self.log.info_running('更新邮件缓存数据', '{}'.format(datetime.datetime.now()))
    #     max_index = self.db.session.query(MailInfo).order_by(MailInfo.index.desc()).limit(1)[0].index
    #     # min_index = self.db.session.query(MailDetail).order_by(MailDetail.index.desc()).limit(1)[0].index
    #     for i in range(len(self.db.session.query(MailDetail).all()) - 300, max_index, 1):
    #     # for i in range(0, max_index, 1):
    #         try:
    #             self.db.session.query(MailDetail).filter_by(index=i + 1).one()
    #         except NoResultFound:
    #             self.log.debug_running('convert mail bit', '{}'.format(i + 1))
    #             self.__remove_mail_cache__(i + 1)
    #             mail_bit = self.__get_mail_bit__(i + 1)
    #             parsed_dict = parse_tencent_email_details(mail_bit)
    #             mail_detail = MailDetail.init_from(i + 1, parsed_dict=parsed_dict)
    #             for obj_dict in mail_detail.content:
    #                 assert isinstance(obj_dict, dict)
    #                 if obj_dict['content_disposition'] == 'attachment':
    #                     # 储存附件
    #                     if obj_dict['name'] is None:
    #                         obj_dict['name'] = 'None'
    #                     elif len(obj_dict['name'].replace(' ', '')) == 0:
    #                         obj_dict['name'] = 'NoName'
    #                     else:
    #                         pass
    #                     self.__put_mail_cache__(i + 1, obj_dict['name'], obj_dict['data'])
    #                 elif obj_dict['content_disposition'] in (None, 'inline'):
    #                     if obj_dict.get('data', None) is None:
    #                         pass
    #                     elif obj_dict.get('content_type', '').startswith('image'):
    #                         pass
    #                     else:
    #                         if len(obj_dict.get('data', '')) > 0:
    #                             try:
    #                                 self.__put_mail_text__(i + 1, obj_dict['data'])
    #                             except TypeError:
    #                                 pass
    #                         else:
    #                             pass
    #                 else:
    #                     raise NotImplementedError('{}'.format(obj_dict))
    #             self.db.add(mail_detail)
    #     for i in range(0, max_index - 8000, 1):
    #         self.__remove_mail_cache__(i + 1)

    def __remove_mail_cache__(self, mail_index: int):
        mail_cache_path = os.path.join(self.config['mail_content_path'], str(mail_index))
        if not os.path.exists(mail_cache_path):
            return
        for m_root, m_folder_list, m_file_list in os.walk(mail_cache_path):
            for file in m_file_list:
                os.remove(os.path.join(m_root, file))
        os.removedirs(mail_cache_path)

    def __remove_mail_bit__(self, name):
        if isinstance(name, str):
            if name.endswith('mb'):
                file_name = name
            else:
                file_name = '.'.join([name, 'mb'])
        elif isinstance(name, int):
            file_name = '{}.mb'.format(name)
        else:
            raise NotImplementedError('{} {}'.format(type(name), name))
        if os.path.exists(os.path.join(self.config['mail_bit_path'], file_name)):
            os.remove(os.path.join(self.config['mail_bit_path'], file_name))

    def __put_mail_bit__(self, name, mail_bit: bytes):
        if isinstance(name, str):
            if name.endswith('mb'):
                file_name = name
            else:
                file_name = '.'.join([name, 'mb'])
        elif isinstance(name, int):
            file_name = '{}.mb'.format(name)
        else:
            raise NotImplementedError('{} {}'.format(type(name), name))
        bit_out = open(os.path.join(self.config['mail_bit_path'], file_name), 'wb')
        bit_out.write(mail_bit)
        bit_out.close()

    def __get_mail_bit__(self, name):
        if isinstance(name, str):
            if name.endswith('mb'):
                file_name = name
            else:
                file_name = '.'.join([name, 'mb'])
        elif isinstance(name, int):
            file_name = '{}.mb'.format(name)
        else:
            raise NotImplementedError('{} {}'.format(type(name), name))
        bit_in = open(os.path.join(self.config['mail_bit_path'], file_name), 'rb')
        bit_content = bit_in.read()
        bit_in.close()
        return bit_content

    def __put_mail_cache__(self, mail_index: int, file_name: str, cache_bit: bytes):
        os.makedirs(os.path.join(self.config['mail_content_path'], str(mail_index)), exist_ok=True)
        file_name = file_name.replace('\t', '').replace('\\', '').replace(':', '').replace('/', '')
        bit_out = open(os.path.join(self.config['mail_content_path'], str(mail_index), file_name), 'wb')
        bit_out.write(cache_bit)
        bit_out.close()

    def __put_mail_text__(self, mail_index: int, text: str, encoding='gb18030'):
        os.makedirs(os.path.join(self.config['mail_content_path'], str(mail_index)), exist_ok=True)
        if os.path.exists(os.path.join(self.config['mail_content_path'], str(mail_index), '__main__.txt')):
            text_out = open(os.path.join(
                self.config['mail_content_path'], str(mail_index), '__main__.txt'
            ), 'a', encoding=encoding)
            try:
                text_out.write(text)
            except UnicodeEncodeError as u_error:
                print(text)
                raise u_error
            except TypeError:
                if isinstance(text, bytes):
                    text_out.write(text.decode(encoding='gb18030', errors='ignore'))
                else:
                    raise TypeError(' write() argument must be str, not {}'.format(type(text)))
            text_out.close()
        else:
            text_out = open(os.path.join(
                self.config['mail_content_path'], str(mail_index), '__main__.txt'
            ), 'w', encoding=encoding)
            try:
                text_out.write(text)
            except UnicodeEncodeError as u_error:
                print(text)
                raise u_error
            text_out.close()

    def __get_mail_text__(self, mail_index: int, encoding='gb18030'):
        assert os.path.exists(
            os.path.join(self.config['mail_content_path'], str(mail_index), '__main__.txt')
        ), str(mail_index)
        text_in = open(os.path.join(
            self.config['mail_content_path'], str(mail_index), '__main__.txt'
        ), 'r', encoding=encoding)
        text = text_in.read()
        text_in.close()
        return text

    # def update_mail_classification(self, range_start: datetime.date = None, range_end: datetime.date = None):
    #     max_index = self.db.session.query(MailDetail).order_by(MailDetail.index.desc()).limit(1)[0].index
    #     # index_range = [int(var) for var in os.listdir(self.config['mail_content_path'])]
    #     # index_range.sort()
    #     # for index in index_range:
    #     self.log.info_running('更新账户分类', '{}'.format(datetime.datetime.now()))
    #     for i in range(max_index, 0, -1):
    #         index = i
    #         try:
    #             mail_detail = self.db.session.query(MailDetail).filter_by(index=index).one()
    #         except NoResultFound:
    #             continue
    #         assert isinstance(mail_detail, MailDetail)
    #         if range_start is not None:
    #             if mail_detail.received_time.date() < range_start:
    #                 return
    #         if range_end is not None:
    #             if mail_detail.received_time.date() > range_end:
    #                 continue
    #         self.log.debug('classify {} {}'.format(index, mail_detail.received_time.strftime('%Y-%m-%d %H:%M:%S')))
    #         mail_detail.content = list()
    #         try:
    #             for tag in os.listdir(os.path.join(self.config['mail_content_path'], str(index))):
    #                 if tag == '__main__.txt':
    #                     mail_detail.main_text = self.__get_mail_text__(index)
    #                 else:
    #                     mail_detail.content.append(tag)
    #         except FileNotFoundError:
    #             continue
    #         file_date_folder = classify_mail_contents(mail_detail, self.db)
    #         for file_name, classified_tuple in file_date_folder.items():
    #             date, folder_name = classified_tuple[0], classified_tuple[1]
    #             if folder_name in ('托管估值表', ):
    #                 date = None
    #             if mail_detail.received_time.hour < 12:
    #                 # raise NotImplementedError('{} - {}'.format(type(mail_detail.received_time), mail_detail.received_time))
    #                 day_part_str = '上午'
    #             elif 12 <= mail_detail.received_time.hour < 15:
    #                 day_part_str = '下午 收盘前'
    #             else:
    #                 day_part_str = '下午 收盘后'
    #             if date is None:    # 估值表
    #                 if folder_name is None:
    #                     target_path = os.path.join(
    #                         self.config['mail_classification_path'],
    #                         '收件日{} {}'.format(mail_detail.received_time.strftime('%Y%m%d'), day_part_str),
    #                     )
    #                 else:
    #                     target_path = os.path.join(
    #                         self.config['mail_classification_path'],
    #                         '收件日{} {}'.format(mail_detail.received_time.strftime('%Y%m%d'), day_part_str),
    #                         folder_name,
    #                     )
    #             else:
    #                 if folder_name is None:
    #                     target_path = os.path.join(
    #                         self.config['mail_classification_path'],
    #                         '收件日{} {}'.format(mail_detail.received_time.strftime('%Y%m%d'), day_part_str),
    #                         '久铭产品交割单{}'.format(date.strftime('%Y%m%d')),
    #                     )
    #                 else:
    #                     target_path = os.path.join(
    #                         self.config['mail_classification_path'],
    #                         '收件日{} {}'.format(mail_detail.received_time.strftime('%Y%m%d'), day_part_str),
    #                         '久铭产品交割单{}'.format(date.strftime('%Y%m%d')), folder_name,
    #                     )
    #             if not os.path.exists(target_path):
    #                 os.makedirs(target_path, exist_ok=True)
    #             if os.path.exists(os.path.join(target_path, file_name)):
    #                 pass
    #             else:
    #                 shutil.copy(os.path.join(self.config['mail_content_path'], str(index), file_name), target_path)
    #                 self.log.debug('copied {}'.format(os.path.join(target_path, file_name)))


if __name__ == '__main__':
    import pickle

    # # 使用POP获取邮件数据
    # settings = {
    #     'server_debug_level': 0,
    #     'mail_bit_path': r'D:\停用邮件账户数据备份\刘融 - 邮件POP二进制缓存',
    #     # 'mail_content_path': r'W:\估值专用邮箱数据\邮件解码数据缓存',
    #     # 'mail_classification_path': r'W:\估值专用邮箱数据\邮件账户分类缓存',
    #     'identify_tag': 'LiuRong',
    #     'db_path': r'D:\离职员工邮件数据备份\mails.db',
    # }
    # loader = MailLoader(settings)
    # # loader.initiate_mail_content_cache()
    # loader.update_mail_data_base()

    from core.ImapLoader import ImapLoader
    SINCE_DATE = None
    # SINCE_DATE = datetime.date.today() - datetime.timedelta(days=5)
    settings = {
        'mail_bit_path': r'D:\MassCacheDir\停用邮件账户数据备份\刘融 - 邮件IMAP二进制缓存',
        'mail_content_path': r'D:\MassCacheDir\停用邮件账户数据备份\邮件IMAP解码数据缓存',
        # 'mail_classification_path': r'D:\链接-久铭估值专用邮箱账户分类',
        'mail_db': r'D:\MassCacheDir\停用邮件账户数据备份\ImapLiuRong.db',
    }
    settings.update({
        'server_address': 'pop.exmail.qq.com',
        'user_account': 'liurong@jiumingfunds.com',
        'user_password': 'Lr19900311',
        # 'server_debug_level': 0,
    })
    loader = ImapLoader(settings)
    # iter_date = datetime.date(2016, 1, 1)
    # while iter_date <= datetime.date.today():
    #     loader.log.info('searching date {}'.format(iter_date))
    #     loader.update_mail_data_base(
    #         # since_date=SINCE_DATE,
    #         on_date=iter_date,
    #     )
    #     iter_date += datetime.timedelta(days=1)
    loader.update_mail_data_base(
        since_date=SINCE_DATE,
        # on_date=datetime.date(2019, 10, 20),
        # skip_folder=(
        #     '&UXZO1mWHTvZZOQ-/&Z05myGOog1BP4Q-',
        #     '&UXZO1mWHTvZZOQ-/2017&XnRTi1tY-',
        #     '&UXZO1mWHTvZZOQ-/2018&XnRTi1tY-',
        #     'Drafts',
        #     'INBOX',
        #     'Junk',
        # )
    )
    # loader.update_mail_content_cache()
    # loader.update_mail_classification(
    #     folder_tag='久铭',
    #     range_start=SINCE_DATE,
    #     # range_end=datetime.date(2019, 9, 6),
    # )
