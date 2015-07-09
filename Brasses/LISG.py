# coding: utf-8
""" Класс для работы с сессиями на linux bras'e ISG """

from Bras import Bras
from Status import Status
from socket import timeout
from json import dumps
from traceback import print_exc, print_stack


class LISG(Bras):
    """ Класс для работы с сессиями на linux bras'e ISG """

    def prepare_cli(self):
        """ Метод для авторизации на Брасе
            результат сохраняет в базовом классе """
        # не надо ничего делать
        pass

    def find_session(self, ip):
        """ Метод для поиска сессии на Брасе """
        res = ''
        try:
            res = self.write('/opt/ISG/bin/ISGkos.pl show_services {0}'.format(ip))
            if not res:
                return dumps({
                    'status' : Status.CANTESTABLISH
                })
            res = self.tn.expect([r'{0}\$'.format(self.greet)], 5)
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
            print('in isg except()')
            print_exc()
            print_stack()
            return dumps({
                'status' : Status.ERROR
            })

        if not res:
            return dumps({
                'status' : Status.EMPTY
            })

        # '10.78.154.119   1685       989        46080000   46080000   C46104K46080000  SOU'
        res = res.split('\n')
        if len(res) < 2:
            return dumps({
                'status' : Status.EMPTY
            })

        res = res[1]

        if 'Virtual' not in res:
            return dumps({
                'status' : Status.EMPTY
            })

        res = res.split()
        speed = -1
        try:
            speed = int(res[4]) / 1024
        except ValueError:
            pass

        if speed == 0:
            r_speed = 'jail'
        else:
            mod = ''
            if speed > 1000:
                speed /= 1000
                mod = ' Мб/c'
            elif speed != -1:
                mod = ' Кб/c'
            r_speed = '{0}{1}'.format(speed, mod)

        body = {
            'source'    : self.clname.upper(),
            'policy'    : res[6],
            'counter'   : ' / '.join([res[2], res[3]]),
            'speed'     : r_speed
        }

        return dumps({
            'status'    : Status.SUCCESS,
            'body'      : body
        })

    def delete_session(self, ip):
        """ Метод для удаления сессии на Брасе """
        try:
            res = self.write('/opt/ISG/bin/ISGkos.pl clear {0}'.format(ip))
            if not res:
                return dumps({
                    'status' : Status.CANTESTABLISH
                })
            self.tn.read_until('{0}$'.format(self.greet))
        except timeout:
            print('timeout in isg del func')
            return dumps({
                'status' : Status.TIMEOUT
            })
        except:
            print('fail to delete session on isg')
            print_exc()
            print_stack()
            return dumps({
                'status' : Status.ERROR
            })
        return dumps({
            'status' : Status.SUCCESS
        })
