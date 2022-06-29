# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import warnings
import traceback


def depreciated_method(new_name: str):
    def __depreciated__(func):
        def wrapper(*args, **kwargs):
            for tb_info in traceback.extract_stack():
            # tb_info = traceback.extract_stack()[-2]
                assert isinstance(tb_info, traceback.FrameSummary)
                warnings.warn('[depreciated]: {} at line {} {}'.format(tb_info.filename, tb_info.lineno, tb_info.line))
            warnings.warn(
                'method <{}> is depreciated and will be removed in the future, please use {} instead.'.format(
                    getattr(func, '__name__', str(func)), new_name)
            )
            return func.__call__(*args, **kwargs)
        return wrapper
    return __depreciated__


@depreciated_method('depreciated_method')
def depreciated(new_name: str):
    return depreciated_method(new_name)
