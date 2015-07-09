# coding: utf-8

""" Класс для работы с базой данных Оранжа """

from Oracle import Oracle
from json import dumps
from Status import Status
from Helpers import check_ip, check_bill, check_sysname, MASKS, extract_port


class Orange(Oracle):
    """ Класс для работы с базой данных Оранжа """
    def get_user_params(self, bill=None, ip=None):
        """ возвращает из оранжа улицу и имя свитча, в который воткнут клиент """
        if ip:
            where = "NA.NET_ADDRESS='{0}'".format(ip)
        elif bill:
            where = "PE.AGREEMENT_NUMBER='{0}'".format(bill)
        else:
            msg = 'Неверное условие поиска!'
            return dumps({
                'status': Status.ERROR,
                'db'    : 'orange',
                'msg'   : msg
            })

        query = '''
                SELECT
                    AS IP, -- 0
                    AS MASK, -- 1
                    AS GW, -- 2
                    AS SWIP, -- 3
                    AS PORT, -- 4
                    AS SYSNAME, -- 5
                    AS ADDR, -- 6
                    AS DISTRICT, -- 7
                    AS ARNAME -- 8
            )
        '''.format(where)

        status, row = self.fetchone(query)
        if status != 0:
            msg = 'Ошибка выполнения запроса к базе данных!'
            return dumps({
                'status': Status.ERROR,
                'db'    : 'orange',
                'msg'   : msg
            })

        if not row:
            return dumps({
                'status'    : Status.EMPTY,
                'db'        : 'orange'
            })

        client_ip = row[0]
        mask = row[1]
        short_mask = mask[-2:]
        long_mask = MASKS[short_mask]
        ip_mask = "<span id='orange-ip-addr'>{0}</span> / <a href='#' id='cidr' data-value='{1}'>{2}</a>".format(client_ip, long_mask, short_mask)
        gateway = row[2]
        sw_ip = row[3]

        sw_port = extract_port(row[4])
        switch_and_port = '<a href="#" id="swIp" data-ip="{0}">{0}</a> : '.format(sw_ip)
        switch_and_port += '<span id="swPort" data-value="{0}"">{0}</span>'.format(sw_port)

        data = {
            'dhcp_ip'       : ip_mask,
            'dhcp_gw'       : gateway,
            'dhcp_swp'      : switch_and_port,
            'ora_sysname'   : row[5],
            'ora_addr'      : row[6],
            'ora_district'  : row[7],
            'ora_arname'    : row[8]
        }
        return dumps({
            'status'    : Status.SUCCESS,
            'data'      : data
        })

    def get_clients_on_switch(self, inp):
        """ Возвращает всех зарезервированных клиентов на свитче """
        ip = check_ip(inp)
        field = 'NDA.NET_ADDRESS' if ip else 'EQM.DEVICE_NAME'
        value = ip if ip else check_sysname(inp)

        if not value:
            msg = 'Не распознал условие поиска!'
            return {
                'status': Status.ERROR,
                'db'    : 'orange',
                'msg'   : msg
            }

        where = "{0} = '{1}'".format(field, value)

        query = '''
            SELECT
                NA.NET_ADDRESS,
                PE.AGREEMENT_NUMBER,
                DP.DEVICE_PORT_ID,
                DP.PORT_NAME,
                NDA.NET_ADDRESS SWIP
        '''.format(where)

        status, rows = self.fetchall(query)
        if status != 0:
            msg = 'Ошибка выполнения запроса к базе данных!'
            return {
                'status': Status.ERROR,
                'db'    : 'orange',
                'msg'   : msg
            }
        tmp = {}
        swip = ''
        for row in rows:
            sw_port = extract_port(row[3])
            tmp[sw_port] = [row[0], row[1], row[2]]
            if row[4]:
                swip = row[4]

        if not tmp:
            msg = 'На свитче нет абонентов!'
            return {
                'status': Status.EMPTY,
                'db'    : 'orange',
                'msg'   : msg
            }
        if not swip:
            msg = 'Не смог получить ip свитча!'
            print(msg)
            return {
                'status': Status.ERROR,
                'db'    : 'orange',
                'msg'   : msg
            }
        return {
            'status'    : Status.SUCCESS,
            'data'      : tmp,
            'swip'      : swip
        }

    def get_bill_id_for_ip(self, ip):
        """ Возвращает номер договора по серому айпишнику """
        query = '''
            SELECT
                PE.AGREEMENT_NUMBER,
                NA.NET_ADDRESS
        '''.format(ip)

        status, row = self.fetchone(query)
        if status != 0:
            msg = 'Ошибка выполнения запроса к базе данных!'
            return {
                'status': Status.ERROR,
                'db'    : 'orange',
                'msg'   : msg
            }
        if not row:
            return {
                'status': Status.EMPTY,
                'db'    : 'orange'
            }

        if not check_bill(row[0]):
            return {
                'status': Status.ERROR,
                'db'    : 'orange'
            }

        return {
            'status'    : Status.SUCCESS,
            'billid'    : row[0]
        }
