# -*- encoding: UTF-8 -*-
import datetime
import json

from jetend.structures import SocketClient, SocketMessage, SocketServer


class WindStatusCode:
    STATUS_SUCCESS = 0
    STATUS_ARGS_ERROR = -100
    STATUS_FUNC_ERROR = -999


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y%m%d')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y%m%d')
        else:
            return json.JSONEncoder.default(self, obj)


class WSDRes(object):
    def __init__(self, response: dict):
        self.ErrorCode = response['ErrorCode']
        self.Codes = response['Codes']
        self.Fields = response['Fields']
        self.Times = [datetime.datetime.strptime(var, '%Y%m%d').date() for var in response['Times']]
        self.Data = response['Data']


class WindClient(SocketClient, WindStatusCode):
    def __init__(self, host: str, port: int = 33331, **kwargs):
        SocketClient.__init__(self, host=host, port=port, **kwargs)

    def wsd(self, codes: str, fields: str, start_date: datetime.date, end_date: datetime.date, options: str = ''):
        self.msg_lock.acquire()
        # self.msg_lock.locked()
        self.msg_out.put(json.dumps({
            'func': 'wsd',
            'args': (codes, fields, start_date, end_date, options)
        }, cls=ComplexEncoder))
        res = json.loads(self.msg_in.get())
        self.msg_lock.release()
        if res['status'] == self.STATUS_SUCCESS:
            return WSDRes(res)
        else:
            self.__process_error__(res)

    def __process_error__(self, e_dict: dict):
        if e_dict['status'] == self.STATUS_FUNC_ERROR:
            raise NotImplementedError
        elif e_dict['status'] == self.STATUS_ARGS_ERROR:
            raise ValueError
        else:
            raise NotImplementedError


class WindServer(SocketServer, WindStatusCode):
    def __init__(self, **kwargs):
        SocketServer.__init__(self, **kwargs)
        self.engine = None

    def on_new_client(self, sock_addr: str):
        from WindPy import w
        self.log.debug('new connection arrived {}'.format(sock_addr))
        self.engine = w
        self.engine.start()

    def process_msg(self):
        while self.__process_tag__ is True:
            msg_obj = self.msg_in.get()
            assert isinstance(msg_obj, SocketMessage)
            msg = json.loads(msg_obj.msg)
            if msg['func'] == 'wsd':
                try:
                    args = msg['args']
                    res = self.engine.wsd(*args)
                    res_msg = json.dumps({
                        'status': self.STATUS_SUCCESS,
                        'ErrorCode': res.ErrorCode, 'Codes': res.Codes,
                        'Fields': res.Fields, 'Times': res.Times, 'Data': res.Data,
                    }, cls=ComplexEncoder)
                except KeyError:
                    res_msg = json.dumps({'status': self.STATUS_ARGS_ERROR, })
            else:
                res_msg = json.dumps({'status': self.STATUS_FUNC_ERROR, })
                self.log.warning('Unknown command from {}: {}'.format(msg_obj.addr, msg_obj.msg))
            self.msg_out.put(SocketMessage(msg_obj.addr, res_msg))
