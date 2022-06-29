# -*- encoding: UTF-8 -*-
import time

from queue import Queue, Empty
from threading import Thread
from collections import defaultdict


class EventObject:
    """事件对象"""
    def __init__(self, event_type, data=None, **kwargs):
        """

        :param event_type:
        :param kwargs: data = 1, event.data -> 1
        """
        self.type = event_type                  # 事件类型
        self.data = data                        # 事件涉及对象
        for key, value in kwargs.items():
            assert key != 'data', '{}'.format(kwargs)
            setattr(self, key, value)           # 该事件类型涉及到的其他数据


class EventEngine(object):
    """
    事件驱动引擎

    事件驱动引擎中所有的变量都设置为了私有，这是为了防止从外部修改了这些变量的值或状态。

    方法说明：
    start: 公共方法，启动引擎
    stop：公共方法，停止引擎
    register：公共方法，向引擎中注册监听函数
    unregister：公共方法，向引擎中注销监听函数
    put：公共方法，向事件队列中存入新的事件

    事件监听函数必须定义为输入参数仅为一个event对象，即：

    函数
    def func(event: EventObject)
        ...

    对象方法
    def method(self, event: EventObject)
        ...

    """
    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def wait(self):
        raise NotImplementedError

    def put(self, event: EventObject):
        raise NotImplementedError

    def register(self, event_type, handler):
        raise NotImplementedError

    def unregister(self, event_type, handler):
        raise NotImplementedError


class SingleThreadEventEngine(EventEngine):
    """单线程事件驱动引擎"""
    def __init__(self):
        self.__is_running__ = False                 # 事件引擎开关
        self.__event_queue__ = Queue()              # 事件队列
        self.__thread__ = Thread(target=self.__run__)                      # 事件处理线程
        # __handlers__，用来保存对应的事件调用关系
        # 其中每个键对应的值是一个列表，列表中保存了对该事件进行监听的函数功能
        self.__handlers__ = defaultdict(list)

    def __run__(self):
        """引擎运行"""
        while self.__is_running__ is True:
            try:
                event = self.__event_queue__.get(block=True, timeout=5)
                self.__process__(event)
            except Empty:
                continue

    def __process__(self, event: EventObject):
        """处理事件"""
        # 检查是否存在对该事件进行监听的处理函数
        if event.type in self.__handlers__:
            # 若存在，则按顺序将事件传递给处理函数执行
            for handler in self.__handlers__[event.type]:
                handler(event)

    def start(self):
        """引擎启动"""
        self.__is_running__ = True                  # 将引擎设为启动
        self.__thread__.start()                     # 启动事件处理线程

    def stop(self):
        """停止引擎"""
        self.__is_running__ = False                 # 将引擎设为停止
        self.__thread__.join()                      # 等待事件处理线程退出

    def wait(self):
        while self.__event_queue__.empty() is False:
            time.sleep(0.02)

    def register(self, event_type, handler):
        """注册事件处理函数监听"""
        # 尝试获取该事件类型对应的处理函数列表，若无则创建
        handler_list = self.__handlers__[event_type]

        # 若要注册的处理器不在该事件的处理器列表中，则注册该事件
        if handler not in handler_list:
            handler_list.append(handler)

    def unregister(self, event_type, handler):
        """注销事件处理函数监听"""
        # 尝试获取该事件类型对应的处理函数列表，若无则忽略该次注销请求
        handler_list = self.__handlers__[event_type]

        # 如果该函数存在于列表中，则移除
        if handler in handler_list:
            handler_list.remove(handler)

        # 如果函数列表为空，则从引擎中移除该事件类型
        if len(handler_list) == 0:
            del self.__handlers__[event_type]

    def put(self, event: EventObject):
        """向事件队列中存入事件"""
        self.__event_queue__.put(event)


# ----------------------------------------------------------------------
def event_engine_test():
    """测试函数"""

    from datetime import datetime

    def simple_test(event):
        print(('当前时间：{}'.format(datetime.now())))
        print('测试成功 {}'.format(event))

    ee = SingleThreadEventEngine()
    ee.register('test', simple_test)
    ee.start()
    ee.put(EventObject(event_type='test'))
    ee.stop()


# 直接运行脚本可以进行测试
if __name__ == '__main__':
    event_engine_test()
