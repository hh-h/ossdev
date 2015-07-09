# coding: utf8

from ..Switch import Switch
from telnetlib import Telnet
from re import search, match
from json import dumps
from Status import Status
from netsnmp import VarList, Varbind
from binascii import hexlify


class Huawei(Switch):
    """ Базовый класс для свитчей вендора Huawei """

    def login(self):
        user = '{0}\n'.format(self.user)
        pwd = '{0}\n'.format(self.password)
        tn = Telnet(self.ip, 23, 5)
        res = tn.expect(['Username:'], 5)
        if res[0] == -1:
            tn.close()
            return False
        tn.write(user)
        tn.read_until('Password:', 5)
        tn.write(pwd)
        res = tn.expect(['>'], 5)
        if res[0] == -1:
            tn.close()
            return False
        tn.write('system-view\n')
        tn.read_until(']')
        return tn

    def cable_test(self, port):
        """ Кабельная диагностика """
        tn = self.login()
        if not tn:
            return dumps({
                'status': Status.CANTESTABLISH
            })

        # если кабель воткнут в активное оборудование, Huawei не может сделать
        # каб. диаг и возвращает 150м или 204м
        # попробуем сделать count раз и если не получится, вернем ошибку
        count = 10
        for c in xrange(count):
            tn.write('interface Ethernet 0/0/{0}\n'.format(port))
            tn.read_until(']', 5)
            tn.write('virtual-cable-test\n')
            res = tn.read_until('?', 5)
            if 'Error' in res:
                print('Error: old version of software on {0}'.format(self.ip))
                return dumps({
                    'status' : Status.ERROR
                })
            tn.write('y\n')

            res = tn.read_until(']', 5)

            if not search('(?:150|204)meter', res):
                break
            elif c + 1 == count:
                tn.close()
                return dumps({
                    'status' : Status.CBNOINFO
                })
        tn.close()
        # """y
        # Pair A length: 0meter(s)
        # Pair B length: 0meter(s)
        # Pair A state: Unknown
        # Pair B state: Unknown
        # [SPB_AN1608_C_2]"""

        if not res or 'failed' in res:
            return dumps({
                'status' : Status.ERROR
            })

        result = []
        for i in res.splitlines()[1:5]:
            i = i.split()
            to_add = i[3]
            if i[2] == 'length:':
                m = match(r'\d+', to_add)
                if not m:
                    # Что-то пошло совсем не так
                    print('Error in cabdiag {0}'.format(self.ip))
                    return dumps({
                        'status' : Status.ERROR
                    })
                to_add = m.group(0)
            result.append(to_add)

        if len(result) != 4:
            msg = 'returned not four values "{0}"'.format(result)
            print(msg)
            return dumps({
                'status' : Status.ERROR
            })

        data = {}
        p1, col1 = Switch.convert_descr(result[2])
        p2, col2 = Switch.convert_descr(result[3])
        len1 = int(result[0])
        len2 = int(result[1])
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

        l = [int(y) for (i, j), (x, y) in zip(var_types, var_status) if int(j) == 6]
        data = {i + 1: i + 1 for i, v in enumerate(l) if v == 2}

        tn = self.login()
        if not tn:
            return dumps({
                'status': Status.CANTESTABLISH
            })
        for k, port in data.iteritems():
            tn.write('interface Ethernet 0/0/{0}\n'.format(port))
            tn.read_until(']', 5)
            tn.write('virtual-cable-test\n')
            res = tn.read_until('?', 5)
            if 'Error' in res:
                print('Error: old version of software on {0}'.format(self.ip))
                tn.close()
                return dumps({
                    'status' : Status.ERROR
                })
            tn.write('y\n')

            res = tn.read_until(']', 5)

            if not res or 'failed' in res:
                data[k] = {
                    'status' : Status.ERROR
                }
                continue

            result = []
            for i in res.splitlines()[1:5]:
                i = i.split()
                to_add = i[3]
                if i[2] == 'length:':
                    m = match(r'\d+', to_add)
                    if not m:
                        # Что-то пошло совсем не так
                        print('Error in cabdiag {0}'.format(self.ip))
                        data[k] = {
                            'status' : Status.ERROR
                        }
                        continue
                    to_add = m.group(0)
                result.append(to_add)

            if len(result) != 4:
                msg = 'returned not four values "{0}"'.format(result)
                print(msg)
                data[k] = {
                    'status' : Status.ERROR
                }
                continue

            tmp = {}
            p1, col1 = Switch.convert_descr(result[2])
            p2, col2 = Switch.convert_descr(result[3])
            len1 = int(result[0])
            len2 = int(result[1])
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

        tn.close()

        return dumps({
            'status': Status.SUCCESS,
            'data'  : data
        })

    def get_count_port_errors(self, port, curr):
        """ Считывает по snmp количество ошибок на порту клиента
        Принимает массив с айпи свитча (ip), снмп-портом (port) и текущим количеством ошибок (cur)
        Возвращает количество ошибок и дельту, если в запросе было указано
        количество ошибок уже Huawei CX200 не поддерживается, поэтому сразу возвращает что это CX200 """

# http://support.huawei.com/enterprise/docinforeader.action?contentId=DOC1000027252&idPath=7919710|9856733|7923144|16561 (01-41 HUAWEI-IF-EXT-MIB)
        oid_errors = 'iso.3.6.1.4.1.2011.5.25.41.1.6.1.1.'

# http://support.huawei.com/enterprise/docinforeader.action?contentId=DOC1000027252&idPath=7919710|9856733|7923144|16561 (01-41 HUAWEI-IF-EXT-MIB)
        counts = (11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33)

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
        if_index = self.get_snmp_port_number(port)

        if not if_index or if_index < 0:
            print('cant get ifindex on {0} port {1} ifindex {2}'.format(self.ip, port, if_index))
            return False

        oid_ports = 'iso.3.6.1.2.1.17.4.3.1.2'

        var_ports = self.sess.bulkwalk(oid_ports)

        if not var_ports:
            return False

        return [hexlify(bytearray(map(int, x.split('.')[-6:]))) for x, y in var_ports if int(y) == if_index]
