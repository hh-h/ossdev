# coding: utf-8

""" Класс для работы с базой данных СБМС """

from Oracle import Oracle
from cx_Oracle import NUMBER, STRING, DatabaseError
from json import dumps
from Status import Status
from time import time, localtime, timezone


class Sbms(Oracle):
    """ Класс для работы с базой данных СБМС """
    def get_user_params(self, bill, ip=None):
        """ возвращает из сбмс данные клиента по договору """
        query = '''
            SELECT
                -- 0
                -- 1
                -- 2 номер договора
                -- 3 ФИО клиента
                -- 4 баланс клиента
                -- 5 длинный номер договора
                -- 6 статус договора по-русски
                -- 7 статус услуги серый айпи
                -- 8 статус услуги добровольная блокировка
                -- 9 номер тарифа
                -- 10 название тарифа
                -- 11 скорость тарифа
                -- 12 белый айпи
                -- 13 серый айпи
                -- 14 город
                -- 15 улица
                -- 16 дом
                -- 17 корпус
                -- 18 квартира
                -- 19 последний раз смена статуса, unixtime
                -- 20 телефон абонента
                -- 21 статус услуги белый айпи
            '''.format(bill)

        status, rows = self.fetchall(query)
        if status != 0:
            msg = 'Ошибка выполнения запроса к базе данных!'
            return dumps({
                'status': Status.ERROR,
                'db'    : 'sbms',
                'msg'   : msg
            })
        unixtime = int(time())

        if not rows:
            return dumps({
                'status'    : Status.EMPTY,
                'db'        : 'sbms'
            })

        abons = {}
        found = None
        for row in rows:
            clntid = row[2]
            abonid = row[5]
            if abonid.startswith(clntid):
                abonid = int(abonid[-4:])
                abons[abonid] = row[13] if row[13] else False
            else:
                print('Error: абонент {0} не должен быть частью {1}'.format(abonid, clntid))

            # поиск был по договору
            if not ip:
                found = row[:]
                continue
            # поиск был по ip, нашли нужный
            if row[13] == ip:
                found = row[:]

        if not found:
            msg = 'Error: empty row in get_user_params {0}, {1}'.format(bill, ip)
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'db'    : 'sbms',
                'msg'   : msg
            })

        color = self.get_client_status_color(found[7], found[8])
        descr = self.status_code_to_descr(found[7], found[8])
        bill = "<span id='billid' class='text-{0}' title='{2}'>{1}</span>".format(color, found[2], descr)
        if color == 'danger':
            bill += " <span class='text-{0}'>({1})</span>".format(color, ((unixtime - int(found[19])) / 86400) + 1)
        # класс, который добавляется если у абонента криво привязана услуга белый айпи
        warning_class = ''
        if not found[12]:
            color = 'primary'
            ext_ip = 'NAT'
        else:
            if not found[21]:
                color = 'danger'
                warning_class = ' fa fa-warning'
            else:
                color = self.get_client_status_color(found[21])
            ext_ip = found[12]

        html_ip = "<span id='int-ip-addr'>{0}</span> / ".format(found[13])
        html_ip += "<span id='ext-ip-addr' class='text-{1}{2}'>{0}</span>".format(ext_ip, color, warning_class)
        bal = '{0} руб.'.format(found[4])

        addr = self.format_address(found[15], found[16], found[17], found[18])
        phone = 'Не указан'
        if found[20]:
            phone = found[20]
            phone = '+7 ({0}) {1}-{2}-{3}'.format(phone[:3], phone[3:6], phone[6:8], phone[8:10])

        data = {
            'sbms_bill'     : bill,
            'sbms_fio'      : found[3],
            'sbms_ip'       : html_ip,
            'sbms_bal'      : bal,
            'sbms_shaper'   : found[11],
            'sbms_addr'     : addr,
            'sbms_phone'    : phone
        }
        if len(abons) > 1:
            data['sbms-abons'] = abons

        return dumps({
            'status'    : Status.SUCCESS,
            'data'      : data
        })

    def get_users_params(self, bill_list):
        """ Возвращает из сбмс данные клиентов по списку договоров """

        bill = bill_list[0] if len(bill_list) == 1 else str(tuple(bill_list))

        query = '''
            SELECT
                -- 0 номер договора
                -- 1 ФИО клиента
                -- 2 статус услуги серый айпи
                -- 3 статус услуги добровольная блокировка
                -- 4 город
                -- 5 улица
                -- 6 дом
                -- 7 корпус
                -- 8 квартира
                -- 9 последний раз смена статуса, unixtime
            '''.format(bill)

        unixtime = int(time())
        result = {}
        status, rows = self.fetchall(query)
        if status != 0:
            msg = 'Ошибка выполнения запроса к базе данных!'
            return {
                'status': Status.ERROR,
                'db'    : 'sbms',
                'msg'   : msg
            }
        try:
            for row in rows:
                days = ((unixtime - int(row[9])) / 86400) + 1
                # фикс для шаблона
                if days == 0:
                    days = 1
                release = 'success' if days > 180 else 'danger'
                addr = self.format_address(row[5], row[6], row[7], row[8])
                color = self.get_client_status_color(row[2], row[3])
                # если абонент активный, обнулим ему счетчик дней
                if color != 'danger':
                    release = 'danger'
                result[row[0]] = [color, row[1].decode('utf8')[:35], addr, release, days]
        except DatabaseError:
            print(bill)
            return result
        # те абоненты, которых нет в сбмс помечаем флагом онимы
        for b in set(bill_list) - set(result.keys()):
            result[b] = 'onyma'
        return result

    def release_port(self, subsid):
        ''' Освобождает порт в оранже и стирает тех параметры в сбмс '''

        cur = self.cursor()
        result_code = cur.var(NUMBER)
        result_text = cur.var(STRING)

        cur.callproc('', (result_code, result_text, 0, subsid))
        cur.close()

        if int(result_code.getvalue()) != 0:
            msg = result_text.getvalue()
            print(msg)
            return {
                'status': Status.ERROR,
                'db'    : 'sbms',
                'msg'   : msg
            }
        return {
            'status' : Status.SUCCESS
        }

    def reserve_port(self, subsid, portid):
        ''' Резервирует порт в оранже для договора '''
        cur = self.cursor()
        clntid = cur.callfunc('', NUMBER, (subsid,))
        try:
            clntid = int(clntid)
        except ValueError:
            msg = 'Не смог получить clntid'
            print(msg)
            return {
                'status': Status.ERROR,
                'db'    : 'sbms',
                'msg'   : msg
            }

        result_code = cur.var(NUMBER)
        result_text = cur.var(STRING)
        cur.callproc('', (result_code, result_text, 0, clntid, '', '', subsid, portid))
        cur.close()

        if int(result_code.getvalue()) != 0:
            msg = result_text.getvalue()
            print(msg)
            return {
                'status': Status.ERROR,
                'db'    : 'sbms',
                'msg'   : msg
            }
        return {
            'status' : Status.SUCCESS
        }

    def get_subs_id_by_portid(self, billid, portid):
        ''' Возвращает SUBS_ID пользователя billid прикрепленному к portid '''
        status, rows = self.__get_all_subs_ids(billid)
        if status != 0:
            msg = 'Ошибка при поиске в базе данных!'
            print(msg)
            return {
                'status' : Status.ERROR,
                'db'    : 'sbms',
                'msg'    : msg
            }
        unixtime = int(time())
        subsid = 0
        for row in rows:
            port = 0
            try:
                port = int(row[3])
            except (TypeError, ValueError):
                continue

            if port != portid:
                continue

            subsid = int(row[1])
            time_status = int(row[4])
            status = int(row[5])
            user_block = int(row[6]) if row[6] else 0

        if not subsid:
            msg = 'Не нашел SUBS_ID'
            print(msg)
            return {
                'status' : Status.ERROR,
                'db'    : 'sbms',
                'msg'    : msg
            }
        priv = 'high'
        # количество дней, после которого отвязывать может любой пользователь
        treshold = 180
        if status != 4 and (not user_block or user_block == 6):
            blocked = ((unixtime - time_status) / 86400) + 1
            if blocked >= treshold:
                priv = 'low'

        return {
            'status'  : Status.SUCCESS,
            'priv'    : priv,
            'subsid'  : subsid
        }

    def get_one_subs_id(self, billid):
        ''' Возвращает SUBS_ID привязанный к billid и PORT_ID если привязан'''
        status, rows = self.__get_all_subs_ids(billid)
        if status != 0:
            msg = 'Ошибка при поиске в базе данных!'
            print(msg)
            return {
                'status' : Status.ERROR,
                'msg'    : msg
            }
        if len(rows) == 0:
            msg = 'У клиента {0} нет абонентов!'.format(billid)
            print(msg)
            return {
                'status' : Status.ERROR,
                'msg'    : msg
            }
        if len(rows) > 1:
            msg = 'У клиента {0} {1} абонента(ов)!'.format(billid, len(rows))
            print(msg)
            return {
                'status' : Status.ERROR,
                'msg'    : msg
            }
        portid = rows[0][3]
        subsid = rows[0][1]
        if not subsid:
            msg = 'Не нашел SUBS_ID'
            print(msg)
            return {
                'status' : Status.ERROR,
                'msg'    : msg
            }
        return {
            'status' : Status.SUCCESS,
            'subsid' : subsid,
            'portid' : portid
        }

    def __get_all_subs_ids(self, billid):
        ''' Возвращает все SUBS_ID пользователя прикрепленные к billid '''
        query = '''
            SELECT
            '''.format(billid)

        return self.fetchall(query)

    def get_user_traffic(self, bill, ip):
        '''Возвращает трафик абонента за сегодняшний день '''

        # получим список всех абонентов на договоре
        status, rows = self.__get_all_subs_ids(bill)
        if status != 0:
            msg = 'Ошибка при поиске в базе данных - трафик!'
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        # абонентов не нашел на договоре
        if len(rows) == 0:
            msg = 'У клиента {0} нет абонентов - трафик!'.format(bill)
            print(msg)
            return dumps({
                'status' : Status.ERROR,
                'msg'    : msg
            })
        # у нас несколько абонентов на договоре, отфильтруем по ip
        subsid = 0
        if len(rows) == 1:
            subsid = rows[0][1]
        elif len(rows) > 1:
            subs_list = []
            for row in rows:
                subs_list.append(str(row[1]))
            subs_list = str(tuple(subs_list))
            query = '''
                SELECT
            '''.format(subs_list)

            status, rows = self.fetchall(query)
            if status != 0:
                msg = 'Ошибка выполнения запроса к базе данных!'
                return dumps({
                    'status': Status.ERROR,
                    'msg'   : msg
                })

            for row in rows:
                if row[0] == ip:
                    subsid = row[1]

        if not subsid:
            msg = 'Не нашел subsid с таким ip'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        # current unixtime
        # unixtime = 1430486997 #  первое мая для тестов
        unixtime = int(time())
        # за сколько трафик выводить, в сек
        delta = 86400
        end = localtime(unixtime)
        start = localtime(unixtime - delta)

        # если все в пределах одной таблицы (месяцы равны)
        if start.tm_mon == end.tm_mon:
            table = '_00_{0:02}{1}'.format(start.tm_mon, start.tm_year)
            start_date = '{0:02}.{1:02}.{2}'.format(start.tm_mday, start.tm_mon, start.tm_year)
            end_date = '{0:02}.{1:02}.{2}'.format(end.tm_mday, end.tm_mon, end.tm_year)
            query = '''
                SELECT
            '''.format(subsid, table, start_date, end_date)
        elif start.tm_mon != end.tm_mon:
            # если сейчас первое число, то выборка из двух таблиц юнионом
            table = '_00_{0:02}{1}'.format(start.tm_mon, start.tm_year)
            start_date = '{0:02}.{1:02}.{2}'.format(start.tm_mday, start.tm_mon, start.tm_year)
            query = '''
                SELECT
            '''.format(subsid, table, start_date)

            table = '_00_{0:02}{1}'.format(end.tm_mon, end.tm_year)
            end_date = '{0:02}.{1:02}.{2}'.format(end.tm_mday, end.tm_mon, end.tm_year)
            query += '''
                UNION
                SELECT
            '''.format(subsid, table, end_date)

        status, rows = self.fetchall(query)
        if status != 0:
            msg = 'Ошибка выполнения запроса к базе данных!'
            return dumps({
                'status': Status.ERROR,
                'db'    : 'sbms',
                'msg'   : msg
            })
        if not rows:
            return dumps({
                'status'    : Status.EMPTY,
                'db'        : 'sbms'
            })
        data = []
        end_point = (unixtime - timezone) * 1000
        start_point = (unixtime - timezone - delta) * 1000
        for i, row in enumerate(rows):
            date = row[0]
            if date <= start_point:
                continue
            traf = row[1] + 0.01
            data.append([date, traf])

        if not data:
            return dumps({
                'status'    : Status.EMPTY,
                'db'        : 'sbms'
            })
        # добавим еще временные отрезки для визуализации
        timeline = [[start_point, 0.01], [end_point, 0.01]]
        return dumps({
            'status'    : Status.SUCCESS,
            'data'      : data,
            'timeline'  : timeline
        })

    @staticmethod
    def get_client_status_color(status, block=None):
        ''' Возвращает цвет договора
        status если не 4 - заблокирован
        block not None - юзер сам заблокировал себя '''
        block = int(block) if block else 0
        status = int(status)
        color = 'normal'
        if status == 4:
            color = 'success'
        elif block and block != 6:
            color = 'warning'
        else:
            color = 'danger'
        return color

    @staticmethod
    def format_address(street, house, housing, flat):
        housing = '/{0}'.format(housing) if housing and housing != '0' else ''
        # иногда возвращается вместо улицы "Турку ул _ Санкт-Петербург г"
        str_idx = street.find(' _ ')
        if str_idx != -1:
            street = street[:str_idx]
        return '{0} д. {1}{2} кв. {3}'.format(
            street,
            house,
            housing,
            flat
        )

    @staticmethod
    def status_code_to_descr(code, block):
        # select * from bis.serv_statuses;
        block = int(block) if block else 0
        code = int(code)
        if code == 4:
            return 'Подключена'
        elif code == 2:
            if block and block == 4:
                return 'Добровольная блокировка'
            return 'Ожидание оплаты'
        elif code == 6:
            return 'Отключена'
        elif code == 1:
            return 'Не заказана'
        elif code == 3:
            return 'Ожидание подключения'
        elif code == 5:
            return 'Ожидание отключения'
        else:
            return '???'
