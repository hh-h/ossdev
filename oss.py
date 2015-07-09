# coding: utf-8

import web
import Helpers as H
from Oracle.Sbms import Sbms
from Oracle.Orange import Orange
from Elastic.Logs import Logs
from Elastic.Dhcp import Dhcp
from Switches.Switch import Switch
from Switches.SimpleSwitchFactory import SimpleSwitchFactory
from Brasses.SimpleBrasFactory import SimpleBrasFactory
from Config import Config
from json import loads, dumps, load
from Ldap import Ldap
from Status import Status
from Netadm import Netadm
from Topology import Topology

version = '1.1.1'

urls = (
    '/',                    'auth',
    '/favicon.ico',         'favicon',
    '/sbms',                'sbms',
    '/changeportstatus',    'portstatus',
    '/switch/status',       'switchstatus',
    '/switch/ports',        'switchportstatus',
    '/switch/ports/all',    'switchallportstatus',
    '/porterrors',          'porterrors',
    '/orange',              'orange',
    '/orangesw',            'orangesw',
    '/cabdiag/port',        'cabdiagport',
    '/cabdiag/ports',       'cabdiagall',
    '/main',                'main',
    '/admin',               'admin',
    '/admin/edit',          'adminedit',
    '/admin/copy',          'admincopy',
    '/admin/delete',        'admindelete',
    '/logout',              'logout',
    '/dhcp/short',          'dhcpshort',
    '/dhcp/full',           'dhcpfull',
    '/logs',                'logs',
    '/bras',                'bras',
    '/port/reserve',        'reserve',
    '/port/release',        'release',
    '/netadm',              'netadm',
    '/macs',                'macs',
    '/topology',            'topology',
    '/topology/switch',     'topologyadm',
    '/topology/switch/del', 'topologyadmdel',
    '/topology/delete',     'topologydel',
    '/topology/add',        'topologyadd',
    '/topology/ports',      'topologyports',
    '/traffic',             'traffic',
    '/users',               'users',
    '/faq',                 'faq'
)

web.config.debug = False
render = web.template.render('templates/')


brasses_list = {}

cfg = Config('config.dat')
s = cfg.get('sbms')
sb = Sbms(s)
s = cfg.get('orange')
ora = Orange(s)
swconf = cfg.get('switches')
swFactory = SimpleSwitchFactory(swconf)
brases = cfg.get('brases')
brasFactory = SimpleBrasFactory()
for key, bras in brases.iteritems():
    for k, b in bras.iteritems():
        cl = b['class']
        name = b['name']
        br = brasFactory.get_bras_by_name(cl, brases[key][name])
        if br:
            brasses_list[name] = br

s = cfg.get('logs')
log = Logs(s)
s = cfg.get('dhcp')
dh = Dhcp(s)
ldap_settings = cfg.get('auth')
na = Netadm()

app = web.application(urls, globals())
db = web.database(dbn="sqlite", db="oss.db")
store = web.session.DBStore(db, 'sessions')
initial = {
    'logged'    : False,
    'regions'   : [-1]
}
for rule in H.RULES:
    initial[rule] = 0
session = web.session.Session(app, store, initializer=initial)


def required_logged(fn):
    def wrapper(*args, **kwargs):
        if not session.get('logged', False):
            raise web.seeother('/')
        return fn(*args, **kwargs)
    return wrapper


def required_permission(perm):
    def wrapper(fn):
        def wrapped_f(*args, **kwargs):
            if not session.get(perm, False):
                return dumps({
                    'status' : Status.NOAUTH
                })
            return fn(*args, **kwargs)
        return wrapped_f
    return wrapper


def required_any_permission_in(perms):
    def wrapper(fn):
        def wrapped_f(*args, **kwargs):
            allowed = False
            for perm in perms:
                if session.get(perm, False):
                    allowed = True
                    break
            if not allowed:
                return dumps({
                    'status' : Status.NOAUTH
                })
            return fn(*args, **kwargs)
        return wrapped_f
    return wrapper


class favicon: # noqa
    ''' Отображение favicon '''
    def GET(self): # noqa
        raise web.redirect('/static/pic/favicon.ico')


