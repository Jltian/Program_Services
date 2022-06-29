# -*- encoding: UTF-8 -*-
from jetend import get_logger


class AbstractInstitution:
    log = get_logger('InstitutionLoader')
    folder_institution_map = tuple()

    @staticmethod
    def load_normal(folder_path: str, date):
        raise NotImplementedError

    @staticmethod
    def load_margin(folder_path: str, date):
        raise NotImplementedError

    @staticmethod
    def load_future(folder_path: str, date):
        raise NotImplementedError

    @staticmethod
    def load_option(folder_path: str, date):
        raise NotImplementedError

    @staticmethod
    def load_swap(folder_path: str, date):
        raise NotImplementedError

    @staticmethod
    def load_valuation_table(file_path: str):
        raise NotImplementedError
