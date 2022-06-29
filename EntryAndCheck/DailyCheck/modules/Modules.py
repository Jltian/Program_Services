# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
from jetend.structures import Environment


class Modules(Environment):

    @property
    def cache_db(self):
        from jetend.structures import Sqlite
        cache_db = self.storage.__getitem__('cache_db')
        assert isinstance(cache_db, Sqlite)
        return cache_db

    @property
    def sql_db(self):
        from jetend.structures import MySQL
        sql_db = self.storage.__getitem__('sql_db')
        assert isinstance(sql_db, MySQL)
        return sql_db

    @property
    def wind_engine(self):
        try:
            wind_engine = self.storage.__getitem__('wind_engine')
        except KeyError:
            from WindPy import w
            wind_engine = w
            self.storage.__setitem__('wind_engine', wind_engine)
        # if wind_engine.isconnected() is False:
        #     wind_engine.start()
        return wind_engine

    @property
    def info_board(self):
        from jetend.modules.jmInfoBoard import jmInfoBoard
        try:
            product_board = self.storage.__getitem__('product_board')
        except KeyError:
            product_board = jmInfoBoard(self.sql_db)
            self.deploy_module('product_board', product_board, None)
        assert isinstance(product_board, jmInfoBoard)
        return product_board

    @property
    def market_board(self):
        from jetend.modules.jmMarketBoard import jmMarketBoard
        try:
            market_board = self.storage.__getitem__('market_board')
        except KeyError:
            market_board = jmMarketBoard(self.wind_engine, self.sql_db)
            self.deploy_module('market_board', market_board)
        assert isinstance(market_board, jmMarketBoard)
        return market_board

    def reach_relative_root_path(self, *args):
        from os import path
        r_path = path.abspath(path.dirname(__file__)).split(path.sep)
        r_path.pop(-1)
        r_path.extend(args)
        return path.sep.join(r_path)

    @property
    def root_path(self):
        from os import path
        r_path = path.abspath(path.dirname(__file__)).split(path.sep)
        r_path.pop(-1)
        return path.sep.join(r_path)
