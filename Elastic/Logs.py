# coding: utf-8

""" Класс для работы с логами OSS """

from Elastic import Elastic
from json import dumps
from Status import Status
from time import strptime, strftime
from datetime import datetime


class Logs(Elastic):
    """ Класс для работы с логами OSS """

    def __add_user(self, user):
        try:
            self.query['query']['bool']['must'].append({
                'match' : {
                    'user' : user
                }
            })
        except KeyError:
            self.query = {
                'query' : {
                    'bool' : {
                        'must' : [
                            {
                                'match' : {
                                    'user' : user
                                }
                            }
                        ]
                    }
                }
            }

    def __add_module(self, module):
        try:
            self.query['query']['bool']['must'].append({
                'match' : {
                    'group' : module
                }
            })
        except KeyError:
            self.query = {
                'query' : {
                    'bool' : {
                        'must' : [
                            {
                                'match' : {
                                    'group' : module
                                }
                            }
                        ]
                    }
                }
            }

    def __add_date(self, start, end):
        # 26.02.2015 12:27
        # YYYY-MM-DD'T'HH:mm
        start = strptime(start, '%d.%m.%Y %H:%M')
        end = strptime(end, '%d.%m.%Y %H:%M')
        start = strftime('%Y-%m-%dT%H:%M', start)
        end = strftime('%Y-%m-%dT%H:%M', end)
        try:
            self.query['query']['bool']['must'].append({
                'range' : {
                    'timestamp' : {
                        'gt' : start,
                        'lt' : end
                    }
                }
            })
        except KeyError:
            self.query = {
                'query' : {
                    'bool' : {
                        'must' : [
                            {
                                'range' : {
                                    'timestamp' : {
                                        'gt' : start,
                                        'lt' : end
                                    }
                                }
                            }
                        ]
                    }
                }
            }

    def __add_phrase(self, phrase):
        try:
            self.query['query']['bool']['must'].append({
                'match' : {
                    'action' : phrase
                }
            })
        except KeyError:
            self.query = {
                'query' : {
                    'bool' : {
                        'must' : [
                            {
                                'match' : {
                                    'action' : phrase
                                }
                            }
                        ]
                    }
                }
            }

    def get_user_logs(self, data):
        ''' Достаем информацию о действиях пользователя '''
        self.query = {}

        if 'user' in data and data['user']:
            self.__add_user(data['user'])

        if 'module' in data and data['module']:
            self.__add_module(data['module'])

        if 'enddate' in data and data['enddate'] \
                and 'startdate' in data and data['startdate']:
            self.__add_date(data['startdate'], data['enddate'])

        if 'phrase' in data and data['phrase']:
            self.__add_phrase(data['phrase'])

        self.query['size'] = 200
        self.query['sort'] = {
            'timestamp' : {
                'order' : 'desc'
            }
        }

        res = self.search_all(self.query)
        if res['hits']['total'] == 0:
            return dumps({
                'status'    : Status.EMPTY
            })

        result = []
        for hit in res['hits']['hits']:
            hit = hit['_source']
            row = {}
            date = strptime(hit['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
            time = strftime('%d/%m %H:%M:%S', date)
            row['time'] = time
            row['user'] = hit['user']
            row['action'] = hit['action'].encode('utf8')
            result.append(row)

        return dumps({
            'status'    : Status.SUCCESS,
            'data'      : result
        })

    def save_action(self, who, group, what):
        ''' Записываем действие пользователя в базу '''
        date = datetime.now()
        query = {
            'user'      : who,
            'action'    : what,
            'group'     : group,
            'timestamp' : date
        }
        self.store(query)

    def get_unique_users(self):
        ''' Возвращаем список пользователей, которые работали с системой '''
        query = {
            'aggs' : {
                'langs' : {
                    'terms' : {
                        'field' : 'user',
                        'size'  : 0
                    }
                }
            }
        }

        res = self.search_all(query)
        result = []
        for i in res['aggregations']['langs']['buckets']:
            result.append(i['key'])
        return result
