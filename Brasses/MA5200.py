# coding: utf-8
""" Класс для работы с сессиями MA5200 """

from Bras import Bras
from Status import Status
from socket import timeout
from json import dumps
from traceback import print_exc, print_stack


class MA5200(Bras):
    """ Класс для работы с сессиями MA5200 """

    def prepare_cli(self):
        """ Метод для авторизации на Брасе
            результат сохраняет в базовом классе """
        self.write('system-view')
        self.tn.read_until('{0}]'.format(self.greet))
        self.write('aaa')
        self.tn.read_until('aaa]')

    def find_session(self, ip):
        """ Метод для поиска сессии на Брасе """
        res = ''
        for i in xrange(2):
            try:
                res = self.write('display access-user domain hsi username {0}@hsi detail'.format(ip))
                if not res:
                    return dumps({
                        'status' : Status.CANTESTABLISH
                    })
                res = self.tn.expect(['---', 'No user'], 5)
                answer = res[0]
                if answer == 1:
                    res = 'No user'
                elif answer == -1:
                    res = ''
                elif answer == 0:
                    res = res[2]
                    self.write(' ')
                    res += self.tn.read_until('---', 5)
                    self.write(' ')
                    res += self.tn.read_until('[y]:', 5)
                    self.write(' ')
                    self.tn.read_until('aaa]', 5)
                break

            except timeout:
                return dumps({
                    'status' : Status.TIMEOUT
                })
            except EOFError:
                pass
            except:
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
        if 'No user' in res:
            return dumps({
                'status' : Status.EMPTY
            })

        # счетчики байтов, первый IN, второй OUT
        counters = []
        # policy
        policy = ''
        # commited rate
        speed = -1
        for line in res.split("\n"):
            line = line.strip()
            if line.startswith('UserGroup'):
                policy = line.split()[2]
            elif any(s in line for s in ('Up bytes', 'Down bytes')):
                # Down bytes number(high,low)   : (0,477848)
                tmp = line.split(':')[1]
                # (0,477848) убираем скобки, делим по ',' берем второе значение
                counters.append(tmp[1:-1].split(',')[1])
            elif line.startswith('Up committed information'):
                speed = line.split()[5]

        counter = ' / '.join(counters)

        try:
            speed = int(speed)
        except ValueError:
            pass
        mod = ''
        if speed > 1024:
            speed /= 1024
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
        for i in xrange(2):
            try:
                res = self.write('cut access-user username {0}@hsi radius'.format(ip))
                if not res:
                    return dumps({
                        'status' : Status.CANTESTABLISH
                    })
                self.tn.read_until('aaa]', 5)
                break
            except timeout:
                print('timeout in ma5200 del func')
                return dumps({
                    'status' : Status.TIMEOUT
                })
            except EOFError:
                pass
            except:
                print_exc()
                print_stack()
                return dumps({
                    'status' : Status.ERROR
                })

        return dumps({
            'status' : Status.SUCCESS
        })
