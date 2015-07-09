# coding: utf-8
''' Класс для авторизации в Active Directory '''

from ldap import initialize, VERSION3, OPT_REFERRALS, INVALID_CREDENTIALS, SERVER_DOWN, OPT_HOST_NAME
from Status import Status


class Ldap(object):
    ''' Класс для авторизации в Active Directory '''
    def __init__(self, host):
        self.ldap = initialize('ldap://{0}'.format(host))
        self.ldap.protocol_version = VERSION3
        self.ldap.set_option(OPT_REFERRALS, 0)

    def authorize(self, user, pwd, domain):
        try:
            self.ldap.simple_bind_s('{0}@{1}'.format(user, domain), pwd)
            return Status.SUCCESS
        except INVALID_CREDENTIALS:
            print('fail ldap auth {0}, {1}, {2}'.format(self.ldap.get_option(OPT_HOST_NAME), user, domain))
            return Status.WRONG_PW
        except SERVER_DOWN:
            print('server down {0}, {1}, {2}'.format(self.ldap.get_option(OPT_HOST_NAME), user, domain))
            return Status.SERVER_DOWN
        except UnicodeEncodeError:
            print('unicode error {0}, {1}, {2}'.format(self.ldap.get_option(OPT_HOST_NAME), user, domain))
            return Status.ERRSYMBOLS
        finally:
            self.ldap.unbind_s()
