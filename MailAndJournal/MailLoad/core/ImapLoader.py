# -*- encoding: UTF-8 -*-
import datetime
import imaplib
import os
import re
import shutil

from sqlalchemy.orm.exc import NoResultFound

from jetend import get_logger
from jetend.structures import Sqlite
from jetend.structures import MySQL

from core.MailClassification import classify_mail_contents
from structures.MailDetail import ImapMailDetail
from structures.MailReceiveInfo import MailReceiveInfo
from structures.Tencent import parse_tencent_email_details


class ImapMailInfo(object):
    """
    用于临时保存IMAP邮件列表中信息的类
    """

    def __init__(self, mail_box: str, uid: int):
        self.mail_box = mail_box
        self.uid = uid
        self.data_bytes = None

    @classmethod
    def define_sqlalchemy_table(cls, meta):
        from sqlalchemy import MetaData, Table, Column, String, Integer
        assert isinstance(meta, MetaData)
        return Table(
            cls.__name__, meta,
            Column('mail_box', String, nullable=False, primary_key=True),
            Column('uid', Integer, nullable=False, primary_key=True),
        )


class ImapLoader(object):
    def __init__(self, config: dict):
        self.no_bills_list = ['mailrecall_admin@qq.com', '2637472262@qq.com', 'lizhihao802@126.com', 'newservice@totodi.com','cwjz@tg.gtja.com','zhangyingyong@xyzq.com.cn','cr14370@htsec.com'
                              'custobackup@citics.com','fj@jingjiukm.com','Jonathan.Lam@vistra.com','gzzy@jingjiukm.com','cjsc_tgjs@vip.163.com','xztgzhpt@xyzq.com.cn','cpsj1@cjsc.com',
                              'gxtggzhs@guosen.com.cn','Marco.Lee@vistra.com ','wenwen023807@gtjas.com',' youxiaojun_sh@chinastock.com.cn','czz@jiumingfunds.com','ops-otc@gtjaqh.com']  # waves
        self.log = get_logger(self.__class__.__name__)
        self.db = Sqlite(config.get('mail_db', os.path.join(self.root_path(), 'mails.db')))
        self.config = config

        # ---- [预处理] ----
        self.db.map(ImapMailInfo, ImapMailInfo.define_sqlalchemy_table(self.db.metadata))
        self.db.map(ImapMailDetail, ImapMailDetail.define_sqlalchemy_table(self.db.metadata))
        self.db.map(MailReceiveInfo, MailReceiveInfo.define_sqlalchemy_table(self.db.metadata))

        self.mail = imaplib.IMAP4_SSL(host='imap.exmail.qq.com', port=993, )

    @staticmethod
    def root_path():
        r_path = os.path.abspath(os.path.dirname(__file__)).split(os.path.sep)
        r_path.pop()
        r_path = os.path.sep.join(r_path)
        return r_path

    def mail_server_login(self):
        # 登录邮箱
        self.mail = imaplib.IMAP4_SSL(host='imap.exmail.qq.com', port=993, )
        status, data = self.mail.login(user=self.config['user_account'], password=self.config['user_password'])
        assert status == 'OK', 'IMAP登录失败 {} {}'.format(status, data)

    def mail_box_list(self):
        # 获取邮件箱
        status, folders = self.mail.list()
        # raise RuntimeError(str([var.decode('utf7') for var in folders]))
        assert status == 'OK', '获取邮箱失败 {}'.format(status)
        return folders

    def mail_select(self, folder_name: str):
        self.mail.select(folder_name, readonly=True)

    def mail_fetch(self, i, folder_name):
        try:
            self.mail_select(folder_name)
            status, data = self.mail.fetch(str(i).encode(), "UID")
        except imaplib.IMAP4_SSL.abort:
            self.mail_server_login()
            self.mail_select(folder_name)
            status, data = self.mail.fetch(str(i).encode(), "UID")
        assert status == 'OK', '获取邮件ID失败 {} 邮箱 {} 编号 {}'.format(status, folder_name, i)
        return data

    def update_mail_data_base(
            self, since_date: datetime.date = None, on_date: datetime.date = None, skip_folder: tuple = tuple(),
    ):
        if since_date is None and on_date is None:
            search_command = 'ALL'
        elif since_date is None and on_date is not None:
            search_command = 'ON {}'.format(on_date.strftime('%d-%b-%Y'))
        elif since_date is not None and on_date is None:
            search_command = 'SINCE {}'.format(since_date.strftime('%d-%b-%Y'))
        else:
            raise RuntimeError('since_date 和 on_date 不能同时赋值')
        self.log.info_running('更新邮件原始数据', str(datetime.datetime.now()))
        self.mail_server_login()
        folders = self.mail_box_list()
        # 分邮箱获取邮件
        list_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')
        for folder in folders:
            # 获取邮箱信息
            flags, delimiter, folder_name = list_pattern.match(folder.decode()).groups()
            folder_name = folder_name.strip('"')
            if 'NoSelect' in flags:
                continue
            if folder_name in ('Sent Messages', 'Deleted Messages'):
                continue
            if folder_name in skip_folder:
                continue
            self.log.info_running('检查邮箱文件夹 {}'.format(folder_name))
            # 进入邮箱获取邮件
            self.mail_select(folder_name)
            status, data = self.mail.search(None, search_command)
            assert status == 'OK', '搜索邮箱失败 {} 邮箱 {} 命令 {}'.format(status, folder_name, search_command)
            # 获取邮件编号
            msg_id_list = [int(i) for i in data[0].split()]
            # 下载邮件原始数据
            for i in msg_id_list:
                # try:
                #     status, data = self.mail.fetch(str(i).encode(), "UID")
                # except imaplib.IMAP4_SSL.abort:
                #     self.mail_server_login()
                data = self.mail_fetch(i, folder_name)
                try:
                    uid = int(re.match('\d+ \(UID (\d+)\)', data[0].decode()).group(1))
                except AttributeError as a_error:
                    print(data)
                    #raise a_error
                try:
                    obj = self.db.session.query(ImapMailInfo).filter_by(mail_box=folder_name, uid=uid).one()
                except NoResultFound:
                    self.log.debug_running('获取邮件数据 {}'.format(folder_name), str(uid))
                    status, data = self.mail.fetch(str(i).encode(), "(RFC822)")
                    assert status == 'OK', '获取邮件数据失败 {} 邮箱 {} 编号 {}'.format(status, folder_name, i)
                    obj = ImapMailInfo(folder_name, uid)
                    try:
                        obj.data_bytes = data[0][1]
                    except TypeError as t_error:
                        if data == [None]:
                            continue
                        print(data)
                        raise t_error
                    self.__put_mail_bit__(folder_name, uid, obj.data_bytes)  # 把邮件数据以字节流形式输出到如二进制缓存文件下/文件名/54552.mb里头
                try:
                    if obj.data_bytes is None:
                        continue
                    else:
                        self.db.add(obj)  # 这就相当于在查ImapMaliInfo的文件目录和文件名时候没匹配到记录，进了上面的异常，才会进这里
                except AttributeError:
                    continue
        self.mail.logout()

    def update_mail_content_cache(self):
        self.log.info_running('更新邮件缓存数据', '{}'.format(datetime.datetime.now()))
        count_num = 0
        for folder_name in os.listdir(self.config['mail_bit_path']):
            folder_name = folder_name.replace('$$$', '/')
            if folder_name.startswith('.'):
                continue
            for file_name in os.listdir(os.path.join(self.config['mail_bit_path'], folder_name.replace('/', '$$$'))):
                if file_name.startswith('.'):
                    continue
                assert file_name.endswith('.mb'), '{} {}'.format(folder_name, file_name)
                uid = int(file_name.split('.')[0])
                try:
                    # try:
                    mail_detail = self.db.session.query(ImapMailDetail).filter_by(mail_box=folder_name, uid=uid).one()
                    if mail_detail.from_account == 'dbzq_dzd@nesc.cn':
                        print("踩一脚")
                    # except:
                    #     print("准备跳过")
                    #     count_num = count_num + 1
                    #     os.remove(os.path.join(self.config['mail_bit_path'], folder_name.replace('/','$$$'), str(uid)+'.mb'))
                    #     print("删除" + str(count_num) + "次")
                    #     continue

                    # 清理60天前的缓存数据
                    try:
                        if mail_detail.received_time.date() + datetime.timedelta(days=60) < datetime.date.today():
                            self.__remove_mail_bit__(folder_name, uid)
                            self.__remove_mail_cache__(folder_name, uid)
                            self.db.execute(
                                """DELETE FROM `ImapMailInfo` WHERE `mail_box` = '{}' AND `uid` = '{}';""".format(
                                    folder_name, uid))
                            self.db.execute(
                                """DELETE FROM `ImapMailDetail` WHERE `mail_box` = '{}' AND `uid` = '{}';""".format(
                                    folder_name, uid))
                        else:
                            pass
                    except AttributeError:
                        pass
                except NoResultFound:
                    self.log.debug_running('转换邮件数据 {}'.format(folder_name), str(uid))
                    self.__remove_mail_cache__(folder_name, uid)  # 清理本地二进制缓存
                    mail_bit = self.__get_mail_bit__(folder_name, uid)  # 把同名的邮件字节码数据拉过来
                    parsed_dict = parse_tencent_email_details(mail_bit)
                    try:
                        if parsed_dict['flag'] == 'unorder':
                            continue
                    except:
                        pass
                    mail_detail = ImapMailDetail.init_from(folder_name, uid, parsed_dict=parsed_dict)
                    for obj_dict in mail_detail.content:
                        assert isinstance(obj_dict, dict)
                        if obj_dict['content_disposition'] == 'attachment':
                            # 储存附件
                            if obj_dict['name'] is None:
                                obj_dict['name'] = 'None'
                            elif len(obj_dict['name'].replace(' ', '')) == 0:
                                obj_dict['name'] = 'NoName'
                            else:
                                pass
                            self.__put_mail_cache__(folder_name, uid, obj_dict['name'], obj_dict['data'])
                        elif obj_dict['content_disposition'] in (None, 'inline'):
                            if obj_dict.get('data', None) is None:
                                pass
                            elif obj_dict.get('content_type', '').startswith('image'):
                                pass
                            else:
                                if len(obj_dict.get('data', '')) > 0:
                                    try:
                                        self.__put_mail_text__(folder_name, uid, obj_dict['data'])
                                    except TypeError:
                                        pass
                                else:
                                    pass
                        else:
                            raise NotImplementedError('{}'.format(obj_dict))
                    self.db.add(mail_detail)  # 前面没在detail数据库表里查出来，现在把它加进去

    def __remove_mail_bit__(self, folder_name: str, uid: int):
        folder_name = folder_name.replace('/', '$$$')
        name = str(uid)
        if isinstance(name, str):
            if name.endswith('mb'):
                file_name = name
            else:
                file_name = '.'.join([name, 'mb'])
        elif isinstance(name, int):
            file_name = '{}.mb'.format(name)
        else:
            raise NotImplementedError('{} {}'.format(type(name), name))
        if os.path.exists(os.path.join(self.config['mail_bit_path'], folder_name, file_name)):
            os.remove(os.path.join(self.config['mail_bit_path'], folder_name, file_name))

    def __put_mail_bit__(self, folder_name: str, uid: int, mail_bit: bytes):
        folder_name = folder_name.replace('/', '$$$')
        name = str(uid)
        if isinstance(name, str):
            if name.endswith('mb'):
                file_name = name
            else:
                file_name = '.'.join([name, 'mb'])
        elif isinstance(name, int):
            file_name = '{}.mb'.format(name)
        else:
            raise NotImplementedError('{} {}'.format(type(name), name))
        if not os.path.exists(os.path.join(self.config['mail_bit_path'], folder_name)):
            os.makedirs(os.path.join(self.config['mail_bit_path'], folder_name))
        bit_out = open(os.path.join(self.config['mail_bit_path'], folder_name, file_name), 'wb')
        bit_out.write(mail_bit)
        bit_out.close()

    def __get_mail_bit__(self, folder_name: str, uid: int):
        folder_name = folder_name.replace('/', '$$$')
        name = str(uid)
        if isinstance(name, str):
            if name.endswith('mb'):
                file_name = name
            else:
                file_name = '.'.join([name, 'mb'])
        elif isinstance(name, int):
            file_name = '{}.mb'.format(name)
        else:
            raise NotImplementedError('{} {}'.format(type(name), name))
        bit_in = open(os.path.join(self.config['mail_bit_path'], folder_name, file_name), 'rb')
        bit_content = bit_in.read()
        bit_in.close()
        return bit_content

    def __remove_mail_cache__(self, folder_name: str, uid: int):
        folder_name = folder_name.replace('/', '$$$')
        mail_cache_path = os.path.join(self.config['mail_content_path'], folder_name, str(uid))
        if not os.path.exists(mail_cache_path):
            return
        for m_root, m_folder_list, m_file_list in os.walk(mail_cache_path):
            for file in m_file_list:
                os.remove(os.path.join(m_root, file))
        os.removedirs(mail_cache_path)

    def __put_mail_cache__(self, folder_name: str, uid: int, file_name: str, cache_bit: bytes):
        folder_name = folder_name.replace('/', '$$$')
        os.makedirs(os.path.join(self.config['mail_content_path'], folder_name, str(uid)), exist_ok=True)
        file_name = file_name.replace('\t', '').replace('\\', '').replace(':', '').replace('/', '')
        bit_out = open(os.path.join(self.config['mail_content_path'], folder_name, str(uid), file_name), 'wb')
        bit_out.write(cache_bit)
        bit_out.close()

    def __put_mail_text__(self, folder_name: str, mail_index: int, text: str, encoding='gb18030'):
        folder_name = folder_name.replace('/', '$$$')
        os.makedirs(os.path.join(self.config['mail_content_path'], folder_name, str(mail_index)), exist_ok=True)
        if os.path.exists(os.path.join(self.config['mail_content_path'], folder_name, str(mail_index), '__main__.txt')):
            text_out = open(os.path.join(
                self.config['mail_content_path'], folder_name, str(mail_index), '__main__.txt'
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
                self.config['mail_content_path'], folder_name, str(mail_index), '__main__.txt'
            ), 'w', encoding=encoding)
            try:
                text_out.write(text)
            except UnicodeEncodeError as u_error:
                print(text)
                raise u_error
            text_out.close()

    def __get_mail_text__(self, folder_name: str, mail_index: int, encoding='gb18030'):
        folder_name = folder_name.replace('/', '$$$')
        assert os.path.exists(
            os.path.join(self.config['mail_content_path'], folder_name, str(mail_index), '__main__.txt')
        ), str(mail_index)
        text_in = open(os.path.join(
            self.config['mail_content_path'], folder_name, str(mail_index), '__main__.txt'
        ), 'r', encoding=encoding)
        text = text_in.read()
        text_in.close()
        return text

    def update_mail_classification(
            self, folder_tag: str, range_start: datetime.date = None, range_end: datetime.date = None):
        self.log.info_running('更新账户分类', '{}'.format(datetime.datetime.now()))
        mail_detail_list = self.db.session.query(ImapMailDetail).order_by('received_time').all()
        assert isinstance(mail_detail_list, list)
        # mail_detail_list.reverse()
        for mail_detail in mail_detail_list:
            self.log.debug_running('checking {} {}'.format(mail_detail.mail_box, mail_detail.uid))
            assert isinstance(mail_detail, ImapMailDetail)
            try:
                if range_start is not None:
                    if mail_detail.received_time.date() < range_start:
                        continue
                if range_end is not None:
                    if mail_detail.received_time.date() > range_end:
                        continue
            except AttributeError:
                continue
            # 以上筛选出要拉取的指定日期范围内的邮箱文件夹内容 @waves
            if mail_detail.from_account in self.no_bills_list:
                self.log.debug_running('跳过无对账单的邮件')
                continue
            self.log.debug_running('classify {}'.format(mail_detail.mail_box), '{} {}'.format(
                mail_detail.uid, mail_detail.received_time.strftime('%Y-%m-%d %H:%M:%S')
            ))
            disk_folder = mail_detail.mail_box.replace('/', '$$$')
            mail_detail.content = list()
            try:
                for tag in os.listdir(
                        os.path.join(self.config['mail_content_path'], disk_folder, str(mail_detail.uid))):
                    if tag == '__main__.txt':
                        mail_detail.main_text = self.__get_mail_text__(mail_detail.mail_box, mail_detail.uid)
                    else:
                        mail_detail.content.append(tag)
            except FileNotFoundError:
                continue

            file_date_folder = classify_mail_contents(mail_detail, self.db)
            for file_name, classified_tuple in file_date_folder.items():
                date, folder_name = classified_tuple[0], classified_tuple[1]
                if folder_name in ('托管估值表',):
                    date = None
                if mail_detail.received_time.hour < 12:
                    day_part_str = '上午'
                elif 12 <= mail_detail.received_time.hour < 15:
                    day_part_str = '下午 收盘前'
                else:
                    day_part_str = '下午 收盘后'
                if date is None:  # 估值表
                    if folder_name is None:
                        target_path = os.path.join(
                            self.config['mail_classification_path'],
                            '收件日{} {}'.format(mail_detail.received_time.strftime('%Y%m%d'), day_part_str),
                        )
                    else:
                        target_path = os.path.join(
                            self.config['mail_classification_path'],
                            '收件日{} {}'.format(mail_detail.received_time.strftime('%Y%m%d'), day_part_str),
                            folder_name,
                        )
                else:
                    if folder_name is None:
                        target_path = os.path.join(
                            self.config['mail_classification_path'],
                            '收件日{} {}'.format(mail_detail.received_time.strftime('%Y%m%d'), day_part_str),
                            '{}产品交割单{}'.format(folder_tag, date.strftime('%Y%m%d')),
                        )
                    else:
                        target_path = os.path.join(
                            self.config['mail_classification_path'],
                            '收件日{} {}'.format(mail_detail.received_time.strftime('%Y%m%d'), day_part_str),
                            '{}产品交割单{}'.format(folder_tag, date.strftime('%Y%m%d')), folder_name,
                        )
                if not os.path.exists(target_path):
                    os.makedirs(target_path, exist_ok=True)
                if os.path.exists(os.path.join(target_path, file_name)):
                    if hash(open(os.path.join(target_path, file_name), 'rb').read()) == hash(open(
                            os.path.join(self.config['mail_content_path'], disk_folder, str(mail_detail.uid),
                                         file_name),
                            'rb',
                    ).read()):
                        continue  # 如果目标目录下的文件和待拷贝源文件的内容一致，则continue
                    else:
                        os.remove(os.path.join(target_path, file_name))  # 先删掉目标目录下的文件
                        self.log.debug('update {}'.format(os.path.join(target_path, file_name)))
                try:
                    shutil.copy(os.path.join(
                        self.config['mail_content_path'], disk_folder, str(mail_detail.uid), file_name
                    ), target_path)
                except PermissionError:
                    self.log.debug('{} copy to {} fail'.format(os.path.join(
                        self.config['mail_content_path'], disk_folder, str(mail_detail.uid), file_name), target_path))
                    # 原本它是raise RuntimeErro()的
                    shutil.copy(os.path.join(
                        self.config['mail_content_path'], disk_folder, str(mail_detail.uid), file_name
                    ), 'D:\\MassCacheDir\\Temp_lang\\')

                self.log.debug('copied {}'.format(os.path.join(target_path, file_name)))


if __name__ == '__main__':
    import pickle

    settings = {
        'mail_bit_path': r'Z:\估值专用邮箱数据\邮件IMAP二进制缓存',
        'mail_content_path': r'Z:\估值专用邮箱数据\邮件IMAP解码数据缓存',
        'mail_classification_path': r'Z:\估值专用邮箱数据\邮件账户分类缓存',
    }
    settings.update(pickle.load(open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'acc.pick'), 'rb')))

    SINCE_DATE = datetime.date(2019, 10, 20)

    loader = ImapLoader(settings)
    loader.update_mail_data_base(
        since_date=SINCE_DATE,
        # since_date=datetime.date(2019, 10, 20),
        # on_date=datetime.date(2019, 10, 20),
    )
    loader.update_mail_content_cache()
    loader.update_mail_classification(
        range_start=SINCE_DATE,
        # range_start=datetime.date(2019, 10, 20),
        # range_end=datetime.date(2019, 9, 6),
    )
