# coding: utf-8
""" Базовый класс для Брасов """
from traceback import print_exc, print_stack
from telnetlib import Telnet

TIMEOUT = 10


class Bras(object):
    """ Базовый класс для Брасов """

    def __init__(self, di):
        self.host   = str(di['host'])
        self.user   = str(di['user'])
        self.pwd    = str(di['password'])
        self.tn     = None
        self.clname = str(di['name'])
        self.greet  = str(di['greetings'])

    def __login(self):
        """ Метод для авторизации на Брасе
            результат сохраняет в базовом классе """
        self.tn = Telnet(self.host, 23, 5)
        self.tn.get_socket().settimeout(TIMEOUT)
        res = self.tn.expect(['Username:', 'login:'], 5)
        # telnet ok, but no greetings from server
        if res[0] == -1:
            self.tn.close()
            return False
        self.tn.write(self.user + '\n')
        res = self.tn.expect(['Password:'], 5)
        if res[0] == -1:
            self.tn.close()
            return False
        self.tn.write(self.pwd + '\n')
        # > ma5200 and e120, # asr, $ lisg
        res = self.tn.expect([r'>', r'#', r'\$'], 5)
        if res[0] == -1:
            self.tn.close()
            return False
        # we're in for sure
        self.prepare_cli()
        return True

    def write(self, string):
        """ Метод для ввода команды в телнет терминал """
        try:
            self.tn.read_very_eager()
            self.tn.write(string + '\n')
        except (EOFError, AttributeError, IOError):
            res = self.__login()
            if not res:
                return False
            self.tn.write(string + '\n')
        except:
            print_exc()
            print_stack()
            print('Exc in write bras')
            res = self.__login()
            if not res:
                return False
            self.tn.write(string + '\n')
        return True
