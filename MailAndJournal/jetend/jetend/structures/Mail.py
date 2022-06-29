# -*- encoding: UTF-8 -*-
import poplib

poplib._MAXLINE = 20480

from email.header import decode_header


from extended.wrapper.Log import get_logger


def decode_email_str(s: str):
    if s is None:
        return None
    elif s.startswith('=?'):
        decoded_list = decode_header(s)
        assert len(decoded_list) == 1, str(decoded_list)
        value, charset = decoded_list[0]
        if charset is not None:
            value = value.decode(charset)
        return value
    else:
        return s


# def decode_base64(s, charset='utf8'):
#     return str(base64.decodebytes(s.encode(encoding=charset)), encoding=charset)


class MailInfo(object):
    """
    用于临时保存POP邮件列表中信息的类
    """
    def __init__(self, index: int, lsize: int):
        self.index = index
        self.lsize = lsize
        self.dsize = None
        self.status = None
        self.data_bytes = None

    @classmethod
    def define_sqlalchemy_table(cls, meta, table_name: str):
        from sqlalchemy import MetaData, Table, Column, Integer, Boolean
        assert isinstance(meta, MetaData)
        return Table(
            table_name, meta,
            Column('index', Integer, nullable=False, primary_key=True),
            Column('lsize', Integer),
            Column('dsize', Integer),
            Column('status', Boolean),
        )

#
# class ImapMailWrapper(object):
#
#     def __init__(self, server_address: str, user_account: str, user_password: str, **kwargs):
#         self.log = get_logger(self.__class__.__name__)
#         self.__user_name__, self.__user_pwd__ = user_account, user_password
#
#         # 开始连接到服务器
#         self.server = imapclient.IMAPClient(
#             host=server_address, ssl=kwargs.get('ssl', True), port=kwargs.get('port', 993)
#         )



class PopMailWrapper(object):
    
    def __init__(self, server_address: str, user_account: str, user_password: str, **kwargs):
        self.log = get_logger(self.__class__.__name__)
        self.__user_name__, self.__user_pwd__ = user_account, user_password

        # 开始连接到服务器
        self.server = poplib.POP3(server_address)
        # 可选项： 打开或者关闭调试信息，1为打开，会在控制台打印客户端与服务器的交互信息
        server_debug_level = kwargs.get('server_debug_level', 0)
        assert server_debug_level in (0, 1), '调试信息接口 {}'.format(server_debug_level)
        self.server.set_debuglevel(server_debug_level)

        self.mail_list = list()
        self.__test_server_connection__()   # 测试连通性
        self.__mail_counts__, self.__login_status__ = 0, None

    def __test_server_connection__(self):
        """测试邮件服务是否连通"""
        welcome_info = self.server.getwelcome().decode('utf8')
        if 'OK' in welcome_info:
            self.log.debug('服务器 {} 连接成功'.format(self.server.host))
        else:
            raise ConnectionError('服务器 {} 无法连通！'.format(self.server.host))

    def login(self):
        """登录邮箱"""
        self.server.user(self.__user_name__)
        self.server.pass_(self.__user_pwd__)
        self.__mail_counts__, total_mail_size = self.server.stat()
        self.__login_status__ = True
        assert isinstance(self.__mail_counts__, int), '{} {}'.format(self.__mail_counts__, type(self.__mail_counts__))
    
    def fetch_mail_list(self):
        resp, mails, octets = self.server.list()
        self.__login_status__ = True
        assert resp.decode() in ('+OK', ), '{} {}'.format(type(resp), resp)
        for one_mail in mails:
            one_mail = one_mail.decode().split(' ')
            assert len(one_mail) == 2, str(one_mail)
            self.mail_list.append(MailInfo(int(one_mail[0]), int(one_mail[1])))
        return self.mail_list

    def fetch_mail_detail(self, mail: MailInfo):
        from poplib import error_proto
        if mail.status is not None:
            return RuntimeError('重复获取邮件信息 {}'.format(mail.__dict__))
        try:
            resp, mail_message_lines, octets = self.server.retr(mail.index)
        except error_proto:
            raise ConnectionAbortedError('到 {} 的连接已中断'.format(self.server.host))
        assert resp.decode() in ('+OK', ), '{} {}'.format(type(resp), resp)
        mail.status, mail.dsize = True, int(octets)
        msg_byte = b'\r\n'.join(mail_message_lines)
        mail.data_bytes = msg_byte
        return mail

    def logout(self):
        """结束对话"""
        self.server.close()
        self.__login_status__ = False

    @property
    def total_mail_numbers(self):
        return len(self.mail_list)


if __name__ == '__main__':
    import imaplib
    from hashlib import md5
    conn = imaplib.IMAP4_SSL(host='imap.exmail.qq.com', port=993, )

    data = conn.login('gzzy@jiumingfunds.com', 'Guzhi123')
    # data = conn.login('tangming@jiumingfunds.com', 'Tm834684')
    print('login', type(data), data)

    data = conn.list()
    print('list', type(data), len(data), data)

    data = data[1]
    print('list content', type(data), data)

    data = data[1]
    print('list content content', type(data), data)

    conn.select('INBOX')
    data = conn.search(None, 'SINCE 20-Oct-2019')
    print('search', type(data), data)

    data = data[1]
    print('search content', type(data), len(data), data)

    data = conn.fetch(b'1081', '(RFC822)')
    # data = conn.fetch('1081', 'UID')
    # data = data[1][0][1]
    print('fetch', type(data), len(data), data, )
