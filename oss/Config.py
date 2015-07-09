# coding: utf-8
""" Класс для работы с конфигом """

from json import load


class Config(object):
    """ Класс для работы с конфигом """

    def __init__(self, filename):
        """ Загружает в память конфиг, держит в себе ссылку на него """
        with open(filename, 'r') as f:
            self.cfg = load(f)

    def get(self, section):
        """ Возвращает словарь с запрашиваемой секцией """
        return self.cfg[section]
