# -*- encoding: UTF-8 -*-
import datetime
import logging


# ----------------------------- [config] -----------------------------
def load_yaml(path: str):
    import yaml
    # loader = yaml.Loader(open(path, mode='r', encoding='utf-8')).get_single_data()
    with open(path, mode='r', encoding='utf-8') as file:
        return yaml.Loader(file).get_single_data()


# ----------------------------- [log] -----------------------------
class LogWrapper(logging.Logger):

    def __init__(self, name: str, level=logging.NOTSET):
        super(LogWrapper, self).__init__(name=name, level=level)

    @staticmethod
    def time_sleep(seconds):
        from time import sleep
        sleep(seconds)

    def debug_running(self, *args, **kwargs):
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


def get_logger(module_name: str):
    """

    :param module_name: str/object
    :return: :class:`~logging.Logger`
    """
    from core.Environment import Environment
    env = Environment.get_instance()
    config = env.config.get('Log', {
        'LogLevel': 'debug', 'LogFile': False, 'LogFolder': 'log'
    })

    log_level = __log_leval_map__[config.get('LogLevel', 'debug')]
    log_file_output = config.get('LogFile', False)
    log_file_folder = config.get('LogFolder', 'log')

    logger = LogWrapper(module_name, log_level)
    logger.setLevel(log_level)

    screen_handler = logging.StreamHandler()
    screen_handler.setFormatter(logging.Formatter(
        '%(filename)s %(lineno)d %(levelname)s: %(message)s'
    ))
    logger.addHandler(screen_handler)

    if log_file_output is True:
        import os
        # try:
        #     log_path = env.get_file_log_path()
        # except AttributeError:
        current_path = os.path.abspath(os.path.dirname(__file__))
        current_path = current_path.split(os.path.sep)
        current_path.pop()
        log_path = os.path.join(os.path.sep.join(current_path), log_file_folder)

        if not os.path.exists(log_path):
            os.makedirs(log_path)
        file_handler = logging.FileHandler(os.path.join(log_path, module_name + '.log'))
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(filename)s %(funcName)s %(lineno)d:  %(levelname)s, %(message)s'
        ))
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    return logger


def get_entry_generation_logger(module_name: str, date: datetime.date):
    """

    :param module_name: str/object
    :return: :class:`~logging.Logger`
    """
    import os
    from core.Environment import Environment
    env = Environment.get_instance()

    logger = LogWrapper(module_name, logging.DEBUG)
    # logger.setLevel(logging.INFO)

    screen_handler = logging.StreamHandler()
    screen_handler.setFormatter(logging.Formatter(
        '%(filename)s %(lineno)d %(levelname)s: %(message)s'
    ))
    screen_handler.setLevel(logging.DEBUG)
    logger.addHandler(screen_handler)

    log_path = os.path.join(env.root_path(), 'temp')
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    file_handler = logging.FileHandler(os.path.join(log_path, '{}_{}.log'.format(module_name, date)))
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(filename)s %(funcName)s %(lineno)d:  %(levelname)s, %(message)s'
    ))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    return logger


def get_journal_logger(module_name: str):
    """

    :param module_name: str/object
    :return: :class:`~logging.Logger`
    """
    import os
    logger = LogWrapper(module_name, logging.DEBUG)

    screen_handler = logging.StreamHandler()
    screen_handler.setFormatter(logging.Formatter(
        '%(filename)s %(lineno)d %(levelname)s: %(message)s'
    ))
    screen_handler.setLevel(logging.INFO)
    logger.addHandler(screen_handler)

        # try:
        #     log_path = env.get_file_log_path()
        # except AttributeError:
    current_path = os.path.abspath(os.path.dirname(__file__))
    current_path = current_path.split(os.path.sep)
    current_path.pop()
    log_path = os.path.join(os.path.sep.join(current_path), 'temp')

    if not os.path.exists(log_path):
        os.makedirs(log_path)
    file_handler = logging.FileHandler(os.path.join(log_path, module_name + '.log'))
    # file_handler.setFormatter(logging.Formatter(
    #     '%(asctime)s %(filename)s %(funcName)s %(lineno)d:  %(levelname)s, %(message)s'
    # ))
    file_handler.setFormatter(logging.Formatter(
        '%(filename)s %(lineno)d:  %(levelname)s, %(message)s'
    ))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    return logger
