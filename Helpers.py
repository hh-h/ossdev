# coding: utf-8
''' Функции помошники '''

from netaddr import IPAddress, AddrFormatError, INET_PTON
from passlib.hash import sha256_crypt
from json import loads, dumps
from base64 import encodestring, decodestring
from re import match, search, IGNORECASE

RULES = (
    'admin',
    'logs',
    'ipaddr',
    'session',
    'dhcp',
    'cabdiag',
    'ports',
    'switch',
    'rellow',
    'relhigh',
    'reserve',
    'netadm',
    'macs',
    'topology',
    'topadm',
    'traffic'
)

MASKS = {
    '16' : '255.255.0.0',
    '17' : '255.255.128.0',
    '18' : '255.255.192.0',
    '19' : '255.255.224.0',
    '20' : '255.255.240.0',
    '21' : '255.255.248.0',
    '22' : '255.255.252.0',
    '23' : '255.255.254.0',
    '24' : '255.255.255.0',
    '25' : '255.255.255.128',
    '26' : '255.255.255.192',
    '27' : '255.255.255.224',
    '28' : '255.255.255.240',
    '29' : '255.255.255.248',
    '30' : '255.255.255.252',
    '31' : '255.255.255.254'
}

REGIONS = {
    '403': 5,
    '402': 23,
    '102': 36,
    '103': 48,
    '301': 52,
    '104': 57,
    '401': 61,
    '105': 69,
    '106': 71,
    '201': 78
}

IP_REGIONS = {
    5: [5, 105],
    23: [23],
    36: [36, 136],
    48: [48, 148],
    52: [52, 152],
    57: [57],
    61: [61, 161],
    69: [69, 169],
    71: [71],
    78: [0, 1, 2, 3, 4, 78, 98, 100, 128, 129, 147, 178, 198]
}

BRAS_FUNCTIONS = {
    'fetch'     : 'find_session',
    'delete'    : 'delete_session'
}


def check_ip(ip):
    ''' Принимает строку, возвращает строку с IP если эта строка валидный IP или False '''
    try:
        ip = IPAddress(ip, version=4, flags=INET_PTON)
        return str(ip)
    except AddrFormatError:
        return False
    except ValueError:
        return False
    except:
        return False


def check_bill(bill):
    ''' Принимает строку, проверяет может ли это быть номером договора и возвращает его или False '''
    # 11 - длина договора
    bill = bill.strip()[:11]
    if match(r'\d{11}', bill):
        return bill
    return False


def check_abon(abon):
    ''' Принимает строку, проверяет может ли это быть abonid и возвращает его либо false '''
    # 15 - длина абонента
    abon = abon.strip()[:15]
    if match(r'\d{15}', abon):
        return abon
    return False


def check_sysname(sysname):
    ''' Принимает строку, проверяет может ли это быть валидным сиснеймом свитча и возвращает его или False '''
    sysname = sysname.strip()
    m = match(r'^[a-z0-9][a-z0-9_\-.()]+$', sysname, IGNORECASE)
    if not m:
        return False
    return sysname


def check_username(name):
    ''' Принимает сроку, проверяет валидный ли юзернейм, если все ок - возвращает его, или False '''
    name = name.strip()
    m = match(r'^[a-z]+\.[a-z]+$', name, IGNORECASE)
    if not m:
        return False
    return name


def check_bras_action(action):
    ''' Проверяем правильность действия для браса '''
    action = action.strip().lower()
    if action not in ('fetch', 'delete'):
        return False
    return action


def authorize(db, user, passwd):
    ''' Поиск пользователя user в базе db с паролем passwd '''
    where = "user = '{0}'".format(user)
    result = db.select('users', where=where)
    if not result:
        # do smth useful
        return False
    # passwd, data, user
    result = list(result)[0]
    # print '*' * 50, list(result)[0].passwd
    # for result in results:
    # print result
    return sha256_crypt.verify(passwd, result.passwd)


def store_passwd(db, user, passwd):
    ''' Сохраняем пароль пользователя для локальной авторизации если AD лежит '''
    passwd = sha256_crypt.encrypt(passwd, rounds=40000)
    db.query('''
        INSERT OR REPLACE INTO users (user, passwd, data)
        VALUES (
            $user,
            $pwd,
            COALESCE((SELECT data FROM users WHERE user=$user), '')
        )''', vars={'user' : user, 'pwd' : passwd})


def get_user_privileges(db, user):
    ''' Вытаскивает из базы права пользователя и возвращает словарь прав '''
    where = "user = '{0}'".format(user)
    result = db.select('users', where=where, what='data')
    result = list(result)[0].data
    if not result:
        return False
    return decode(result)


def fill_session(session, data):
    ''' Заполняем сессию правами пользователя '''
    for rule in RULES:
        session[rule] = data[rule] if rule in data else 0

    regions = data['regions'].split(',')
    session['regions'] = map(int, regions)


def update_user_privileges(db, user, data):
    ''' Установим новые права пользователю '''
    where = "user = '{0}'".format(user)
    db.update('users', where=where, data=encode(data))
    return True