class netadm: # noqa
    ''' заглушка тестовая '''
    @required_logged
    @required_permission('netadm')
    def POST(self): # noqa
        i = web.input(descr='', type='', portid='', bill='')
        if not i.portid:
            msg = 'no portid!'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        if not i.descr and not i.type and not i.bill:
            msg = 'nothing to do!'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        log.save_action(session.name, 'netadm', 'Смена {0} {1} {2}'.format(i.portid, i.bill, i.type))
        return na.store(i.portid, i.type, i.bill, i.descr)

    @required_logged
    @required_permission('netadm')
    def GET(self): # noqa
        i = web.input(data={})
        try:
            data = loads(i.data)
        except (ValueError, TypeError):
            print('cant loads data netadm')
            return dumps({
                'status' : Status.ERROR
            })
        if not data:
            print('no data to insert netadm')
            return dumps({
                'status' : Status.ERROR
            })
        return na.findall(data['device'], data['type'])


class bras: # noqa
    ''' Возвращает список брасов для клиента по номеру договора '''
    @required_logged
    @required_permission('session')
    def GET(self): # noqa
        i = web.input(bill='')
        if not i.bill:
            return dumps({
                'status': Status.ERROR
            })

        bill = H.check_bill(i.bill)
        if not bill:
            return dumps({
                'status': Status.ERROR
            })

        region = H.get_region_by_bill(bill)
        result = []
        for key, value in brases[region].iteritems():
            result.append(value['name'].upper())
        if not result:
            return dumps({
                'status' : Status.EMPTY
            })
        return dumps({
            'status' : Status.SUCCESS,
            'data'   : result
        })

    @required_logged
    @required_permission('session')
    def POST(self): # noqa
        i = web.input(bras='', action='', ip='')
        if not i.ip or not i.action or not i.bras:
            return dumps({
                'status' : Status.ERROR
            })

        if i.bras not in brasses_list:
            print('dont know dis bras {0}'.format(i.bras))
            return dumps({
                'status' : Status.ERROR
            })
        action = H.check_bras_action(i.action)
        if not action:
            print('dont know dis action {0}'.format(i.action))
            return dumps({
                'status' : Status.ERROR
            })

        ip = H.check_ip(i.ip)
        if not ip:
            return dumps({
                'status' : Status.ERROR
            })
        log.save_action(session.name, 'session', 'Делает {0} для сессии {1} на {2}'.format(action, ip, i.bras))

        return getattr(brasses_list[i.bras], H.BRAS_FUNCTIONS[action])(ip)


class sbms: # noqa
    ''' Работа с СБМС '''
    @required_logged
    @required_permission('ipaddr')
    def POST(self): # noqa
        i = web.input(inp='')
        if not i.inp:
            return dumps({
                'status'    : Status.ERROR,
                'db'        : 'sbms'
            })
        log.save_action(session.name, 'ipaddr', 'Поиск в SBMS {0}'.format(i.inp.encode('utf8')))

        bill = H.check_bill(i.inp)
        ip = None
        if not bill:
            ip = H.check_ip(i.inp)
            if not ip:
                return dumps({
                    'status'    : Status.ERROR,
                    'db'        : 'sbms'
                })
            res = ora.get_bill_id_for_ip(ip)
            if res['status'] != Status.SUCCESS:
                return dumps({
                    'status'    : Status.ERROR,
                    'db'        : 'sbms'
                })
            bill = res['billid']

        if not bill:
            return dumps({
                'status'    : Status.EMPTY,
                'db'        : 'sbms'
            })

        if not H.is_region_allowed(bill, session.regions):
            return dumps({
                'status'    : Status.NOAUTH,
                'db'        : 'sbms'
            })

        return sb.get_user_params(bill, ip)


class portstatus: # noqa
    ''' Погасить / Поднять порт на свитче '''
    @required_logged
    @required_permission('ports')
    def POST(self): # noqa
        i = web.input(ip='', port='', data='')

        if not i.ip or not i.port or not i.data:
            msg = 'wrong (empty) inputs'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'wrong ip'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        # trigger must be 1 for up or 2 for down
        try:
            trigger = int(i.data)
            port = int(i.port)
        except ValueError:
            msg = 'wrong port or trigger'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        if trigger not in (0, 1):
            msg = 'wrong trigger {0}'.format(trigger)
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        trigger, action = [1, 'поднять'] if trigger == 0 else [0, 'опустить']

        log.save_action(session.name, 'ports', 'Пытается {0} порт {1} на свитче {2}'.format(action, port, ip))

        sw = Switch(swconf, ip)
        return sw.change_port_status(port, trigger)


