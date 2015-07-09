# coding: utf8

from Huawei import Huawei
from json import dumps
from Status import Status
from ..Switch import Switch
from netsnmp import VarList, Varbind
from binascii import hexlify


class CX200(Huawei):
    """ Класс для работы со свитчами Huawei, model CX200 """

    def cable_test(self, port):
        """ Кабельная диагностика """
        oid_diag = 'iso.3.6.1.4.1.2011.5.25.31.1.1.7.1.'

        port = self.get_snmp_port_number(port)
        if not port or port < 0:
            return dumps({
                'status' : Status.ERROR
            })

        count = 10
        for c in xrange(count):
            oids = VarList()
            # 2 - status, 3 - length
            for index in 2, 3:
                oid_str = '{0}{1}.{2}'.format(oid_diag, index, port)
                oid = Varbind(oid_str)
                oids.append(oid)

            res = self.sess.get(oids)

            if not res:
                msg = 'not status answer {0}:{1}'.format(self.ip, port)
                print(msg)
                return dumps({
                    'status' : Status.ERROR,
                    'msg'    : msg
                })

            if res[1] not in ('150', '204'):
                break
            elif c + 1 == count:
                return dumps({
                    'status' : Status.CBNOINFO
                })

        data = {}
        status = int(res[0]) - 1
        p1, col1 = Switch.convert_descr(str(status))
        len1 = int(res[1])
        data['p1col'] = col1
        data['p1st'] = p1
        data['p1len'] = len1

        return dumps({
            'status': Status.SUCCESS,
            'data'  : data
        })

    def cable_test_all(self):
        """ Возвращает результат кабдиага на всех портах кроме активных и где активный договор """

        # получим список всех 100мб портов
        oid_typeport = 'iso.3.6.1.2.1.2.2.1.3'
        oid_status = 'iso.3.6.1.2.1.2.2.1.8'

        var_types = self.sess.bulkwalk(oid_typeport)
        if not var_types:
            msg = 'Предположительно свитч лежит!'
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        var_status = self.sess.bulkwalk(oid_status)
        if not var_status:
            msg = 'Предположительно свитч лежит!'
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        if len(var_types) != len(var_status):
            print('len not equal on switch {0}'.format(self.ip))
            return dumps({
                'status' : Status.ERROR
            })

        l = [int(y) for (i, j), (x, y) in zip(var_types, var_status) if int(j) == 6]
        data = {i + 1: i + 1 for i, v in enumerate(l) if v == 2}

        tn = self.login()
        if not tn:
            return dumps({
                'status': Status.CANTESTABLISH
            })

        for k, port in data.iteritems():
            tn.write('display cable interface Ethernet 0/0/{0}\n'.format(port))
            res = tn.read_until(']', 5)
            res = res.split('\n')[1].split()
            status, color = Switch.convert_descr(res[4])
            lenght = int(res[5])

            tmp = {}
            tmp['p1col'] = color
            tmp['p1st'] = status
            tmp['p1len'] = lenght

            data[k] = {
                'status': Status.SUCCESS,
                'data'  : tmp
            }

        tn.close()

        return dumps({
            'status': Status.SUCCESS,
            'data'  : data
        })

    def get_count_port_errors(self, port, curr):
        """ Количество ошибок на порту """

        oid_errors = 'iso.3.6.1.2.1.2.2.1.'

        counts = (14, 20)

        if_index = self.get_snmp_port_number(port)
        if not if_index or if_index < 0:
            return dumps({
                'status' : Status.ERROR
            })
        # формируем запрос со всеми оидами
        oids = VarList()
        for index in counts:
            oid = Varbind('{0}{1}.{2}'.format(oid_errors, index, if_index))
            oids.append(oid)

        # лист с количеством ошибок на каждом счетчике
        res = self.sess.get(oids)

        # суммируем ошибки
        errors = 0
        for count in res:
            errors += int(count)

        delta = 0
        if curr > 0:
            delta = errors - int(curr)

        return dumps({
            'status' : Status.SUCCESS,
            'errors' : errors,
            'delta'  : delta
        })

    def _get_macs(self, port):
        """ Принимает порт и возвращает все маки на порту """

        oid_ports = 'iso.3.6.1.2.1.17.4.3.1.2'

        var_ports = self.sess.bulkwalk(oid_ports)
        if not var_ports:
            return False

        return [hexlify(bytearray(map(int, x.split('.')[-6:]))) for x, y in var_ports if int(y) == port]