def copy_user_privileges(db, user, to):
    ''' копируем права user пользователям из списка to '''
    data = get_user_privileges(db, user)

    tr = db.transaction()
    try:
        for u in to:
            where = "user = '{0}'".format(u)
            db.update('users', where=where, data=encode(data))
    except:
        tr.rollback()
        return False
    else:
        tr.commit()
    return True


def delete_user_sessions(db, store, user):
    ''' удаляет все сессии пользователя из базы '''
    result = db.select('sessions', what='session_id,data')
    tr = db.transaction()
    try:
        for res in result:
            # res.data
            user_data = store.decode(res.data)
            if 'name' in user_data \
                    and user_data['name'] == user \
                    and 'session_id' in user_data:
                where = "session_id='{0}'".format(res.session_id)
                db.delete('sessions', where=where)
    except:
        tr.rollback()
        return False
    else:
        tr.commit()
    return True


def copy_user_sessions(db, store, to, data):
    ''' копирует сессию пользователя user пользователям из списка to '''
    result = db.select('sessions', what='data')
    tr = db.transaction()
    try:
        for res in result:
            # res.data
            user_data = store.decode(res.data)
            if 'name' in user_data \
                    and user_data['name'] in to \
                    and 'session_id' in user_data:

                for rule in RULES:
                    user_data[rule] = data[rule]

                regions = data['regions'].split(',')
                user_data['regions'] = map(int, regions)

                db.query('''
                    UPDATE sessions
                    SET data=$data
                    WHERE session_id=$id
                    ''', vars={'id' : user_data['session_id'], 'data' : store.encode(user_data)})
    except:
        tr.rollback()
        return False
    else:
        tr.commit()
    return True


def update_user_sessions(db, store, user, data):
    ''' обновляем права пользователю в сессиях '''
    result = db.select('sessions', what='data')
    tr = db.transaction()
    try:
        for res in result:
            # res.data
            user_data = store.decode(res.data)
            if 'name' in user_data \
                    and user_data['name'] == user \
                    and 'session_id' in user_data:

                for rule in RULES:
                    user_data[rule] = data[rule]

                regions = data['regions'].split(',')
                user_data['regions'] = map(int, regions)

                db.query('''
                    UPDATE sessions
                    SET data=$data
                    WHERE session_id=$id
                    ''', vars={'id' : user_data['session_id'], 'data' : store.encode(user_data)})
    except:
        tr.rollback()
        return False
    else:
        tr.commit()
    return True


def is_region_allowed(bill, user_regions):
    ''' Проверка можно ли пользователю просматривать данный регион '''
    # права на просмотр всех регионов или новый аккаунт
    if any(x in user_regions for x in (0, -1)):
        return True

    if bill[:3] not in REGIONS:
        return False
    region = REGIONS[bill[:3]]

    # у нас есть права на просмотр этого региона
    if region in user_regions:
        return True

    # нет прав
    return False


def get_region_by_ip(ip):
    ''' Возвращает номер региона по айпи адресу '''
    ip = IPAddress(ip)
    octet = ip.words[1]
    for reg, values in IP_REGIONS.iteritems():
        if octet in values:
            return reg
    return False


def get_region_by_bill(bill):
    ''' Возвращает номер региона по номеру договора '''
    if bill[:3] not in REGIONS:
        return False
    return str(REGIONS[bill[:3]])


def huawei_port(port):
    """ Достает из "Ethernet0/0/X" тот самый Х и возращает его
        если строка не является Ethernet0/0/Х возвращает None """
    ret = None
    if 'Ethernet0' in port:
        port = port.replace(r'Ethernet0/0/', '')
        try:
            ret = int(port)
        except ValueError:
            print('fail in 1')
            print(port)
    return ret


def dlink_port1(port):
    """ Достает из "Y/X" тот самый Х и возращает его
        если строка не является Y/Х возвращает None """
    ret = None
    ret_match = search(r'\d[/:](\d+)', port)
    if ret_match:
        try:
            ret = int(ret_match.group(1))
        except ValueError:
            print('fail in 2')
            print(port)
    return ret


def dlink_port2(port):
    """ Достает из "RMON Port  X on Unit Y" тот самый Х и возращает его
        если строка не является RMON Port X on Unit Y возвращает None """
    ret = None
    if 'RMON' in port:
        port = port.replace(r' on Unit 1', '')
        port = port.replace(r'RMON Port', '')
        try:
            ret = int(port)
        except ValueError:
            print('fail in 3')
            print(port)
    return ret


def extract_port(port):
    for func in huawei_port, dlink_port1, dlink_port2:
        sw_port = func(port)
        if sw_port is not None:
            return sw_port
    return 0


def encode(di):
    ''' кодирует словарь для хранения в базе '''
    j = dumps(di)
    return encodestring(j)


def decode(string):
    ''' декодирует строку из базы в словарь '''
    j = decodestring(string)
    return loads(j)
