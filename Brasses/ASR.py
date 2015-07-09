# coding: utf-8
""" Класс для работы с сессиями ASR """

from Bras import Bras
from Status import Status
from socket import timeout
from json import dumps
from traceback import print_exc, print_stack


class ASR(Bras):
    """ Класс для работы с сессиями ASR """

    def prepare_cli(self):
        """ Подготовка к выполнению команд в терминале """
        self.write('terminal length 0')
        self.tn.read_until('{0}#'.format(self.greet))

    def find_session(self, ip):
        """ Метод для поиска сессии на Брасе """
        res = ''
        try:
            res = self.write('show subscriber session identifier source-ip-address {0} 255.255.255.255'.format(ip))
            if not res:
                return dumps({
                    'status' : Status.CANTESTABLISH
                })
            res = self.tn.expect(['{0}#'.format(self.greet)], 5)
            if res[0] == -1:
                return dumps({
                    'status' : Status.ERROR
                })
            res = res[2]
        except timeout:
            return dumps({
                'status' : Status.TIMEOUT
            })
        except:
            print('in asr except()')
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

        if 'Session' not in res or 'No active' in res:
            return dumps({
                'status' : Status.EMPTY
            })

        # счетчики времени сессий, первый Uptime, второй Last Changed
        timers = []
        # счетчики байтов, первый IN, второй OUT
        counters = []
        # записываем оба полиси для IN и OUT
        policys = []
        # статус сессии
        status = ''
        # скорость
        speed = -1

        for line in res.split('\n'):
            line = line.strip()
            if line.startswith('Session'):
                timers += [line.split()[2], line.split()[5]]
            elif line.startswith('Authentication'):
                status = line.split()[2]
            elif line.startswith('name'):
                policys.append(line.split('"')[1])
            elif line.startswith('Classifiers'):
                break

        r_speed = 0
        # разобьем результат на 2 половины, потом вторую часть по пробелам
        if 'Accounting:' in res:
            tmp = res.split('Accounting:')[1]
            traf = tmp.split(None, 15)
            # 8 поле IN bytes, 13 OUT bytes
            counters += [traf[8], traf[13]]

            tmp = tmp.split('Policing:')

            if len(tmp) > 1:
                tmp = tmp[1].split(None, 25)
                speed = -1
                try:
                    speed = int(tmp[23]) / 1024
                except ValueError:
                    pass
                mod = ''
                if speed > 1000:
                    speed /= 1000
                    mod = ' Мб/c'
                elif speed != -1:
                    mod = ' Кб/c'
                r_speed = '{0}{1}'.format(speed, mod)
            else:
                r_speed = 'jail'

        policy = '' if not policys else ', '.join(policys)
        sesstime = 'None' if not timers else ' '.join(timers)
        counter = 'None' if not counters else ' / '.join(counters)

        body = {
            'source'    : self.clname.upper(),
            'policy'    : policy,
            'counter'   : counter,
            'status'    : status,
            'time'      : sesstime,
            'speed'     : r_speed
        }

        return dumps({
            'status'    : Status.SUCCESS,
            'body'      : body
        })

    def delete_session(self, ip):
        """ Метод для удаления сессии на Брасе """
        try:
            res = self.write('clear subscriber session identifier source-ip-address {0} 255.255.255.255'.format(ip))
            if not res:
                return dumps({
                    'status' : Status.CANTESTABLISH
                })
            res = self.tn.expect(['{0}#'.format(self.greet)], 5)
            if res[0] == -1:
                return dumps({
                    'status' : Status.ERROR
                })
        except timeout:
            print('timeout in asr del func')
            return dumps({
                'status' : Status.TIMEOUT
            })
        except:
            print('fail to delete session on ASR')
            print_exc()
            print_stack()
            return dumps({
                'status' : Status.ERROR
            })
        return dumps({
            'status' : Status.SUCCESS
        })
