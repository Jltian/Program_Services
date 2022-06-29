# -*- encoding: UTF-8 -*-
import os


class Environment(object):
    """
    变量传递结构，在程序的各个部分之间（特别是文件之间）传递各项参数
    需要注意，在 python 当中，结构化的内容在函数之间是引用传递的，比如 3 是值传递，而 [3,]就可以引用传递
    """
    __env__ = None
    # product_range = (  # 非托管的产品范围 手动调整即运行顺序
    #     '久铭2号', '稳健7号',
    #     '久铭3号', '全球1号', '收益1号',
    #     '稳健2号', '稳健3号', '稳健5号', '稳健6号', '稳健8号', '稳健9号', '稳健10号',
    #     '稳健11号', '稳健12号', '稳健15号', '稳健16号', '稳健17号', '稳健18号', '稳健19号',
    #     '稳健21号', '稳健31号', '稳健32号', '稳健33号',   # '稳健22号',
    #     '稳利2号', '双盈1号',
    # )
    product_range = None
    # 若托管范围内的产品流水和账单差异大不用处理
    product_name_range = product_range

    def __init__(self):
        from utils import load_yaml
        if Environment.__env__ is None:
            Environment.__env__ = self
        else:
            raise RuntimeError('Environment set up again!')
        self.config = load_yaml(os.path.join(self.root_path(), 'settings.yaml'))

        # ---- [set before using] ---- #
        self.data = dict()
        self.__data_base__ = None  # 数据库连接
        self.__event_engine__ = None  # 事件引擎
        self.__wind_engine__ = None  # Wind引擎

        self.__entry_generator__ = None  # 凭证生成

        # ---- [set when called] --- #
        self.__institution_name_set__ = None  # 机构简称目录
        self.__security_info_list__ = None  # 合约名称目录

        # ---- [others] ---- #
        self.__exited_tag__ = False

    def __del__(self):
        if self.__exited_tag__ is False:
            print('[Waring]: Environment ended (with program finish) without exit action.')
        del self.__data_base__

    @classmethod
    def get_instance(cls):
        """返回已经创建的 Environment 对象"""
        if Environment.__env__ is None:
            Environment.__env__ = Environment()
            # raise RuntimeError("Environment has not been created.")
        assert isinstance(Environment.__env__, Environment)
        return Environment.__env__

    @property
    def info_board(self):
        from jetend.modules.jmInfoBoard import jmInfoBoard
        # from jetend.structures import MySQL
        if 'info_board' not in self.data:
            info_board = jmInfoBoard(self.data_base)
            self.data['info_board'] = info_board
        else:
            info_board = self.data['info_board']
        assert isinstance(info_board, jmInfoBoard)
        return info_board

    @property
    def wind_board(self):
        from jetend.modules.jmMarketBoard import jmMarketBoard
        if 'wind_board' not in self.data:
            from jetend.structures import Sqlite
            # self.data['wind_board'] = jmMarketBoard(self.wind_engine, self.memory_cache)        # wind缓存->内存
            # self.data['wind_board'] = jmMarketBoard(self.wind_engine, Sqlite(r'C:\Documents\GitHub\cache.db'))         # wind缓存->本地
            self.data['wind_board'] = jmMarketBoard(self.wind_engine, self.data_base, db_name='test')
        wind_board = self.data['wind_board']
        assert isinstance(wind_board, jmMarketBoard)
        return wind_board

    @property
    def local_cache(self):
        from jetend.structures import Sqlite
        if 'local_cache' not in self.data:
            local_cache = Sqlite(db_path=os.path.join(self.root_path(), 'temp.db'))
            self.data['local_cache'] = local_cache
        else:
            local_cache = self.data['local_cache']
        assert isinstance(local_cache, Sqlite)
        return local_cache

    @property
    def memory_cache(self):
        from jetend.structures import Sqlite
        if 'memory_cache' not in self.data:
            memory_cache = Sqlite()
            self.data['memory_cache'] = memory_cache
        else:
            memory_cache = self.data['memory_cache']
        assert isinstance(memory_cache, Sqlite)
        return memory_cache

    @property
    def wind_engine(self):
        if self.__wind_engine__ is None:
            from WindPy import w
            self.__wind_engine__ = w
        # if not self.__wind_engine__.isconnected():
        #     self.__wind_engine__.start()
        return self.__wind_engine__

    @property
    def event_engine(self):
        from jetend.structures import SingleThreadEventEngine
        if self.__event_engine__ is None:
            self.__event_engine__ = SingleThreadEventEngine()
            self.__event_engine__.start()
        assert isinstance(self.__event_engine__, SingleThreadEventEngine), 'set EventEngine before using.'
        return self.__event_engine__

    @property
    def data_base(self):
        from jetend.structures import MySQL
        if self.__data_base__ is None:
            self.__data_base__ = MySQL(
                username=self.config.get('DataBase')['usr'], passwd=self.config.get('DataBase')['pwd'],
                server=self.config.get('DataBase')['server'], port=self.config.get('DataBase')['port']
            )
        assert isinstance(self.__data_base__, MySQL), 'set DataBase before using.'
        return self.__data_base__

    @property
    def entry_gen(self):
        assert hasattr(self.__entry_generator__, 'accounts') and hasattr(self.__entry_generator__, 'positions')
        return self.__entry_generator__

    def deploy_entry_generator(self, entry_gen):
        self.__entry_generator__ = entry_gen

    def trigger_event(self, event_type, data=None, **kwargs):
        from structures import EventObject
        e_object = EventObject(event_type=event_type, data=data, **kwargs)
        self.event_engine.put(e_object)

    @staticmethod
    def root_path():
        import os
        current_path = os.path.abspath(os.path.dirname(__file__))
        current_path = current_path.split(os.path.sep)
        current_path.pop(-1)  # to upper level folder
        return os.path.sep.join(current_path)

    def __load_config__(self):
        import os
        from utils import load_yaml
        return load_yaml(os.path.join(self.root_path(), 'settings.yaml'))

    def exit(self):
        if self.__event_engine__ is not None:
            self.__event_engine__.stop()

        if self.__wind_engine__ is not None:
            self.__wind_engine__.stop()

        if 'local_cache' in self.data:
            self.local_cache.close()

        self.__exited_tag__ = True
