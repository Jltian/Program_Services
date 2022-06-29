# -*- encoding: UTF-8 -*-
from .DataTable import DataList
from .DataObject import DataObject
from .Event import EventType, EventObject


class Persist(object):
    inner2outer_map = dict()

    def __init__(self, *args, **kwargs):
        pass

    def get_state(self):
        state_dict = dict()
        for key in self.inner2outer_map.keys():
            state_dict[key] = str(getattr(self, key))
        return state_dict

    @classmethod
    def set_state(cls, state: dict):
        return cls(**state)

    def update_by(self, *args, **kwargs):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def check_match(self, *args):
        raise NotImplementedError

    @staticmethod
    def __check_match__(target, base):
        if abs(base) < 0.1:  # 持仓为零
            if abs(target) < 0.1:
                return True
            else:
                return False
        else:
            if abs((target - base) / base) < 0.1 * 0.01:
                return True
            else:
                return False


class StatusObject:

    def update_from(self, *args, **kwargs):
        raise NotImplementedError
