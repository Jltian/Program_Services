# -*- encoding: UTF-8 -*-


class MailDetail(object):
    def __init__(self, index: int):
        self.index = index
        self.message_id = None
        self.mime_version = None
        self.from_account = None
        self.subject = None
        self.received_time = None
        self.content = None
        self.main_text = None

    def __repr__(self):
        return '\n'.join([
            '{}:'.format(self.__class__.__name__), 'index={}'.format(self.index), 'message_id={}'.format(self.message_id),
            'mime_version={}'.format(self.mime_version), 'from_account={}'.format(self.from_account),
            'subject={}'.format(self.subject), 'received_time={}'.format(self.received_time),
            'main_text={}'.format(self.get_main_text()), 'content={}'.format(self.content),
        ])

    def get_main_text(self):
        try:
            return self.main_text
        except AttributeError:
            return ''

    @classmethod
    def init_from(cls, index: int, parsed_dict: dict):
        new_obj = cls(index)
        new_obj.message_id = parsed_dict['message_id']
        new_obj.mime_version = parsed_dict['mime_version']
        new_obj.from_account = parsed_dict['from_account']
        new_obj.subject = parsed_dict['subject']
        new_obj.received_time = parsed_dict['received_time']
        new_obj.content = parsed_dict['content']
        return new_obj

    @classmethod
    def define_sqlalchemy_table(cls, meta):
        from sqlalchemy import MetaData, Table, Column, String, Integer, DateTime
        assert isinstance(meta, MetaData)
        return Table(
            cls.__name__, meta,
            Column('index', Integer, nullable=False, primary_key=True),
            Column('message_id', String),
            Column('mime_version', String),
            Column('from_account', String),
            Column('subject', String),
            Column('received_time', DateTime),
        )


class ImapMailDetail(object):
    def __init__(self, mail_box: str, uid: int):
        self.mail_box = mail_box
        self.uid = uid
        self.message_id = None
        self.mime_version = None
        self.from_account = None
        self.subject = None
        self.received_time = None
        self.content = None
        self.main_text = None

    def __repr__(self):
        return '\n'.join([
            '{}:'.format(self.__class__.__name__),
            'mail_box={}'.format(self.mail_box),
            'uid={}'.format(self.uid),
            'message_id={}'.format(self.message_id),
            'mime_version={}'.format(self.mime_version), 'from_account={}'.format(self.from_account),
            'subject={}'.format(self.subject), 'received_time={}'.format(self.received_time),
            'main_text={}'.format(self.get_main_text()), 'content={}'.format(self.content),
        ])

    def get_main_text(self):
        try:
            return self.main_text
        except AttributeError:
            return ''

    @classmethod
    def init_from(cls, mail_box: str, uid: int, parsed_dict: dict):
        new_obj = cls(mail_box, uid)
        new_obj.message_id = parsed_dict['message_id']
        new_obj.mime_version = parsed_dict['mime_version']
        new_obj.from_account = parsed_dict['from_account']
        new_obj.subject = parsed_dict['subject']
        new_obj.received_time = parsed_dict['received_time']
        new_obj.content = parsed_dict['content']
        return new_obj

    @classmethod
    def define_sqlalchemy_table(cls, meta):
        from sqlalchemy import MetaData, Table, Column, String, Integer, DateTime
        assert isinstance(meta, MetaData)
        return Table(
            cls.__name__, meta,
            Column('mail_box', String, nullable=False, primary_key=True),
            Column('uid', Integer, nullable=False, primary_key=True),
            Column('message_id', String),
            Column('mime_version', String),
            Column('from_account', String),
            Column('subject', String),
            Column('received_time', DateTime),
        )
