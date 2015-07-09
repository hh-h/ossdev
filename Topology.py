# coding: utf8

from pymongo import MongoClient
from json import dumps
from Color import Color
from Status import Status


class Topology(object):
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.summaswitches.switchesold2
        # объект для нодов и эджей cytoscape.js
        self.elements = {'nodes': [], 'edges': []}
        # layout для cytoscape.js
        self.layout = {}
        # все свитчи агрегатора, чтобы не дергать базу
        self.switches = {}
        # искомый свитч
        self.ip = ''

    def __create_nodes(self, vertices):
        ''' заполняет словарь элементов для библиотеки Cytoscape.js нодами '''
        for v in vertices:
            sw = self.switches[v]
            color = Color.OFFLINE
            if 'online' in sw and sw['online']:
                color = Color.ONLINE
            shape = 'ellipse'
            if 'role' in sw and sw['role'] == 'aggregator':
                shape = 'rectangle'
            location = 'Nowhere'
            if 'location' in sw and sw['location']:
                location = sw['location']
            sysname = 'NaN'
            if 'sysname' in sw and sw['sysname']:
                sysname = sw['sysname']

            n = sw['ip']

            uid = sw['ip']

            node = {
                'data': {
                    'id'        : uid,
                    'ip'        : n,
                    'shape'     : shape,
                    'sysname'   : sysname,
                    'location'  : location,
                    'color'     : color
                }
            }
            if sw['ip'] == self.ip:
                node['data']['blacken'] = 0.4

            self.elements['nodes'].append(node)

    def __create_edges(self, edges, num=None):
        ''' заполняет словарь элементов для библиотеки Cytoscape.js эджами '''
        count = len(self.elements['edges']) + 1
        for e in edges:
            target = e[0]
            source = e[1]

            # найдем связные объекты
            # куда ведет источник
            t1 = {}
            for k, v in self.switches[source]['ports'].iteritems():
                if v['neighbour'] == target:
                    # сохраним порт для последующей обработки
                    t1 = v
                    # удалим порт из базы, чтобы избежать ошибок при обработке колец с одним свитчем
                    del self.switches[source]['ports'][k]
                    # выйдем
                    break
            # куда ведет назначение
            t2 = {}
            for k, v in self.switches[target]['ports'].iteritems():
                if v['neighbour'] == source:
                    # сохраним порт для последующей обработки
                    t2 = v
                    # удалим порт из базы, чтобы избежать ошибок при обработке колец с одним свитчем
                    del self.switches[target]['ports'][k]
                    # выйдем
                    break

            if not t1 or not t2:
                # у нас петля на порту
                if target == source:
                    # просто скопируем данные
                    t2 = t1
                # странная херня, не вижу как оно может быть
                else:
                    print(t1, t2)
                    raise NameError('wierd')

            color = Color.OFFLINE
            if t1['up'] == t2['up'] == 1 and \
                    'online' in self.switches[source] and self.switches[source]['online'] and \
                    'online' in self.switches[target] and self.switches[target]['online']:
                color = Color.ONLINE

            errors = t1['errors'] + t2['errors']

            edge = {
                'data': {
                    'target': target,
                    'source': source,
                    'color' : color,
                    'errors': errors
                }
            }
            count += 1

            self.elements['edges'].append(edge)

    def __create_govno_nodes(self, vertices, name=None, num=None):
        ''' заполняет словарь элементов для библиотеки Cytoscape.js нодами '''
        parent = 'mnode{0}'.format(num)

        node = {
            'data': {
                'id'        : parent,
                'ip'        : '',
                'shape'     : 'rectangle',
                'color'     : Color.WHITE
            }
        }
        self.elements['nodes'].append(node)

        count = len(self.elements['nodes'])

        for v in vertices:
            sw = self.switches[v]
            color = Color.OFFLINE
            if 'online' in sw and sw['online']:
                color = Color.ONLINE
            shape = 'ellipse'
            if 'role' in sw and sw['role'] == 'aggregator':
                shape = 'rectangle'
            location = 'Nowhere'
            if 'location' in sw and sw['location']:
                location = sw['location']
            sysname = 'NaN'
            if 'sysname' in sw and sw['sysname']:
                sysname = sw['sysname']

            n = sw['ip']
            if name and sw['ip'] == self.ip:
                n = repr(name)
                if len(name) == 2:
                    n = u'◄ {0}    \n     {1} ►'.format(*[x.replace('GigabitEthernet', 'GI') for x in name])
                elif len(name) == 1:
                    n = name[0].replace('GigabitEthernet', 'GI')
                sysname = n
                location = n

            uid = sw['ip']
            if num and sw['ip'] == self.ip:
                uid = '0node{0}'.format(num)

            node = {
                'data': {
                    'id'        : uid,
                    'ip'        : n,
                    'shape'     : shape,
                    'sysname'   : sysname,
                    'location'  : location,
                    'color'     : color,
                    'parent'    : parent
                }
            }
            if sw['ip'] == self.ip:
                node['data']['blacken'] = 0.4
                self.elements['nodes'].insert(count, node)
            else:
                self.elements['nodes'].append(node)

    def __create_govno_edges(self, edges, num=None):
        ''' заполняет словарь элементов для библиотеки Cytoscape.js эджами '''
        count = len(self.elements['edges']) + 1
        current = self.ip
        next_hope = ''
        while edges:
            for e in edges:
                if e[0] == current or e[1] == current:
                    edges.remove(e)
                    next_hope = e[0] == current and e[1] or e[0]
                    break
            else:
                e = edges.pop(0)
                current = e[0]
                next_hope = e[1]
            source = current
            target = next_hope

            # найдем связные объекты
            # куда ведет источник
            t1 = {}
            for k, v in self.switches[source]['ports'].iteritems():
                if v['neighbour'] == target:
                    # сохраним порт для последующей обработки
                    t1 = v
                    # удалим порт из базы, чтобы избежать ошибок при обработке колец с одним свитчем
                    del self.switches[source]['ports'][k]
                    # выйдем
                    break
            # куда ведет назначение
            t2 = {}
            for k, v in self.switches[target]['ports'].iteritems():
                if v['neighbour'] == source:
                    # сохраним порт для последующей обработки
                    t2 = v
                    # удалим порт из базы, чтобы избежать ошибок при обработке колец с одним свитчем
                    del self.switches[target]['ports'][k]
                    # выйдем
                    break

            if not t1 or not t2:
                # у нас петля на порту
                if target == source:
                    # просто скопируем данные
                    t2 = t1
                # странная херня, не вижу как оно может быть
                else:
                    print(t1, t2)
                    raise NameError('wierd')

            color = Color.OFFLINE
            if t1['up'] == t2['up'] == 1 and \
                    'online' in self.switches[source] and self.switches[source]['online'] and \
                    'online' in self.switches[target] and self.switches[target]['online']:
                color = Color.ONLINE

            errors = t1['errors'] + t2['errors']

            if source == self.ip:
                source = '0node{0}'.format(num)
            if target == self.ip:
                target = '0node{0}'.format(num)

            edge = {
                'data': {
                    # 'id'    : uid,
                    'target': target,
                    'source': source,
                    'color' : color,
                    'errors': errors
                }
            }
            count += 1

            self.elements['edges'].append(edge)
            current = next_hope

    def __get_single_switch(self, data):
        ''' Возвращает свитч из базы по сиснейму или IP, False если не найдено '''

        query = {
            '$or' : [
                {
                    'ip': data
                },
                {
                    'sysname': data
                }
            ]
        }
        res = self.db.find(query, {
            '_id': 0
        })
        if res.count() == 0:
            return False
        return list(res)[0]

    def __get_vertices(self, ip):
        ''' Возвращает список всех вершин для графа '''
        visited = set()
        stack = [ip]
        while stack:
            vertex = stack.pop()
            if vertex not in visited:
                visited.add(vertex)
                tmp = set()
                sw = self.switches[vertex]
                if sw['role'] == 'aggregator':
                    continue
                for v in sw['ports'].values():
                    tmp.add(v['neighbour'])
                stack.extend(tmp - visited)
        return list(visited)

    def __get_edges(self, vertices):
        ''' Возвращает список всех эджей между входными вершинами '''
        edges = []
        for v1 in vertices:
            sw = self.switches[v1]
            for v2 in sw['ports'].values():
                neighbour = v2['neighbour']
                if neighbour in vertices:
                    edges.append(sorted([v1, v2['neighbour']]))

        new_edges = []
        while edges:
            v = edges.pop()
            new_edges.append(v)
            if v[0] != v[1]:
                if v in edges:
                    edges.remove(v)
                else:
                    print(v, 'not in edges!')
        return new_edges

    def __make_breadthfirst_layout(self, vertices):
        ''' breadthfirst layout для библиотеки Cytoscape.js '''
        # корень для шаблона библиотеки, точки в id надо экранировать
        for v in vertices:
            if self.switches[v]['role'] == 'aggregator':
                root = v.replace('.', '\\.')
                break
        self.layout = {
            'name': 'breadthfirst',
            'directed': False,
            'roots': '#' + root,
            'padding': 20,
            'fit': True
        }

    def __make_dagre_layout(self):
        ''' dagre layout для библиотеки Cytoscape.js '''
        self.layout = {
            'name'      : 'dagre',
            'minLen'    : 1.5,
            'nodeSep'   : 80,
            'rankSep'   : 50,
            'edgeSep'   : 20,
            'fit'       : True,
            'animate'   : False
        }

    def get_topology(self, data):
        ''' Возвращает объект нод и эджей, и layout для библиотеки cytoscape.js '''

        res = self.__get_single_switch(data)

        if not res:
            return dumps({
                'status': Status.EMPTY
            })

        role = res['role']
        self.ip = res['ip']
        belongs = res['belongs']

        switches = self.db.find({
            'belongs': belongs
        })

        if switches.count() == 0:
            return dumps({
                'status': Status.ERROR
            })

        # сохраним все свитчи этого агрегатора для удобной работы из памяти
        self.switches = {v['ip']: v for v in list(switches)}

        if role == 'access':
            vertices = self.__get_vertices(self.ip)
            edges = self.__get_edges(vertices)

            self.__create_nodes(vertices)
            self.__create_edges(edges)
            self.__make_breadthfirst_layout(vertices)
        elif role == 'aggregator':
            # сохраним список всех портов
            ports = self.switches[self.ip]['ports'].keys()
            p_dict = {}
            while ports:
                p_key = []
                port = ports.pop(0)
                p_key.append(port)
                ip = self.switches[self.ip]['ports'][port]['neighbour']
                vertices = self.__get_vertices(ip)

                for k, v in self.switches[self.ip]['ports'].iteritems():
                    if v['neighbour'] in vertices and k in ports:
                        p_key.append(k)
                        ports.remove(k)
                p_dict[tuple(p_key)] = vertices
            count = 1
            for k, v in p_dict.iteritems():
                edges = self.__get_edges(v)
                self.__create_govno_nodes(v, name=k, num=count)
                self.__create_govno_edges(edges, num=count)
                count += 1

            self.__make_dagre_layout()

        return dumps({
            'status'    : Status.SUCCESS,
            'elements'  : self.elements,
            'layout'    : self.layout
        })

    def get_info(self, data):
        ''' Возвращает объект топологии (свитч) из базы '''

        res = self.__get_single_switch(data)

        if not res:
            return dumps({
                'status': Status.EMPTY
            })

        data = {k: v for k, v in res.iteritems()}

        return dumps({
            'status': Status.SUCCESS,
            'data'  : data
        })

    def get_ports(self, data):
        ''' Возвращает список занятых портов из базы '''

        res = self.__get_single_switch(data)

        if not res:
            return dumps({
                'status': Status.EMPTY
            })

        return set(res['ports'].keys())

    def add_link(self, src_ip, src_port, dst_ip, dst_port):
        ''' принимает данные линка и добавляет его в базу '''
        # запрос для добавления линка на искомом свитче
        # TODO можно в один запрос, но зачем?
        src_sw = self.__get_single_switch(src_ip)
        dst_sw = self.__get_single_switch(dst_ip)
        if not src_sw or not dst_sw:
            msg = 'Один из свитчей не найден в базе {0} или {1}'.format(src_ip, dst_ip)
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        # проверим, что таких портов еще нет на свитчах
        if src_port in src_sw['ports'].keys():
            msg = 'Порт {0} уже есть на свитче {1}, надо сначала удалить руками!'.format(src_port, src_ip)
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        if dst_port in dst_sw['ports'].keys():
            msg = 'Порт {0} уже есть на свитче {1}, надо сначала удалить руками!'.format(dst_port, dst_ip)
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        # создадим объекты
        src_sw_port = {
            'errors'    : 0,
            'neighbour' : dst_ip,
            'up'        : 0
        }
        dst_sw_port = {
            'errors'    : 0,
            'neighbour' : src_ip,
            'up'        : 0
        }

        query1 = {}
        key = 'ports.{0}'.format(src_port)
        query1['$set'] = {key: src_sw_port}

        query2 = {}
        key = 'ports.{0}'.format(dst_port)
        query2['$set'] = {key: dst_sw_port}

        self.db.update({
            'ip': src_ip
        }, query1)

        self.db.update({
            'ip': dst_ip
        }, query2)

        return dumps({
            'status': Status.SUCCESS
        })

    def delete_link(self, ip, port):
        ''' удаляет порт port на свитче ip и его соседа '''
        src_sw = self.__get_single_switch(ip)
        if not src_sw:
            msg = 'Свитч {0} не найден в базе'.format(ip)
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        if port not in src_sw['ports'].keys():
            msg = 'no port {0} in {1}'.format(port, ip)
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })
        neighbour = src_sw['ports'][port]['neighbour']
        if not neighbour:
            msg = 'У {0} на порту {1} нет IP адреса'.format(ip, port)
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        dst_sw = self.__get_single_switch(neighbour)

        # если есть такой свитч в базе, попробуем с него тоже удалить порт
        if dst_sw:
            ports = []
            # пройдем все порты
            for p, v in dst_sw['ports'].iteritems():
                # если сосед не наш свитч, идем дальше
                if v['neighbour'] != ip:
                    continue
                # этот порт граничит с нужным свитчем, сохраним его и статус
                # это сделано для того, чтобы удалять дублирующиеся линки
                ports.append((p, v['up']))

            # если нашли порт, который ведет к нашем свитчу, попробуем его удалить
            if ports:
                query = {}
                # если порт один - все просто, удаляем его
                if len(ports) == 1:
                    key = 'ports.{0}'.format(ports[0][0])
                # портов больше чем один, удалим первый который лежит
                # если все в апе, удалим просто первый
                else:
                    port_to_del = ''
                    for p in ports:
                        if not p[1]:
                            port_to_del = p[0]
                            break
                    else:
                        port_to_del = ports[0][0]
                    key = 'ports.{0}'.format(port_to_del)

                # подготовим запрос для удаления
                query['$unset'] = {key: True}
                # ну и удалим этот порт
                # print neighbour, query
                self.db.update({
                    'ip': neighbour
                }, query)

        # освободим порт на нашем свитче
        query = {}
        key = 'ports.{0}'.format(port)
        query['$unset'] = {key: True}

        self.db.update({
            'ip': ip
        }, query)

        return dumps({
            'status': Status.SUCCESS
        })

    def delete_switch(self, ip):
        ''' Удаляет свитч из базы '''
        res = self.db.find_and_modify({
            'ip': ip
        }, remove=True)

        if not res:
            msg = 'Такого свитча нет в базе'
            print(msg)
            return dumps({
                'status': Status.ERROR,
                'msg'   : msg
            })

        # получим список соседей удаленного объекта
        neighbours = set()
        for v in res['ports'].values():
            neighbours.add(v['neighbour'])

        # если у него были соседи, эти линки надо удалить
        # не важно, что в цикле, там не может быть больше 40 итераций
        for n in neighbours:
            res = self.__get_single_switch(n)
            if not res:
                continue
            to_del = {}
            to_del['$unset'] = {}
            for p, v in res['ports'].iteritems():
                if v['neighbour'] != ip:
                    continue
                key = 'ports.{0}'.format(p)
                to_del['$unset'][key] = True
            # если нашли что удалять - удалим
            if to_del['$unset']:
                self.db.update({
                    'ip': n
                }, to_del)

        return dumps({
            'status': Status.SUCCESS
        })
