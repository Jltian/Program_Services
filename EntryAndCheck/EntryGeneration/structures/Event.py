# -*- encoding: UTF-8 -*-
from enum import Enum


class EventType(Enum):
    # -------- [business] --------
    AccountUpdate = 'AccountUpdate'                         # 存借款余额缓存更新
    ConfirmGeneration = 'ConfirmGeneration'                 # 从在途申述生成申赎确认对象
    EntryGeneration = 'JournalEntryGeneration'              # 会计分录对象生成
    PositionUpdate = 'PositionUpdate'                       # 从交易信息更新会计持仓信息
    VATGen = 'VATGen'                     # 增值税生成

    # -------- [system] --------
    Log = 'LogEvent'                                    # 日志事件
    Test = 'TestEvent'                                  # 测试事件


class EventObject:
    """事件对象"""
    def __init__(self, event_type: EventType, data=None, **kwargs):
        """

        :param event_type:
        :param kwargs: data = 1, event.data -> 1
        """
        self.type = event_type                  # 事件类型
        self.data = data                        # 事件涉及对象
        for key, value in kwargs.items():
            setattr(self, key, value)           # 该事件类型涉及到的其他数据
