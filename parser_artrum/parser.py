from pyquery import PyQuery as pq
import requests
import threading
from multiprocessing import Queue
import time
import json
import os
import redis


class ParserArtRum:
    def __init__(self, **kwargs):
        self.config = {
            # имя папки в которой находится парсер
            'path_parser_dir': 'parser_artrum',
            # имя папки в директории дарсера в которой будут находится файлы с результатом парсинга
            'path_out_dir': 'out',
            # название файла для хранения результатов парсинга
            'json_file': 'parser_json.txt',
            # включить структурирование информации в выходном файле
            'json_file_indent': None,
            # название файла для хранения списка файлов для скачивания
            'json_download_file': 'download_file_json.txt',
            # адрес сайта для парсинга
            'base_link': 'http://art-rum.ru',
            # наименование разделов для сканирования
            'categorys': ['kaminy',
                          'topki',
                          'pechi'],

            # включить отображение лога
            'log': 0,
        }
        # счетчик активных потоков
        self.cur_thread = 0
        # создается очередь адресов парсинга
        self.queue = Queue()
        # блокировка парсера
        self.lock = threading.Lock()
        # выходной словарь данных парсинга
        self.out = {}

        # структура записей хранимых в Redis
        self.redis_conf = {
            'counter': 'page:counter',
            'url': 'page:url',
            'file': 'page:file',
            'out': 'page:out'
        }

        # Подключаемся к Redis
        self.redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0, decode_responses=True)

        # обработка входящих данных и их применение
        for key, val in kwargs.items():
            if key in self.config:
                self.config[key] = val

    def run(self):
        # очистка файлов хранения результатов парсинга
        self.out_file_clear(self.config['json_file'])
        self.out_file_clear(self.config['json_download_file'])

        # устанавливаем счетчик страниц в 0
        r = self.redis_connect()
        r.set(self.redis_conf['counter'], 0)

        # заполнение очереди предустановлеными адресами
        for category in self.config['categorys']:
            # читаем из сформированого url и добавляем его в очередь
            self.add_queue('/{}/'.format(category), r)

        # фиксируем число используемых потоков
        self.cur_thread = threading.active_count()

        while True:
            if self.queue.qsize() > 0 :
                # обработчик очереди
                self.refresh_queue()
            else:
                # ожидание завершения работы всех созданных потоков
                if self.cur_thread != threading.active_count():
                    time.sleep(0.5)
                else:
                    break

        if self.config['log']:
            print('page count = {}, downloads file count = {}'.
                  format(r.get(self.redis_conf['counter']),
                         r.scard(self.redis_conf['file'])))

        # заполнение файлов хранения результатов парсинга
        self.out_file(self.config['json_file'],
                      self.out_json(self.out))
        self.out_file(self.config['json_download_file'],
                      str(r.smembers(self.redis_conf['file'])))

    def redis_connect(self):
        return redis.StrictRedis(connection_pool=self.redis_pool)

    def add_queue(self, url, r_cur):
        with self.lock:
            if r_cur.sadd(self.redis_conf['url'], url):
                self.queue.put(url)
            else:
                if self.config['log']:
                    print('---- duplicate ---- url( {} )'.format(url))

    def refresh_queue(self):
        # функция для запуска в новом потоке
        # достаем адресс из очереди и подготавливаем поток для его обработки
        thread = threading.Thread(target=self.parser, args=(self.queue.get(),))

        # ограничивыаем число одновременно работающих потоков
        while threading.active_count() > 100:
            time.sleep(0.2)

        # запускаем новый поток
        thread.start()

    def out_json(self, out):
        return json.dumps(out, sort_keys=True, indent=self.config['json_file_indent'])

    def out_file(self, file, out):
        with open(os.path.join(self.config['path_parser_dir'], self.config['path_out_dir'], file), 'w') as f:
            f.write(out)
            if self.config['log']:
                print('file write - {}'.format(file))

    def out_file_clear(self, file):
        with open(os.path.join(self.config['path_parser_dir'],
                               self.config['path_out_dir'],
                               file), 'w') as f:
            f.write('')
            if self.config['log']:
                print('file clear - {}'.format(file))

    def get_content(self, url, find=None):
        response = requests.get('{}{}'.format(self.config['base_link'], url))
        return pq(response.content).find(find) if find else pq(response.content)

    def parser(self, url):
        r_cur = self.redis_connect()
        r_cur.incr(self.redis_conf['counter'])

        if self.config['log']:
            print('№{} - url( {} )'.format(r_cur.get(self.redis_conf['counter']), url))

        p_types = [self.type_1,
                   self.type_2,
                   self.type_3
                   ]
        # читаем страницу и сразу ее парсим
        content = self.get_content(url, 'body div#main')

        # пробуем парсить страницу разными обработчиками
        for p_type in p_types:
            # передаем страницу в обработчик
            cur_type = p_type(content)
            # в случае пустоты пробуем следующий обработчик
            if cur_type:
                with self.lock:
                    self.out.update(cur_type)
                return

    def type_1(self, content):
        r_cur = self.redis_connect()
        out = {}
        name = ''
        img = ''
        for cur_li in content.find('ul.catalog.treepic li'):
            for link in pq(cur_li).children('a'):
                if pq(link).text():
                    name = pq(link).text()
                    href = pq(link).attr('href')
                    self.add_queue(href, r_cur)
                    out[name] = {'link': href}
                else:
                    img = {}
                    for img_link in pq(link).children('div div'):
                        cur_img = pq(img_link).children('img').attr('src')
                        r_cur.sadd(self.redis_conf['file'], cur_img)
                        img.update({pq(img_link).attr('class'): cur_img})
            out[name]['img'] = img
        return out

    def type_2(self, content):
        r_cur = self.redis_connect()
        out = self.type_2_page(content, r_cur)
        for next_page in content.find('div.text-box font a'):
            if str(pq(next_page).text()).isdigit():
                out.update(self.type_2_page(self.get_content(pq(next_page).attr('href')), r_cur))
        return out

    def type_2_page(self, content, r_cur):
        out = {}
        name = ''
        img = ''
        for cur_li in content.find('ul.catalog li'):
            for link in pq(cur_li).children('a'):
                text = pq(link).text()
                if text:
                    name = text
                    href = pq(link).attr('href')
                    self.add_queue(href, r_cur)
                    out[name] = {'link': href}
                    # out[name]['ext'] = self.parser(href)
                else:
                    img = pq(link).children('div span img').attr('src')
            out[name]['img'] = img
            r_cur.sadd(self.redis_conf['file'], img)
        return out

    def type_3(self, content):
        r_cur = self.redis_connect()
        out = {}
        scheme = {}
        out['img'] = content.find('a.group-full-img.jqzoom').attr('href')
        r_cur.sadd(self.redis_conf['file'], out['img'])
        html = content.find('div.text-box.small')
        for html_img in pq(html).children('img'):
            r_cur.sadd(self.redis_conf['file'], pq(html_img).attr('src'))
        out['html'] = pq(html).html()
        for cur_scheme in content.find('div.file_catalog.schema'):
            link = pq(cur_scheme).find('div.file a.group-full-img')
            r_cur.sadd(self.redis_conf['file'], pq(link).attr('href'))
            scheme[pq(link).text()] = pq(link).attr('href')
        out['scheme'] = scheme
        return out

    def clear_redis(self):
        r_cur = self.redis_connect()
        for value in self.redis_conf.values():
            r_cur.delete(value)


if __name__ == '__main__':
    settings = {
        'path_parser_dir': os.getcwd(),
        'json_file_indent': 4,
        'log': 1,
    }
    a = ParserArtRum(**settings)
    a.run()
    a.clear_redis()
