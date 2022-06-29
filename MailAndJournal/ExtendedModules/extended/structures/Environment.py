# -*- encoding: UTF-8 -*-


class Environment(object):
    """
    变量传递结构，在程序的各个部分之间（特别是文件之间）传递各项参数
    需要注意，在 python 当中，结构化的内容在函数之间是引用传递的，比如 3 是值传递，而 [3,]就可以引用传递
    """
    __env__ = None

    def __init__(self):
        if Environment.__env__ is None:
            Environment.__env__ = self
        else:
            raise RuntimeError('Environment set up again!')

        self.storage = dict()
        self.__exit_strategy__ = dict()
        self.__exited_tag__ = False

    def __del__(self):
        if self.__exited_tag__ is False:
            print('[Waring]: Environment ended (with program finish) without exit action.')
        del self.storage

    def __getattr__(self, key: str):
        try:
            return self.storage.__getitem__(key)
        except KeyError:
            raise AttributeError('No Attribute {} or not deployed'.format(key))

    @classmethod
    def get_instance(cls):
        """返回已经创建的 Environment 对象"""
        if Environment.__env__ is None:
            # Environment.__env__ = Environment()
            raise RuntimeError("Environment has not been created.")
        assert isinstance(Environment.__env__, Environment)
        return Environment.__env__

    def deploy_module(self, m_key: str, m_obj, exit_func=None):
        self.storage.__setitem__(m_key, m_obj)
        self.__exit_strategy__.__setitem__(m_key, exit_func)

    def exit(self):

        for k, v in self.storage.items():
            try:
                exit_tag = self.__exit_strategy__[k]
            except KeyError:
                continue
            if exit_tag is None:
                continue
            elif isinstance(exit_tag, str):
                getattr(v, exit_tag).__call__()
            else:
                exit_tag.__call__()

        self.__exited_tag__ = True
