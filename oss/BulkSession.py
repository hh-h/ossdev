# coding: utf8

from netsnmp import Varbind, VarList, Session


class BulkSession(Session):
    """ обертка для работы с пакетной версией snmpwalk'a """
    def bulkwalk(self, oid):
        """ Принимает str oid, Возвращает tuple с листом [tag, val], False в случае неудачи """
        oid_base = oid
        res = []
        done = True
        while done:
            var = VarList(Varbind(oid))
            result = self.getbulk(0, 16, var)

            if not result:
                done = False
                break

            for i in var:
                if oid_base not in i.tag:
                    done = False
                    break
                res.append([i.tag, i.val])
            else:
                oid = i.tag

        if not res:
            return False

        return tuple(res)
