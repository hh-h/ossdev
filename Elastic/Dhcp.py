# coding: utf-8

""" Класс для работы с таблицами из базы данных DHCP """

from Elastic import Elastic
from Helpers import check_ip
from re import match
from cgi import escape
from Status import Status
from json import dumps


class Dhcp(Elastic):
    """ Класс для работы с таблицами из базы данных DHCP """

    def get_dhcp_short_logs(self, ip):
        """ Принимает ip клиента и возвращает его логи на DHCP """
        query = {
            'query' : {
                'match' : {
                    'ip' : ip
                }
            },
            'sort' : {
                '@timestamp' : {
                    'order' : 'desc'
                }
            },
            'size' : 8
        }
        ret = self.search_all(query)

        if ret['hits']['total'] == 0:
            return dumps({
                'status'    : Status.EMPTY
            })

        result = []
        for hit in ret['hits']['hits']:
            hit = hit['_source']
            row = {
                'time'  : hit['time'],
                'srv'   : hit['server_host'][:5],
                'type'  : hit['command'],
                'ip'    : hit['ip'],
                'mask'  : hit['mask'],
                'gw'    : hit['gw'],
                'mac'   : hit['mac'],
                'host'  : escape(hit['cl_host'].encode('utf8')),
                'swip'  : hit['swip'],
                'swp'   : hit['swport']

            }
            result.append(row)

        return dumps({
            'status'    : Status.SUCCESS,
            'data'      : result
        })

    def get_dhcp_full_logs(self, data):
        terms = []
        exclude = []

        size = 100
        if data['rows']:
            try:
                size = int(data['rows'])
            except ValueError:
                pass
            if size > 500 or size < 1:
                size = 100

        if data['ip']:
            data_ip = data['ip'].strip()
            excl = data_ip.startswith('!')
            if excl:
                data_ip = data_ip.replace('!', '')
            ip = check_ip(data_ip)
            if ip:
                if excl:
                    exclude.append({'match': {'ip': ip}})
                else:
                    terms.append({'match': {'ip': ip}})

        if data['mac']:
            mac = data['mac'].lower().strip()
            if ':' in mac:
                mac = mac.replace(':', '')
            if '-' in mac:
                mac = mac.replace('-', '')
            excl = mac.startswith('!')
            if excl:
                mac = mac.replace('!', '')
            if match(r'^[0-9a-f]{12}$', mac):
                if excl:
                    exclude.append({'match': {'mac': mac}})
                else:
                    terms.append({'match': {'mac': mac}})

        if data['host']:
            host = escape(data['host'].strip())
            excl = host.startswith('!')
            if excl:
                host = host[1:]
                exclude.append({'match': {'cl_host': host}})
            else:
                terms.append({'match': {'cl_host': host}})

        if data['switch']:
            data_swip = data['switch'].strip()
            excl = data_swip.startswith('!')
            if excl:
                data_swip = data_swip.replace('!', '')
            swip = check_ip(data_swip)
            if swip:
                if excl:
                    exclude.append({'match': {'swip': swip}})
                else:
                    terms.append({'match': {'swip': swip}})

        if data['port']:
            data_port = data['port'].strip()
            excl = data_port.startswith('!')
            if excl:
                data_port = data_port.replace('!', '')
            port = 0
            try:
                port = int(data_port)

            except ValueError:
                pass
            if port:
                if excl:
                    exclude.append({'match': {'swport': port}})
                else:
                    terms.append({'match': {'swport': port}})

        if not terms and not exclude:
            return dumps({
                'status'    : Status.EMPTY
            })

        query = {
            'query': {
                'bool': {
                    'must': terms,
                    'must_not' : exclude
                }
            },
            'sort' : {
                '@timestamp' : {
                    'order' : 'desc'
                }
            },
            'size' : size
        }

        res = self.search_all(query)

        if res['hits']['total'] == 0:
            return dumps({
                'status'    : Status.EMPTY
            })

        result = []
        for hit in res['hits']['hits']:
            hit = hit['_source']
            row = {}
            row['time'] = hit['time']
            row['server'] = hit['server_host'][:5]
            row['type'] = hit['command']
            row['ip'] = hit['ip']
            row['gw'] = hit['gw']
            row['mac'] = hit['mac']
            row['host'] = escape(hit['cl_host'].encode('utf8'))
            row['swp'] = '{0} : {1}'.format(hit['swip'], hit['swport'])
            result.append(row)

        return dumps({
            'status': Status.SUCCESS,
            'data'  : result
        })
