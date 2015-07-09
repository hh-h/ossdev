# coding: utf-8

""" Базовый класс для работы с базой данных Оракла """

from cx_Oracle import connect, InterfaceError, OperationalError, DatabaseError
from os import environ


environ['NLS_LANG'] = 'RUSSIAN_RUSSIA.UTF8'


class Oracle(object):
    """ Класс для работы с базой данных Оранжа """
    def __init__(self, di):
        self.host   = di['host']
        self.user   = di['user']
        self.passwd = di['password']
        self.db     = di['db']
        self.con    = None

    def __connect(self):
        """ подключение к базе данных """
        conn = "{0}/{1}@{2}/{3}".format(self.user, self.passwd, self.host, self.db)
        try:
            self.con = connect(conn)
            self.con.autocommit = True
        except DatabaseError:
            return False
        return True

    def cursor(self):
        ''' Возвращает курсор для запросов '''
        cur = None
        try:
            cur = self.con.cursor()
        except AttributeError:
            status = self.__connect()
            if not status:
                return None
            cur = self.con.cursor()
        return cur

    def __execute(self, cur, query):
        ''' Выполнение запроса к базе
        при потере подключения, пересодиняется к базе '''
        try:
            cur.execute(query)
        except (AttributeError, InterfaceError, OperationalError):
            try:
                self.con.close()
            except:
                pass
            status = self.__connect()
            if not status:
                return False
            cur.execute(query)
        except DatabaseError:
            print(query)
        return True

    def fetchone(self, query):
        cur = self.cursor()
        if not cur:
            return -1, None
        status = self.__execute(cur, query)
        if not status:
            return -1, None
        result = cur.fetchone()
        cur.close()
        return 0, result

    def fetchall(self, query):
        cur = self.cursor()
        if not cur:
            return -1, None
        status = self.__execute(cur, query)
        if not status:
            return -1, None
        result = cur.fetchall()
        cur.close()
        return 0, result
