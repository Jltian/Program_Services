# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import logging


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


__log_leval_map__ = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


def get_logger(module_name: str, log_level=logging.DEBUG, log_path: str = None):

    if isinstance(log_level, int):
        log_level = log_level
    elif isinstance(log_level, str):
        try:
            log_level = __log_leval_map__[log_level]
        except KeyError:
            raise ValueError('param log_level should be in range {} but got {}.'.format(
                str(list(__log_leval_map__.keys())), str(log_level),
            ))
    else:
        raise ValueError('param log_level should be in int/str but got {} with value {}.'.format(
            type(log_level), str(log_level)
        ))

    logger = LogWrapper(module_name, log_level)

    screen_handler = logging.StreamHandler()
    screen_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(filename)s %(lineno)d %(levelname)s: %(message)s'
    ))
    screen_handler.setLevel(log_level)
    logger.addHandler(screen_handler)

    if log_path is not None:
        import os
        if not isinstance(log_path, str):
            raise ValueError('param log_path should be in type str but got {}'.format(type(log_path)))
        folder_path = os.path.split(log_path)[0]

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(filename)s %(funcName)s %(lineno)d:  %(levelname)s, %(message)s'
        ))
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    return logger
