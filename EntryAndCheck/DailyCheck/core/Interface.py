# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime

from jetend import get_logger


class AbstractLoader:
    log = get_logger('LoaderPart', )

    # @staticmethod
    # def load_simple_normal(file_path: str, product: str, date: datetime.date, institution: str, ):
    #     raise NotImplementedError

    @staticmethod
    def root_path():
        from os import path
        file_path = path.abspath(path.dirname(__file__)).split(path.sep)
        file_path.pop(-1)
        file_path = path.sep.join(file_path)
        return file_path

    @staticmethod
    def load_swap_excel(file_path: str, product: str, date: datetime.date, account_type: str, ):
        raise NotImplementedError

    @staticmethod
    def load_normal_text(content_text: str, product: str, date: datetime.date, institution: str):
        raise NotImplementedError

    @staticmethod
    def load_normal_excel(file_path: str, product: str, date: datetime.date, institution: str):
        raise NotImplementedError

    @staticmethod
    def load_simple_margin(file_path: str, product: str, date: datetime.date, institution: str, ):
        raise NotImplementedError

    @staticmethod
    def load_future_excel(file_path: str, product: str, date: datetime.date, institution: str):
        raise NotImplementedError

    @staticmethod
    def load_future_csv(file_path: str, product: str, date: datetime.date, institution: str):
        raise NotImplementedError

    # @property
    # def log(self):
    #     from jetend.structures import LogWrapper
    #     if not isinstance(AbstractLoader.__log__, LogWrapper):
    #         from jetend import get_logger
    #         AbstractLoader.__log__ = get_logger('LoaderPart', )
    #     logger = AbstractLoader.__log__
    #     assert isinstance(logger, LogWrapper)
    #     return logger
