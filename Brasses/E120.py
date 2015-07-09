# coding: utf-8
""" Класс для работы с сессиями E120 """

from Bras import Bras
from Status import Status
from socket import timeout
from json import dumps
from traceback import print_exc, print_stack


class E120(Bras):
    """ Класс для работы с сессиями E120 """

    def prepare_cli(self):
        """ Подготовка к выполнению команд в терминале """
        self.write('enable')
        self.tn.read_until('Password:')
        self.write(self.pwd)
        self.tn.read_until('{0}#'.format(self.greet))
        self.write('virtual-router BRAS01')
        self.tn.read_until('{0}:BRAS01#'.format(self.greet))
        self.write('terminal length 0')
        self.tn.read_until('{0}:BRAS01#'.format(self.greet))

    def find_session(self, ip):
        """ Метод для поиска сессии на Брасе """
        res = ''
        try:
            res = self.write('show ip interface ip {0}'.format(ip))
            if not res:
                return dumps({
                    'status' : Status.CANTESTABLISH
                })
            res = self.tn.read_until('{0}:BRAS01#'.format(self.greet), 5)
        except timeout:
            return dumps({
                'status' : Status.TIMEOUT
            })
        except:
            print('in e120 fetch except()')
            print_exc()
            print_stack()
            return dumps({
                'status' : Status.ERROR
            })

        if not res:
            print('timeout in empty return')
            return dumps({
                'status' : Status.TIMEOUT
            })

        # нет сессии
        if 'Invalid interface' in res:
            return dumps({
                'status' : Status.EMPTY
            })

        # счетчики байтов, первый IN, второй OUT
        counters = []
        # записываем оба полиси для IN и OUT
        policys = []
        # commited rate
        speed = -1
        for line in res.split("\n"):
            line = line.strip()
            if line.startswith('IP policy'):
                policys.append(line.split()[3])
            elif any(s in line for s in ('Received', 'Forwarded')):
                counters.append(line.split()[5])
            elif line.startswith('committed rate:'):
                speed = line.split()[2]

        # если IN / OUT policy отличаются, вернем оба, если нет - первое
        policy = 'Empty policy'
        if policys:
            policy = policys[0] if policys[0] == policys[1] else ' / '.join(policys)
        counter = ' / '.join(counters)

        try:
            speed = int(speed) / 1024
        except ValueError:
            pass
        mod = ''
        if speed > 1000:
            speed /= 1000
            mod = ' Мб/c'
        elif speed != -1:
            mod = ' Кб/c'
        r_speed = '{0}{1}'.format(speed, mod)

        body = {
            'source'    : self.clname.upper(),
            'policy'    : policy,
            'counter'   : counter,
            'speed'     : r_speed
        }

        return dumps({
            'status'    : Status.SUCCESS,
            'body'      : body
        })

    def delete_session(self, ip):
        """ Метод для удаления сессии на Брасе """
        try:
            res = self.write('configure terminal')
            if not res:
                return dumps({
                    'status' : Status.CANTESTABLISH
                })
            self.tn.read_until('{0}:BRAS01(config)#'.format(self.greet), 5)
            self.write('no interface ip {0}'.format(ip))
            self.tn.read_until('{0}:BRAS01(config)#'.format(self.greet), 5)
            self.write('end')
            self.tn.read_until('{0}:BRAS01#'.format(self.greet), 5)
        except timeout:
            print('timeout in E120 del func')
            return dumps({
                'status' : Status.TIMEOUT
            })
        except:
            print('fail to delete session on E120')
            print_exc()
            print_stack()
            return dumps({
                'status' : Status.ERROR
            })

        return dumps({
            'status' : Status.SUCCESS
        })
