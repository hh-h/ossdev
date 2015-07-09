# coding: utf8

from netsnmp import Session, VarList, Varbind
from Status import Status
from re import search, compile
from Switches.Dlink.Dlink import Dlink
from Switches.Dlink.D3026 import D3026
from Switches.Huawei.S2300 import S2300
from Switches.Huawei.CX200 import CX200
from Switches.Huawei.S3328 import S3328


class SimpleSwitchFactory(object):
    """ Фабрика свитчей """

    def __init__(self, di):
        self.swconf = di
        self.community = self.swconf['community']
        self.version = self.swconf['version']

    def get_switch_model(self, ip):
        """ Возвращает класс свитча """

        oid_system = 'iso.3.6.1.2.1.1.1.0'
        sess = Session(Version=self.version, DestHost=ip, Community=self.community)
        cl, = sess.get(VarList(Varbind(oid_system)))

        if not cl:
            return {
                'status' : Status.ERROR,
                'msg'    : 'Предположительно свитч лежит!'
            }

        pattern = compile('(?:D[GE]S|D-Link)')
        if 'Huawei' in cl:
            if 'S2300' in cl:
                return {
                    'status' : Status.SUCCESS,
                    'sw'     : S2300(self.swconf, ip)
                }
            elif 'CX200' in cl:
                return {
                    'status' : Status.SUCCESS,
                    'sw'     : CX200(self.swconf, ip)
                }
            elif 'S3328' in cl:
                return {
                    'status' : Status.SUCCESS,
                    'sw'     : S3328(self.swconf, ip)
                }
            else:
                print(cl)
                return {
                    'status' : Status.NOTFOUND
                }
        elif search(pattern, cl):
            if '3026' in cl:
                return {
                    'status' : Status.SUCCESS,
                    'sw'     : D3026(self.swconf, ip)
                }
            return {
                'status' : Status.SUCCESS,
                'sw'     : Dlink(self.swconf, ip)
            }
        print(cl)
        return {
            'status' : Status.NOTFOUND
        }
