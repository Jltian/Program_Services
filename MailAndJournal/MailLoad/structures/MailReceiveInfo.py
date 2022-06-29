# -*- encoding: UTF-8 -*-


class MailReceiveInfo(object):
    def __init__(self):
        self.mail_account = None
        self.institution = None

    @classmethod
    def define_sqlalchemy_table(cls, meta):
        from sqlalchemy import MetaData, Table, Column, String, Integer, DateTime
        assert isinstance(meta, MetaData)
        return Table(
            cls.__name__, meta,
            Column('mail_account', String, nullable=False, primary_key=True),
            Column('institution', String, primary_key=True),
        )
