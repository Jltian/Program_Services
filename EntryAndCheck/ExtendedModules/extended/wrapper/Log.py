# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import logging


__log_leval_map__ = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


class LogWrapper(logging.Logger):

    def __init__(self, name: str, level=logging.NOTSET):
        super(LogWrapper, self).__init__(name=name, level=level)

    @staticmethod
    def time_sleep(seconds):
        from time import sleep
        sleep(seconds)

    def debug_running(self, *args, **kwargs):
        # self.debug('[running]: {0:s} - now {1:s}'.format(running, status))
        if self.isEnabledFor(logging.DEBUG):
            if len(args) == 2:
                self._log(
                    logging.DEBUG,
                    '[running]: {0:s} - now {1:s}'.format(args[0], args[1]),
                    tuple(), **kwargs
                )
            elif len(args) == 1:
                self._log(logging.DEBUG, '[running]: {0:s}'.format(args[0]), tuple(), **kwargs)
            else:
                self._log(logging.DEBUG, *args, **kwargs)

    def info_running(self, *args, **kwargs):
        # self.debug('[running]: {0:s} - now {1:s}'.format(running, status))
        if self.isEnabledFor(logging.INFO):
            if len(args) == 2:
                self._log(
                    logging.INFO,
                    '[running]: {0:s} - {1:s}'.format(args[0], args[1]),
                    tuple(), **kwargs
                )
            elif len(args) == 1:
                self._log(logging.INFO, '[running]: {0:s}'.format(args[0]), tuple(), **kwargs)
            else:
                self._log(logging.INFO, *args, **kwargs)

    def debug_variable(self, variable, *args, **kwargs):
        from collections import Sized
        name = kwargs.get('name', None)
        if name is None:
            log_info = '[variable]: content {:s} and of type {:s} '.format(str(variable), str(type(variable)),)
        else:
            log_info = '[variable]: name {:s} content {:s} and of type {:s} '.format(
                        name, str(variable), str(type(variable)),
                    )
        if isinstance(variable, Sized):
            log_info += ', of size {}'.format(len(variable))
        if self.isEnabledFor(logging.DEBUG):
            self._log(logging.DEBUG, log_info, args, **kwargs)

    def debug_if(self, check: bool, msg: str, *args, **kwargs):
        if check is True and self.isEnabledFor(logging.DEBUG):
            self._log(logging.DEBUG, msg, args, **kwargs)

    def info_if(self, check: bool, msg: str, *args, **kwargs):
        if check is True and self.isEnabledFor(logging.INFO):
            self._log(logging.INFO, msg, args, **kwargs)

    def warning_if(self, check: bool, msg: str, *args, **kwargs):
        if check is True and self.isEnabledFor(logging.WARNING):
            self._log(logging.WARNING, msg, args, **kwargs)

    def warning_at(self, process: str, msg: str, *args, **kwargs):
        if self.isEnabledFor(logging.WARNING):
            self._log(logging.WARNING, 'process {} warns {}'.format(process, msg), *args, **kwargs)

    def error_if(self, check: bool, msg: str, *args, **kwargs):
        if check is True and self.isEnabledFor(logging.ERROR):
            self._log(logging.ERROR, msg, args, **kwargs)


def get_logger(module_name: str, log_file: str = None, **kwargs):
    """

    :param module_name: str/object
    :return: :class:`~logging.Logger`
    """
    log_level = kwargs.get('log_level', logging.DEBUG)
    assert isinstance(log_level, int), '日志输出级别 log_level 需要设置为 int 而非 {}'.format(type(log_level))

    logger = LogWrapper(module_name, logging.DEBUG)
    # logger.setLevel(log_level)

    screen_handler = logging.StreamHandler()
    screen_handler.setFormatter(logging.Formatter('%(filename)s %(lineno)d %(levelname)s: %(message)s'))
    logger.addHandler(screen_handler)

    if log_file is not None:
        from os import path, makedirs
        assert isinstance(log_file, str), '日志输出路径不可以设置为 {}'.format(log_file)

        log_file_folder = log_file.split(path.sep)
        log_file_folder.pop(-1)
        log_file_folder = path.sep.join(log_file_folder)

        if not log_file.lower().endswith('log'):
            log_file = '{}.log'.format(log_file)

        if not path.exists(log_file_folder):
            makedirs(log_file_folder, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode='w', encoding='gb18030')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(filename)s %(funcName)s %(lineno)d:  %(levelname)s, %(message)s'
        ))
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    return logger
