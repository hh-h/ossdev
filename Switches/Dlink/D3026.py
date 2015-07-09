# coding: utf8

from json import dumps
from Dlink import Dlink
from Status import Status


class D3026(Dlink):
    """ Класс для работы со свитчем Dlink 3026 """

    def cable_test_all(self):
        return dumps({
            'status' : Status.ERROR,
            'msg'    : 'Масс каб диаг на Dlink 3026 временно не поддерживается!'
        })