class orange: # noqa
    ''' Работа с оранжем '''
    @required_logged
    @required_permission('ipaddr')
    def POST(self): # noqa
        i = web.input(inp='')
        if not i.inp:
            return dumps({
                'status'    : Status.ERROR,
                'db'        : 'orange'
            })
        log.save_action(session.name, 'ipaddr', 'Поиск в ORANGE {0}'.format(i.inp.encode('utf8')))

        bill = H.check_bill(i.inp)
        ip = None
        if not bill:
            ip = H.check_ip(i.inp)
            if not ip:
                return dumps({
                    'status'    : Status.ERROR,
                    'db'        : 'orange'
                })
            res = ora.get_bill_id_for_ip(ip)

            if res['status'] != Status.SUCCESS:
                return dumps({
                    'status'    : Status.ERROR,
                    'db'        : 'orange'
                })
            bill = res['billid']

        if not bill:
            return dumps({
                'status'    : Status.EMPTY,
                'db'        : 'orange'
            })

        if not H.is_region_allowed(bill, session.regions):
            return dumps({
                'status'    : Status.NOAUTH,
                'db'        : 'orange'
            })

        return ora.get_user_params(bill, ip)


class release: # noqa
    ''' отвязывание абонентов '''
    @required_logged
    @required_any_permission_in(['rellow', 'relhigh'])
    def POST(self): # noqa
        i = web.input(billid='', portid='', days='', swip='', swport='')
        if not i.billid or not i.portid or not i.days or not i.swip or not i.swport:
            print('incorrect parameters {0}'.format(i))
            return dumps({
                'status' : Status.ERROR
            })
        billid = H.check_bill(i.billid)
        if not billid:
            return dumps({
                'status' : Status.ERROR
            })
        try:
            portid = int(i.portid)
        except ValueError:
            msg = 'port not int, port: "{0}"'.format(i.portid)
            print(msg)
            return dumps({
                'status' : Status.ERROR
            })
        try:
            days = int(i.days)
            swport = int(i.swport)
        except ValueError:
            msg = 'not valid num of days or port: "{0}" "{1}"'.format(i.days, i.swport)
            print(msg)
            return dumps({
                'status' : Status.ERROR
            })
        swip = H.check_ip(i.swip)
        if not swip:
            print('not switch ip {0}'.format(i.swip))
            return dumps({
                'status' : Status.ERROR
            })

        perm = 'relhigh'
        if days >= 180:
            perm = 'rellow'
        if not session.get(perm, False):
            return dumps({
                'status' : Status.NOAUTH
            })

        log.save_action(
            session.name,
            'release',
            'Попытка отвязать абонента {0} с {1} порт {2} portid {3}'.format(
                billid, swip, swport, portid))

        res = sb.get_subs_id_by_portid(billid, portid)
        if res['status'] != Status.SUCCESS:
            return dumps(res)

        perm = 'relhigh'
        if res['priv'] == 'low':
            perm = 'rellow'
        if not session.get(perm, False):
            return dumps({
                'status'    : Status.NOAUTH
            })

        res = sb.release_port(res['subsid'])

        msg = 'Успешно отвязал абонента {0} c {1} порт {2} portid {3}'.format(
            billid, swip, swport, portid)

        if res['status'] != Status.SUCCESS:
            msg = 'Отвязывание абонента {0} с {1} порт {2} portid {3} прошло с ошибкой!'.format(
                billid, swip, swport, portid)

        log.save_action(session.name, 'release', msg)

        return dumps(res)


