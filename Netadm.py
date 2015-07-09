# coding: utf8

from pymongo import MongoClient
from json import dumps
from bson.objectid import ObjectId
from Status import Status
from Helpers import check_abon


class Netadm(object):
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.summapoller.develop

    def findall(self, device, lx_type):
        query = {'device': device}
        lx_type = int(lx_type)
        if lx_type == 0:
            query['$or'] = [{'type': {'$exists': False}}, {'type': 0}]
        elif lx_type != -1:
            query['type'] = lx_type

        rows = self.db.find(query, {
            'device': 0,
            'changed': 0
        })
        ret = []
        for row in rows:
            tmp = {}
            tmp['id'] = str(row['_id'])
            tmp['port'] = row['portname']
            tmp['type'] = row['type'] if 'type' in row else ''
            tmp['descr'] = row['descr'] if 'descr' in row else ''
            tmp['active'] = row['sbms_active'] if 'sbms_active' in row else ''
            tmp['bill'] = row['bill'] if 'bill' in row else ''
            tmp['net'] = row['net'] if 'net' in row else ''
            if 'sbms_policy' in row:
                tmp['policy'] = row['sbms_policy']
                p_in = 'None' if 'in_policy' not in row else row['in_policy']
                p_out = 'None' if 'out_policy' not in row else row['out_policy']
                if p_in != p_out:
                    tmp['policy'] = '** {0} ({1}/{2})'.format(tmp['policy'], p_in, p_out)
                elif tmp['policy'] != p_out:
                    tmp['policy'] = '* {0} ({1})'.format(tmp['policy'], p_out)
            else:
                tmp['policy'] = ''
            ret.append(tmp)

        return dumps(ret)

    def store(self, portid, lx_type, abon, descr):
        if abon:
            new_abon = check_abon(abon)
            if not new_abon:
                msg = 'Невалидный номер абонента {0}!'.format(abon)
                print('{0} {1}'.format(msg, abon))
                return dumps({
                    'status': Status.ERROR,
                    'msg'   : msg
                })
            abon = new_abon

            res = self.db.find({'bill': abon}, {'portname': 1})
            if res.count() > 0:
                ports = []
                for r in res:
                    ports.append(r['portname'])
                msg = 'Абонент {0} уже привязан в базе к интерфейсам: {1}'.format(abon, ' '.join(ports))
                print(msg)
                return dumps({
                    'status': Status.ERROR,
                    'msg'   : msg
                })

        obj_id = ObjectId(portid)

        if self.db.find({'_id': obj_id}).count() != 1:
            msg = 'Не нашел такого айди {0} в базе!'.format(portid)
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        upd = {
            'descr'  : descr,
            'bill'   : abon,
            'type'   : int(lx_type),
            'changed': True
        }
        res = self.db.update({'_id': obj_id}, {'$set': upd})
        if res['ok'] == 1:
            return dumps({
                'status': Status.SUCCESS
            })
        msg = 'Не смог обновить данные в базе! {0}'.format(portid)
        print(msg)
        return dumps({
            'status': Status.ERROR,
            'msg'   : msg
        })
