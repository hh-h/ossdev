# coding: utf-8

''' Базовый класс для работы со свитчами '''

from netsnmp import VarList, Varbind
from BulkSession import BulkSession as Session
from json import dumps
from time import sleep
from Status import Status
from os import system
from netaddr import EUI, NotRegisteredError


class Switch(object):
    ''' Базовый класс для работы со свитчами '''

    def __init__(self, di, ip):
        self.community = di['community']
        self.user = di['user']
        self.password = di['password']
        self.version = di['version']
        self.ip = ip
        self.sess = Session(Version=self.version, DestHost=self.ip, Community=self.community)

    def __available_by_system_ping(self):
        ''' Возвращает True если свитч ответил на пинг, False в случае таймаута или другой ошибки '''
        res = system('/bin/ping -c1 -q -W2 {0} >/dev/null 2>&1'.format(self.ip))
        if res == 0:
            return True
        return False

    def get_switch_status(self):
        ''' Возвращает статус свитча '''
        oid_descr = VarList(Varbind('iso.3.6.1.2.1.1.1.0'))
        descr, = self.sess.get(oid_descr)
        status = 'success'
        if not descr:
            status = 'danger'
            r = self.__available_by_system_ping()
            if r:
                status = 'warning'

        return dumps({
            'status'    : Status.SUCCESS,
            'swstatus'  : status
        })

    def get_snmp_port_status(self, port):
        ''' Принимает айпи свитча и порт Возвращает его статус '''

        if_index = self.get_snmp_port_number(port)

        # switch down by snmp
        if not if_index:
            stport = 'muted'
            stswitch = 'danger'
            # если свитч не ответил по снмп, попробуем пингануть
            r = self.__available_by_system_ping()
            if r:
                # свитч в апе, проблема в снмп коммунити
                stswitch = 'warning'
            return dumps({
                'isup'          : 0,
                'statusswitch'  : stswitch,
                'statusport'    : stport,
                'ip'            : self.ip,
                'port'          : port
            })
        # гиговый порт
        if if_index < 0:
            return dumps({
                'status' : Status.ERROR
            })
        # список портов
        oid_ports = 'iso.3.6.1.2.1.2.2.1.'
        oids = VarList()
        # 7 - admin status, 8 - oper status, 5 - port speed http://www.opennet.ru/base/cisco/cisco_snmp.txt.html
        for index in 7, 8, 5:
            oid = Varbind('{0}{1}.{2}'.format(oid_ports, index, if_index))
            oids.append(oid)

        # лист со статусом портов, административный и оперативный, 1 - up, 2 - down
        ret = self.sess.get(oids)
        admin = 0 if ret[0] == '2' else 1
        oper = ret[1]
        speed = int(ret[2]) / 1000000

        # None - error, 1 = port up, 2 = port down
        sw_status = 'success'
        port_status = 'muted'
        if not oper:
            port_status = 'muted'
        elif oper == '2':
            port_status = 'danger'
        elif oper == '1':
            if speed == 100:
                port_status = 'success'
            else:
                port_status = 'warning'

        return dumps({
            'isup'          : 1,
            'statusswitch'  : sw_status,
            'statusport'    : port_status,
            'statusadmin'   : admin,
            'ip'            : self.ip,
            'port'          : port
        })

    def get_snmp_all_ports_status(self):
        ''' Возвращает статус всех портов на свитче '''
        oid_typeport = 'iso.3.6.1.2.1.2.2.1.3'
        oid_status = 'iso.3.6.1.2.1.2.2.1.8'

        var_types = self.sess.bulkwalk(oid_typeport)
        if not var_types:
            return dumps({
                'status' : Status.ERROR
            })

        var_status = self.sess.bulkwalk(oid_status)
        if not var_status:
            return dumps({
                'status' : Status.ERROR
            })

        if len(var_status) != len(var_types):
            return dumps({
                'status' : Status.ERROR
            })

        # собираем статус всех портов, у которых тип порта = 6 (100мб\с)
        ports = [int(j) for (i, j), (x, y) in zip(var_status, var_types) if int(y) == 6]
        return dumps({
            'status' : Status.SUCCESS,
            'data'   : ports
        })

    def get_snmp_port_number(self, port):
        ''' Получаем ifIndex порта , -1 если порт не 100Мб/с, False если свитч лежит '''
        # тип порта http://www.opennet.ru/base/cisco/cisco_snmp.txt.html
        oid_typeport = 'iso.3.6.1.2.1.2.2.1.3'
        var_types = VarList(Varbind(oid_typeport))

        var_types = self.sess.bulkwalk(oid_typeport)

        if not var_types:
            return False

        # получаем список пар (тип порта, снмп индекс) только для портов ethernet_csmacd ('6')
        ports = [tag.split('.')[-1] for tag, val in var_types if int(val) == 6]

        # снмп индекс нужного нам порта
        if port <= len(ports):
            return int(ports[port - 1])
        return -1

    def change_port_status(self, port, trigger):
        if_index = self.get_snmp_port_number(port)
        if not if_index or if_index < 0:
            return dumps({
                'status' : Status.ERROR
            })
        oid_str = 'iso.3.6.1.2.1.2.2.1.7.{0}'.format(if_index)
        trigger = 2 if trigger == 0 else 1
        oid = VarList(Varbind(oid_str, '', trigger, 'INTEGER'))
        count = 0
        status = 0
        sleep_time = 1
        # ждем пока не вернет not null завершения теста 3/sleep_time = 3sec
        while status == 0 and count < 3:
            status = self.sess.set(oid)
            sleep(sleep_time)
            count += 1
        # чтобы порт успел подняться в веб форме
        oid = VarList(Varbind('iso.3.6.1.2.1.2.2.1.8.{0}'.format(if_index)))
        count = 0
        status = 0
        sleep_time = 1
        while int(status) != trigger and count < 10:
            status, = self.sess.get(oid)
            sleep(sleep_time)
            count += 1

            if not status:
                return dumps({
                    'status' : Status.ERROR
                })

        return dumps({
            'status' : Status.SUCCESS
        })

    @staticmethod
    def convert_descr(descr):
        if not descr:
            return '??', 'muted'
        descr = descr.strip().lower()
        if descr in ('normal,', 'ok', '0'):
            return 'OK', 'success'
        elif descr in ('open', 'abnormal(open),', '1'):
            return 'OP', 'info'
        elif descr in ('short', 'abnormal(short),', '2'):
            return 'SH', 'danger'
        elif descr in ('7'):
            return 'NO', 'primary'
        else:
            print('new Cabdiag status: {0}'.format(descr))
            return '??', 'muted'

    def get_macs(self, port):
        macs = self._get_macs(port)
        if not macs:
            return dumps({
                'status': Status.EMPTY
            })

        data = {}

        for mac in macs:
            org = ''
            try:
                org = EUI(mac).oui.registration().org
            except NotRegisteredError:
                pass
            data[mac] = org

        return dumps({
            'status' : Status.SUCCESS,
            'data'   : data
        })

    def get_local_lldp_ports(self):
        oid_lldp_local = 'iso.0.8802.1.1.2.1.3.7.1.3'
        var_lldp = self.sess.bulkwalk(oid_lldp_local)

        if not var_lldp:
            return False

        return [v for k, v in var_lldp]
