# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
from sqlalchemy import Table
from sqlalchemy.orm import mapper


class SqliteMappable:

    @classmethod
    def define_table(cls, meta):
        from sqlalchemy import MetaData
        assert isinstance(meta, MetaData)
        raise NotImplementedError


class Sqlite(object):
    connection_dict = dict()

    def __init__(self, db_path: str = ':memory:'):
        from sqlalchemy import create_engine, MetaData

        # 建立连接
        self.engine = create_engine('sqlite:///{host}'.format(host=db_path), echo=False)
        self.metadata = MetaData(bind=self.engine)
        self.__session__ = None

        # 若目标表格不存在则创建
        # self.metadata.create_all(bind=self.engine, checkfirst=True)

    @classmethod
    def new(cls, db_path: str = ':memory:'):
        if db_path in cls.connection_dict:
            return cls.connection_dict[db_path]
        else:
            return cls(db_path=db_path)

    @property
    def session(self):
        from sqlalchemy.orm import Session
        if self.__session__ is None:
            from sqlalchemy.orm import sessionmaker
            # from sqlalchemy.orm import create_session
            # self.session = create_session(bind=self.engine)
            ses = sessionmaker(bind=self.engine)
            self.__session__ = ses()
        assert isinstance(self.__session__, Session)
        return self.__session__

    def execute(self, clause: str, params=None):
        self.session.execute(clause, params=params,)
        self.session.flush()

    @staticmethod
    def map(obj_type: type, table_def: Table, create_table: bool = True):
        from sqlalchemy.exc import ArgumentError
        try:
            mapper(obj_type, table_def)
            table_def.create(checkfirst=create_table)
        except ArgumentError:
            pass

    def add_all(self, obj):
        if len(obj) > 0:
            self.session.add_all(obj)
            self.session.commit()

    def add(self, obj):
        self.session.add(obj)
        self.session.commit()

    def delete_table(self, table: Table):
        self.metadata.remove(table)

    def clean(self):
        self.metadata.drop_all()

    def close(self):
        self.session.flush()
        self.session.close()
