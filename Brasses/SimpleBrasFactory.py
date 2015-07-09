# coding: utf8

from Brasses.E120 import E120
from Brasses.ASR import ASR
from Brasses.MA5200 import MA5200
from Brasses.LISG import LISG


class SimpleBrasFactory(object):
    ''' Возвращает инстанс браса по имени '''
    @staticmethod
    def get_bras_by_name(name, config):
        if name == 'ASR':
            return ASR(config)
        elif name == 'MA5200':
            return MA5200(config)
        elif name == 'E120':
            return E120(config)
        elif name == 'LISG':
            return LISG(config)
        else:
            print('dont know about {0}'.format(name))
            return None
