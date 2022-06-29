# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
from sqlalchemy import create_engine, Table
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.exc import ArgumentError, IntegrityError


class MySQL(object):
    """MySQL 数据库包装，一个账号一个包装"""
    connection_dict = dict()

    def __init__(self, username: str, passwd: str, server: str = 'localhost', port: int = 3306):
        self.__usr__ = username
        self.__pwd__ = passwd
        self.__server__ = server
        self.__port__ = port
        self.__engine_dict__ = dict()
        # self.__metadata__ = MetaData(bind=self.__engine__)
        # self.metadata.create_all(bind=self.engine, checkfirst=True)
        # session = sessionmaker(bind=self.__engine_dict__)
        self.__session_dict__ = dict()
        # from sqlalchemy.orm import create_session
        # self.session = create_session(bind=self.engine)

    @classmethod
    def new(cls, username: str, passwd: str, server: str = 'localhost', port: int = 3306):
        if server in cls.connection_dict:
            return cls.connection_dict[server]
        else:
            return cls(username=username, passwd=passwd, server=server, port=port)

    def engine(self, db_name: str, charset: str = 'utf8'):
        from sqlalchemy.engine import Engine
        if db_name not in self.__engine_dict__:
            try:
                self.__engine_dict__[db_name] = create_engine('mysql+pymysql://{}:{}@{}:{}/{}?charset={}'.format(
                    self.__usr__, self.__pwd__, self.__server__, str(self.__port__), db_name, charset
                ))
                return self.__engine_dict__[db_name]
            except Exception as e:
                raise e
        engine = self.__engine_dict__[db_name]
        assert isinstance(engine, Engine)
        return engine

    def session(self, db_name: str, charset: str = 'utf8'):
        from sqlalchemy.orm import Session
        if db_name not in self.__session_dict__:
            session_mk = sessionmaker(bind=self.engine(db_name=db_name, charset=charset))
            self.__session_dict__[db_name] = session_mk()
        session = self.__session_dict__[db_name]
        assert isinstance(session, Session)
        return session

    def metadata(self, db_name: str):
        from sqlalchemy import MetaData
        return MetaData(bind=self.engine(db_name=db_name))

    def execute(self, db_name: str, sql: str):
        try:
            self.engine(db_name).execute(sql)
        except Exception as exec_error:
            print(sql)
            raise exec_error

    def read_pd_query(self, db_name: str, sql: str):
        from pandas import read_sql_query
        return read_sql_query(sql, self.engine(db_name))

    def read_dict_query(self, db_name: str, sql: str):
        dt = self.read_pd_query(db_name, sql)
        re_list = list()
        for i in dt.index:
            one_series = dt.iloc[i, ]
            re_list.append(one_series.to_dict())
        return re_list

    def insert_data_list(self, db_name: str, table_name: str, data_list, integrity_error_skip: bool = False):
        assert isinstance(data_list, list), '{}\n{}'.format(type(data_list), data_list)
        if len(data_list) == 0:
            return
        for obj in data_list:
            try:
                self.insert_data_obj(db_name=db_name, table_name=table_name, data_obj=obj)
            except IntegrityError as integrity_error:
                if integrity_error_skip is True:
                    continue
                else:
                    raise integrity_error

    def insert_data_obj(self, db_name: str, table_name: str, data_obj):
        if hasattr(data_obj, 'form_insert_sql'):
            sql = getattr(data_obj, 'form_insert_sql').__call__(table_name)
            self.execute(db_name, sql)
        elif isinstance(data_obj, dict):
            self.__insert_dict_obj__(db_name, table_name, data_obj)
        else:
            raise NotImplementedError('{}-{}'.format(type(data_obj), data_obj))

    def __insert_dict_obj__(self, db_name: str, table_name: str, dict_obj):
        from extended.utils import is_valid_float
        assert isinstance(dict_obj, dict), 'dict_obj should has format dict or super_dict'
        col_list, data_list = list(dict_obj.keys()), list()
        for key in col_list:
            cell = dict_obj[key]
            if cell is None:
                data_list.append("''")
            elif isinstance(cell, float):
                if not is_valid_float(cell):
                    data_list.append("null")
                else:
                    data_list.append(str(cell))
            elif isinstance(cell, int):
                data_list.append(str(cell))
            else:
                data_list.append("'{}'".format(cell))
        sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table_name, ', '.join(col_list), ', '.join(data_list))
        self.execute(db_name, sql)

    @staticmethod
    def map(obj_type: type, table_def: Table, create_table: bool = True):
        try:
            mapper(obj_type, table_def)
            table_def.create(checkfirst=create_table)
        except ArgumentError:
            pass

    def add_all(self, db_name: str, obj):
        if len(obj) > 0:
            self.session(db_name=db_name).add_all(obj)
            self.session(db_name=db_name).commit()

    def add(self, db_name: str, obj):
        self.session(db_name=db_name).add(obj)
        self.session(db_name=db_name).commit()

    # def delete_table(self, table: Table):
    #     self.metadata.remove(table)

    # def add_all(self, obj):
    #     if len(obj) > 0:
    #         self.session.add_all(obj)
    #         self.session.commit()
    #         self.optimize()
    #
    # def add(self, obj):
    #     self.session.add(obj)
    #     self.session.commit()
    #
    # def drop_tables(self, table):
    #     from sqlalchemy import Table
    #     assert isinstance(table, Table), str(TypeError('table should be of type sqlalchemy.Table'))
    #     self.metadata.remove(table)
    #
    # def clear_db(self):
    #     self.metadata.drop_all()
    #
    # def get_all(self, obj_type: type, **filter_by):
    #     """get_all all {obj_type} filter by {kwargs} -> list"""
    #     return self.session.query(obj_type).filter_by(**filter_by).all()

    # def merge(self, inst, load=True):
    #     if isinstance(inst, (Book, Reader)):
    #         self.session.merge(inst, load=load)
    #     elif isinstance(inst, Event):
    #         if self.__action_limit__ is True:
    #             if self.__action_range__[0] <= inst.date <= self.__action_range__[1]:
    #                 raise PermissionError('Event {} can be changed since created.'.format(inst.__repr__()))
    #             else:
    #                 self.session.merge(inst, load=load)
    #         else:
    #             self.session.merge(inst, load=load)
    #     else:
    #         raise TypeError
