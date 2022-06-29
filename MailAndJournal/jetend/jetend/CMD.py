# -*- encoding: UTF-8 -*-
"""
Socketer:
    Proudly presented by JM.

Usage:
    sockter -w | --wind
    sockter -h | --help
    sockter -v | --version

Tips:
    Please hit Ctrl-C to exit.

Options:
    -w --wind        Start Wind Server
    -h --help        Show this help message and exit.
    -v --version     Show version.
"""
import time

from docopt import docopt


class socketer():

    def __init__(self, **kwargs):
        self.__args__ = kwargs

    def get_command(self):
        """ 处理命令行参数 """
        if '-w' in self.__args__ or '--wind' in self.__args__:
            from jetend import WindServer
            wind_server = WindServer()
            try:
                wind_server.start()
                while wind_server.is_alive():
                    time.sleep(5)
                wind_server.stop()
            except KeyboardInterrupt:
                wind_server.stop()
                exit(0)
            else:
                exit(0)
        else:
            pass


def entry_socketer():
    """ 入口方法 """
    from jetend import __version__
    args = docopt(__doc__, version='jetend.Socketer {}'.format(__version__))
    socketer(**args).get_command()


if __name__ == '__main__':
    entry_socketer()