class reserve: # noqa
    ''' привязка абонента к порту '''
    @required_logged
    @required_permission('reserve')
    def POST(self): # noqa
        i = web.input(billid='', portid='', swip='', swport='')
        if not i.billid or not i.portid or not i.swip or not i.swport:
            print('not billid or portid or swip or swport')
            return dumps({
                'status' : Status.ERROR
            })

        billid = H.check_bill(i.billid)
        if not billid:
            print('wrong billid {0}'.format(i.billid))
            return dumps({
                'status' : Status.ERROR
            })

        try:
            portid = int(i.portid)
        except ValueError:
            msg = 'portid not int, raw portid: "{0}"'.format(i.portid)
            print(msg)
            return dumps({
                'status' : Status.ERROR
            })

        swip = H.check_ip(i.swip)
        if not swip:
            msg = 'not switch ip "{0}"'.format(i.swip)
            print(msg)
            return dumps({
                'status' : Status.ERROR
            })

        try:
            swport = int(i.swport)
        except ValueError:
            msg = 'swport not int, raw port: "{0}"'.format(i.swport)
            print(msg)
            return dumps({
                'status' : Status.ERROR
            })

        log.save_action(
            session.name,
            'reserve',
            'Попытка привязать абонента {0} на {1} порт {2}'.format(billid, swip, swport))

        res = sb.get_one_subs_id(billid)

        if res['status'] != Status.SUCCESS:
            return dumps(res)

        # есть привязка, освобождаем в оранже
        if res['portid']:
            res_in = sb.release_port(res['subsid'])
            msg = ''
            if res_in['status'] != Status.SUCCESS:
                msg = 'Отвязывание абонента {0} с portid {1} прошло с ошибкой!'.format(
                    billid, res['portid'])

                log.save_action(session.name, 'reserve', msg)
                return dumps(res_in)

            msg = 'Успешно отвязал абонента {0} с portid {1}'.format(billid, res['portid'])
            log.save_action(session.name, 'reserve', msg)
        # теперь привяжем
        res = sb.reserve_port(res['subsid'], portid)
        msg = 'Привязал абонента {0} на {1} порт {2}'.format(billid, swip, swport)
        if res['status'] != Status.SUCCESS:
            msg = 'Привязка абонента {0} на {1} порт {2} прошла с ошибкой!'.format(billid, swip, swport)
        log.save_action(session.name, 'reserve', msg)
        return dumps(res)


class orangesw: # noqa
    ''' поиск абонентов на свитче '''
    @required_logged
    @required_permission('switch')
    def POST(self): # noqa
        i = web.input(inp='')
        if not i.inp:
            return dumps({
                'status' : Status.ERROR
            })

        log.save_action(session.name, 'switch', 'Запрос клиентов на свитче {0}'.format(i.inp.encode('utf8')))
        res = ora.get_clients_on_switch(i.inp)

        if res['status'] != Status.SUCCESS:
            return dumps(res)

        # составим список клиентов на свитче для запроса в сбмс
        orange_data = res['data']
        bill_list = []
        for bill in orange_data.values():
            if bill[1] and H.check_bill(bill[1]):
                bill_list.append(bill[1])

        # если есть хоть 1 абонент
        if bill_list:
            sbms_data = sb.get_users_params(bill_list)
            if not sbms_data:
                return dumps({
                    'status' : Status.ERROR
                })
        result = []
        for port in orange_data.keys():
            row = {}
            # если есть договор, достаем о нем инфу из сбмс
            port_info = orange_data[port]
            ip      = port_info[0]
            billid  = port_info[1]
            portid  = port_info[2]

            row['port'] = port
            row['portid'] = portid

            if not billid:
                result.append(row)
                continue

            row['bill'] = billid
            row['ip'] = ip
            addr = 'Nowhere'
            fio = 'John Doe'

            if billid not in sbms_data.keys():
                addr = ''
                fio = ''
            elif sbms_data[billid] == 'onyma':
                addr = 'Onyma'
                fio = 'Onyma'
            else:
                fio = sbms_data[billid][1]
                addr = sbms_data[billid][2]
                bill_status = sbms_data[billid][0]
                row['bill-status'] = bill_status
                if bill_status == 'danger':
                    row['blocked'] = sbms_data[billid][4]
                row['release'] = sbms_data[billid][3]
            row['addr'] = addr
            row['fio'] = fio
            result.append(row)

        # port bill ip addr blocked fio release portid
        return dumps({
            'status'    : Status.SUCCESS,
            'data'      : result,
            'swip'      : res['swip']
        })


