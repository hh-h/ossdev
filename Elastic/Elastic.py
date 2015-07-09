# coding: utf8

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
from time import strftime, localtime


class Elastic(object):
    """ Базовый класс для работы с базой ElasticSearch """
    def __init__(self, di):
        self.host   = di['host']
        self.port   = int(di['port'])
        self.con    = None
        self.index  = di['index']

    def __connect(self):
        ''' Соединение с базой '''
        self.con = Elasticsearch([{'host' : self.host, 'port' : self.port}])
        self.con.info()

    def search_all(self, query):
        """ Выполняет поиск в базе, если нет соединения - пересоединяется """
        res = None
        index = '{0}-*'.format(self.index)
        try:
            res = self.con.search(index=index, body=query)
        except (AttributeError, ConnectionError):
            self.__connect()
            res = self.con.search(index=index, body=query)
        return res

    def store(self, query):
        """ Выполняет запрос к базе, если нет соединения - пересоединяется """
        index = '{0}-{1}'.format(self.index, strftime('%Y.%m.%d', localtime()))
        try:
            self.con.index(index=index, doc_type='logs', body=query)
        except (AttributeError, ConnectionError):
            try:
                self.__connect()
                self.con.index(index=index, doc_type='logs', body=query)
            except ConnectionError:
                print('failed to connect elasticsearch')
                print(query)
