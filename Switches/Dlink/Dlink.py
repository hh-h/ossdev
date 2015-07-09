# coding: utf8

from ..Switch import Switch
from Status import Status
from json import dumps
from time import sleep
from netsnmp import VarList, Varbind
from binascii import hexlify


class Dlink(Switch):
    """ Базовый класс для свитчей Dlink """

    def cable_test(self, port):
        oid_dlink = 'iso.3.6.1.4.1.171.12.58.1.1.1.'
        rw_cabdiag = 12
        port = self.get_snmp_port_number(port)
        if not port or port < 0:
            return dumps({
                'status' : Status.ERROR
            })
        oid_str = '{0}{1}.{2}'.format(oid_dlink, rw_cabdiag, port)
        oid = VarList(Varbind(oid_str, '', 1, 'INTEGER'))

        status = self.sess.set(oid)

        if not status:
            msg = 'not status answer {0}:{1}'.format(self.ip, port)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        count = 0
        status = 2
        sleep_time = 0.5
        # ждем пока не вернет 3 (ready for test) завершения теста 6/sleep_time = 3sec
        oid = VarList(Varbind(oid_str))
        while status != '3' and count < 6:
            status, = self.sess.get(oid)
            sleep(sleep_time)
            count += 1

        # формируем запрос со всеми оидами
        oids = VarList()
        # 4-7 status pair 1-4, 8-11 length pair 1-4
        for index in 4, 5, 8, 9:
            oid = Varbind('{0}{1}.{2}'.format(oid_dlink, index, port))
            oids.append(oid)

        # лист с количеством ошибок на каждом счетчике
        res = self.sess.get(oids)

        # частный случай, длинк не может промерить кабель, так как он вставлен в активное оборудование
        if all(x == '0' for x in res):
            return dumps({
                'status' : Status.CBNOINFO
            })
        data = {}
        p1, col1 = Switch.convert_descr(res[0])
        p2, col2 = Switch.convert_descr(res[1])
        len1 = int(res[2])
        len2 = int(res[3])
        data['p1col'] = col1
        data['p1st'] = p1
        data['p1len'] = len1
        data['p2col'] = col2
        data['p2st'] = p2
        data['p2len'] = len2

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

        t = {int(i.split('.')[-1]): int(y) for (i, j), (x, y) in zip(var_types, var_status) if int(j) == 6}
        data = {i + 1: k for i, (k, v) in enumerate(sorted(t.iteritems())) if v == 2}

        oid_dlink = 'iso.3.6.1.4.1.171.12.58.1.1.1.'
        rw_cabdiag = 12

        oids = []
        for port in data.values():
            oid_str = '{0}{1}.{2}'.format(oid_dlink, rw_cabdiag, port)
            oid = Varbind(oid_str, '', 1, 'INTEGER')
            oids.append(oid)

        for oid in oids:
            self.sess.set(VarList(oid))

        count = 0
        status = ''
        sleep_time = 0.5
        # ждем пока не вернет 3 (ready for test) завершения теста 6/sleep_time = 3sec
        oid = '{0}{1}'.format(oid_dlink, rw_cabdiag)
        while not status and not all(val == '3' for tag, val in status) and count < 6:
            status = self.sess.bulkwalk(oid)
            sleep(sleep_time)
            count += 1

        for k, port in data.iteritems():
            # 4-7 status pair 1-4, 8-11 length pair 1-4
            oids = VarList()
            for index in 4, 5, 8, 9:
                oid = Varbind('{0}{1}.{2}'.format(oid_dlink, index, port))
                oids.append(oid)

            res = self.sess.get(oids)

            # частный случай, длинк не может промерить кабель, так как он вставлен в активное оборудование
            if all(x == '0' for x in res):
                data[k] = {
                    'status' : Status.CBNOINFO
                }
                continue
            tmp = {}
            p1, col1 = Switch.convert_descr(res[0])
            p2, col2 = Switch.convert_descr(res[1])
            len1 = int(res[2])
            len2 = int(res[3])
            tmp['p1col'] = col1
            tmp['p1st'] = p1
            tmp['p1len'] = len1
            tmp['p2col'] = col2
            tmp['p2st'] = p2
            tmp['p2len'] = len2

            data[k] = {
                'status': Status.SUCCESS,
                'data'  : tmp
            }

        return dumps({
            'status': Status.SUCCESS,
            'data'  : data
        })

    def get_count_port_errors(self, port, curr):
        """ Считывает по snmp количество ошибок на порту клиента
        Принимает массив с айпи свитча (ip), снмп-портом (port) и текущим количеством ошибок (cur)
        Возвращает количество ошибок и дельту, если в запросе было указано
        количество ошибок уже """

        # dlink stored info about ports
        oid_errors = 'iso.3.6.1.2.1.2.2.1.'

        counts = (14, 20)

        # Может быть не надо, но запрос быстрый, так что оставим
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

        oid_macs = 'iso.3.6.1.2.1.17.7.1.2.2.1.2'

        result = self.sess.bulkwalk(oid_macs)
        if not result:
            return False

        return [hexlify(bytearray(map(int, x.split('.')[-6:]))) for x, y in result if int(y) == port]