class switchstatus: # noqa
    ''' Возвращает статус свитча '''
    @required_logged
    @required_permission('ipaddr')
    def POST(self): # noqa
        i = web.input(ip='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip "{0}"'.format(i.ip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        sw = Switch(swconf, ip)
        return sw.get_switch_status()

class switchportstatus: # noqa
    ''' Возвращает статус порта '''
    @required_logged
    @required_permission('ipaddr')
    def POST(self): # noqa
        i = web.input(ip='', port='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip "{0}"'.format(i.ip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        try:
            port = int(i.port)
        except ValueError:
            msg = 'port not int, port: "{0}"'.format(i.port)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        sw = Switch(swconf, ip)
        return sw.get_snmp_port_status(port)


class switchallportstatus: # noqa
    ''' Возвращает статус всех портов '''
    @required_logged
    @required_permission('switch')
    def POST(self): # noqa
        i = web.input(ip='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip "{0}"'.format(i.ip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        sw = Switch(swconf, ip)
        return sw.get_snmp_all_ports_status()


class porterrors: # noqa
    ''' Ошибки на свитче '''
    @required_logged
    @required_permission('ipaddr')
    def POST(self): # noqa
        i = web.input(ip='', port='', curr='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip "{0}"'.format(i.ip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        try:
            port = int(i.port)
        except ValueError:
            msg = 'port not int, port: "{0}"'.format(i.port)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        try:
            curr = int(i.curr)
        except ValueError:
            msg = 'no curr err'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        res = swFactory.get_switch_model(ip)
        if res['status'] != Status.SUCCESS:
            if res['status'] == Status.NOTFOUND:
                msg = 'Не смог получить модель свитча!'
                print('{0} {1}'.format(msg, ip))
            return dumps(res)
        sw = res['sw']
        return sw.get_count_port_errors(port, curr)


class cabdiagport: # noqa
    ''' КабДиаг на свитче '''
    @required_logged
    @required_permission('cabdiag')
    def POST(self): # noqa
        log.save_action(session.name, 'cabdiag', 'Попытка сделать кабдиаг')
        i = web.input(ip='', port='')

        try:
            port = int(i.port)
        except ValueError:
            msg = 'port not int, port: "{0}"'.format(i.port)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        log.save_action(session.name, 'cabdiag', 'Успешный кабдиаг свитч {0} порт {1}'.format(ip, port))

        res = swFactory.get_switch_model(ip)
        if res['status'] != Status.SUCCESS:
            if res['status'] == Status.NOTFOUND:
                msg = 'Не смог получить модель свитча!'
                print('{0} {1}'.format(msg, ip))
            return dumps(res)
        sw = res['sw']
        return sw.cable_test(port)


class cabdiagall: # noqa
    ''' КабДиаг всех портов на свитче '''
    @required_logged
    @required_permission('cabdiag')
    def POST(self): # noqa
        log.save_action(session.name, 'cabdiagall', 'Попытка сделать масс кабдиаг')
        i = web.input(ip='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip'
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        log.save_action(session.name, 'cabdiagall', 'Успешный масс кабдиаг свитч {0}'.format(ip))

        res = swFactory.get_switch_model(ip)
        if res['status'] != Status.SUCCESS:
            if res['status'] == Status.NOTFOUND:
                msg = 'Не смог получить модель свитча!'
                print('{0} {1}'.format(msg, ip))
            return dumps(res)
        sw = res['sw']
        return sw.cable_test_all()


class dhcpshort: # noqa
    ''' Просмотр дхцп логов в веб форме клиентов '''
    @required_logged
    @required_permission('dhcp')
    def POST(self): # noqa
        i = web.input(ip='')
        ip = H.check_ip(i.ip)
        if not ip:
            return dumps({
                'status' : Status.ERROR
            })
        log.save_action(session.name, 'dhcp', 'Просмотр дхцп логов {0}'.format(ip))
        return dh.get_dhcp_short_logs(ip)


class logout: # noqa
    ''' Завершение сессии '''
    def GET(self): # noqa
        if not session.get('name', False):
            raise web.seeother('/')
        log.save_action(session.name, 'auth', 'Выход из системы')
        session.kill()
        raise web.seeother('/')


class auth: # noqa
    ''' Авторизация пользователей '''
    def GET(self): # noqa
        if session.get('logged', False):
            raise web.seeother('/main')
        # отсортируем словарь по городу
        sorted_list = []
        for row in sorted(ldap_settings.iteritems(), key=lambda (k, v): v['name']):
            sorted_list.append(row)
        return render.auth(version, sorted_list)

    def POST(self): # noqa
        i = web.input(username='', password='', domain='')
        if not i.username or not i.password or not i.domain:
            msg = 'Одно или несколько полей не заполнено!'
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        username = i.username.strip().lower()
        password = i.password.strip()
        # попробуем авторизоваться в Active Directory
        host = ldap_settings[i.domain]['host']
        status = Ldap(host).authorize(username, password, host)

        # если сервер AD лежит, пробуем локальную авторизацию
        local_auth = False
        if status == Status.SERVER_DOWN:
            print('localauth {0}, st: {1}, host: {2}, domain: {3}'.format(username, status, host, i.domain))
            status = H.authorize(db, username, password)
            local_auth = True

        # если статус неуспешный, вернем ошибку
        if status != Status.SUCCESS:
            print('authorize not success {0}, st: {1}, host: {2}, domain: {3}'.format(username, status, host, i.domain))
            return dumps({
                'status': status
            })

        # если входили через AD, сохраним пароль в базе
        # чтобы можно было пользоваться локальной авторизацией
        if not local_auth:
            H.store_passwd(db, username, password)

        session.logged = True
        session.name = username
        # получим права пользователя из базы
        data = H.get_user_privileges(db, username)
        if data:
            # заполним сессию пользователя правами
            H.fill_session(session, data)
        log.save_action(session.name, 'auth', 'Успешная авторизация')
        return dumps({
            'status': Status.SUCCESS
        })


class admin: # noqa
    ''' Класс для разграничения прав пользователей '''
    @required_logged
    @required_permission('admin')
    def GET(self): # noqa
        i = web.input(user='')
        if not i.user:
            msg = 'Не указан пользователь!'
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        user = H.check_username(i.user)
        if not user:
            msg = 'Неправильный формат имени пользователя!'
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        log.save_action(session.name, 'admin', 'Просмотр прав {0}'.format(user))
        # получим права пользователя из базы
        data = H.get_user_privileges(db, user)

        return dumps({
            'status' : Status.SUCCESS,
            'data'   : data
        })


class admindelete: # noqa
    @required_logged
    @required_permission('admin')
    def POST(self): # noqa
        log.save_action(session.name, 'admin', 'Попытка удаления пользователя')

        i = web.input(user='')

        user = H.check_username(i.user)
        if not user:
            msg = 'Не знаю кого удалять!'
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        where = "user='{0}'".format(user)
        res = db.delete('users', where=where)
        if res != 1:
            msg = 'Не смог удалить пользователя!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        log.save_action(session.name, 'admin', 'Удалил пользователя {0}'.format(user))

        status = H.delete_user_sessions(db, store, user)
        if not status:
            msg = 'Не смог удалить сессии пользователя!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        return dumps({
            'status' : Status.SUCCESS
        })


class admincopy: # noqa
    @required_logged
    @required_permission('admin')
    def POST(self): # noqa
        log.save_action(session.name, 'admin', 'Попытка копирования прав в админке')

        i = web.input(user='', to='')

        user = H.check_username(i.user)
        if not user:
            msg = 'Не с кого копировать права!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        try:
            to = loads(i.to)
        except ValueError:
            msg = 'Не смог преобразовать входные данные!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        if not to:
            msg = 'Пустые входные данные!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        # обновим права в базе данных
        status = H.copy_user_privileges(db, user, to)
        if not status:
            msg = 'Не смог установить новые права пользователю!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        data = H.get_user_privileges(db, user)

        # обновим права самому себе, чтобы не перелогиниваться
        if session.name in to:
            for rule in H.RULES:
                session[rule] = data[rule]

            regions = data['regions'].split(',')
            session['regions'] = map(int, regions)

        # обновим сессии пользователей в базе
        status = H.copy_user_sessions(db, store, to, data)
        if not status:
            print('Не смог обновить сессии пользователям')

        log.save_action(session.name, 'admin', 'Скопировал права {0} пользователям {1}'.format(user, ', '.join(to)))

        return dumps({
            'status' : Status.SUCCESS
        })


class adminedit: # noqa
    @required_logged
    @required_permission('admin')
    def POST(self): # noqa
        log.save_action(session.name, 'admin', 'Попытка изменений прав в админке')

        i = web.input(user='', data={})

        user = H.check_username(i.user)
        if not user:
            msg = 'Не знаю кому изменять права!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        try:
            data = loads(i.data)
        except ValueError:
            msg = 'Не смог преобразовать входные данные!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        if not data:
            msg = 'Пустые входные данные!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        # обновим права в базе данных
        status = H.update_user_privileges(db, user, data)
        if not status:
            msg = 'Не смог установить новые права пользователю!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        # обновим права самому себе, чтобы не перелогиниваться
        if session.name == user:
            for rule in H.RULES:
                session[rule] = data[rule]

            regions = data['regions'].split(',')
            session['regions'] = map(int, regions)

        # обновим сессию пользователя в базе
        status = H.update_user_sessions(db, store, user, data)
        if not status:
            msg = 'Не смог обновить сессии пользователя!'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        log.save_action(session.name, 'admin', 'Изменил права пользователю {0}'.format(user))
        return dumps({
            'status' : Status.SUCCESS
        })


class dhcpfull: # noqa
    ''' Расширенный посмотр DHCP логов '''
    @required_logged
    @required_permission('dhcp')
    def POST(self): # noqa
        i = web.input(data={})
        try:
            data = loads(i.data)
        except ValueError:
            print('cant loads data')
            return dumps({
                'status' : Status.ERROR
            })

        if not data:
            return dumps({
                'status' : Status.ERROR
            })

        log.save_action(session.name, 'dhcp', 'Поиск по дхцп логам')
        return dh.get_dhcp_full_logs(data)


class users: # noqa
    ''' список пользователей системы oss '''
    @required_logged
    @required_permission('admin')
    def GET(self): # noqa
        result = db.select('users', what='user')
        result = [v['user'] for v in list(result)]
        # отсортируем список по фамилии
        return dumps(sorted(result, key=lambda k: k[k.find('.') + 1:]))


class logs: # noqa
    ''' Отображение логов пользователя '''
    @required_logged
    @required_permission('logs')
    def GET(self): # noqa
        ''' список пользователей, которые пользовались когда-либо системой '''
        table = log.get_unique_users()
        # отсортируем список по фамилии
        return dumps(sorted(table, key=lambda k: k[k.find('.') + 1:]))

    @required_logged
    @required_permission('logs')
    def POST(self): # noqa
        i = web.input(data={})
        try:
            data = loads(i.data)
        except ValueError:
            print('cant loads data')
            return
        return log.get_user_logs(data)


class main: # noqa
    ''' глагне '''
    @required_logged
    def GET(self): # noqa
        changelog = {}
        with open('changelog.json', 'r') as f:
            changelog = load(f)

        return render.main(version, session, changelog)


class macs: # noqa
    ''' Список мак адресов на порту '''
    @required_logged
    @required_permission('macs')
    def POST(self): # noqa
        i = web.input(ip='', port='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip "{0}"'.format(i.ip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        try:
            port = int(i.port)
        except ValueError:
            msg = 'port not int, port: "{0}"'.format(i.port)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        res = swFactory.get_switch_model(ip)
        log.save_action(session.name, 'macs', 'Просмотр маков на {0} : {1}'.format(ip, port))
        if res['status'] != Status.SUCCESS:
            if res['status'] == Status.NOTFOUND:
                msg = 'Не смог получить модель свитча!'
                print('{0} {1}'.format(msg, ip))
            return dumps(res)
        sw = res['sw']
        return sw.get_macs(port)


class topology: # noqa
    ''' Топология свитчей '''
    @required_logged
    @required_permission('topology')
    def POST(self): # noqa
        ''' Возвращает список элементов для библиотеки cytoscape и layout '''
        i = web.input(inp='')
        data = H.check_ip(i.inp)
        if not data:
            data = H.check_sysname(i.inp)
            if not data:
                msg = 'not ip or sysname "{0}"'.format(i.inp)
                print(msg)
                return dumps({
                    'status' : Status.ERROR,
                    'msg'    : msg
                })
        log.save_action(session.name, 'topology', 'Просмотр топологии {0}'.format(data))
        return Topology().get_topology(data)


class topologyadm: # noqa
    ''' Просмотр и редактирование конфигурации свитча в топологии '''
    @required_logged
    @required_permission('topadm')
    def GET(self): # noqa
        ''' Возвращает объект (свитч) из базы '''
        i = web.input(inp='')
        data = H.check_ip(i.inp)
        if not data:
            data = H.check_sysname(i.inp)
            if not data:
                msg = 'not ip or sysname "{0}"'.format(i.inp)
                print(msg)
                return dumps({
                    'status' : Status.ERROR,
                    'msg'    : msg
                })
        log.save_action(session.name, 'topadm', 'Просмотр объекта топологии {0}'.format(data))
        return Topology().get_info(data)


class topologyports: # noqa
    ''' Работа с портами '''
    @required_logged
    @required_permission('topadm')
    def POST(self): # noqa
        ''' Возвращает список свободных портов на свитче '''
        i = web.input(ip='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip "{0}"'.format(i.ip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        # получим список портов со свитча
        sw = Switch(swconf, ip)
        sw_ports = sw.get_local_lldp_ports()
        if not sw_ports:
            msg = 'switch {0} dont have lldp ports'
            print(msg)
            return dumps({
                'status': Status.EMPTY
            })
        ports = set(sw_ports)
        # получим список портов которые уже есть в базе
        db_ports = Topology().get_ports(ip)
        if db_ports:
            ports = ports - db_ports
        return dumps({
            'status': Status.SUCCESS,
            'data'  : sorted(ports)
        })


class topologyadmdel: # noqa
    ''' Удаление свитча из базы '''
    @required_logged
    @required_permission('topadm')
    def POST(self): # noqa
        ''' Удаление свитча из базы '''
        i = web.input(ip='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip "{0}"'.format(i.ip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        log.save_action(session.name, 'topadm', 'Удаление свитча {0} из топологии'.format(ip))
        return Topology().delete_switch(ip)


class topologydel: # noqa
    @required_logged
    @required_permission('topadm')
    def POST(self): # noqa
        i = web.input(ip='', port='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip "{0}"'.format(i.ip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        if not i.port:
            msg = 'no port to del'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        if i.port.find('.') != -1:
            msg = 'you cant use dots in portname'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        port = i.port
        log.save_action(session.name, 'topadm', 'Удаление порта {0} на свитче {1}'.format(port, ip))
        return Topology().delete_link(ip, port)

class topologyadd: # noqa
    @required_logged
    @required_permission('topadm')
    def POST(self): # noqa
        i = web.input(srcip='', srcport='', dstip='', dstport='')
        src_ip = H.check_ip(i.srcip)
        if not src_ip:
            msg = 'not src ip "{0}"'.format(i.srcip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        dst_ip = H.check_ip(i.dstip)
        if not dst_ip:
            msg = 'not dst ip "{0}"'.format(i.dstip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        if src_ip == dst_ip:
            msg = 'srcip cant be dstip'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        if not i.dstport or not i.srcport:
            msg = 'no dst or src port'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        if i.dstport.find('.') != -1 or i.srcport.find('.') != -1:
            msg = 'you cant use dots in portname'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })

        log.save_action(session.name, 'topadm', 'Добавление линка между {0} - {1} <=> {2} - {3}'.format(
            src_ip, i.srcport, dst_ip, i.dstport))
        return Topology().add_link(src_ip, i.srcport, dst_ip, i.dstport)

class traffic: # noqa
    ''' Список абонентских траффик сессий '''
    @required_logged
    @required_permission('traffic')
    def POST(self): # noqa
        i = web.input(bill='', ip='')
        ip = H.check_ip(i.ip)
        if not ip:
            msg = 'not ip "{0}"'.format(i.ip)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        bill = H.check_bill(i.bill)
        if not bill:
            msg = 'not bill "{0}"'.format(i.bill)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        log.save_action(session.name, 'traffic', 'Просмотр трафика абонента {0}, ip: {1}'.format(bill, ip))
        return sb.get_user_traffic(bill, ip)


class faq: # noqa
    ''' документация '''
    @required_logged
    def GET(self): # noqa
        return render.faq(version)


def notfound():
    ''' error 404 '''
    return web.notfound(render.page404(version))

app.notfound = notfound
application = app.wsgifunc()
