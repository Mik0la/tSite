from pyquery import PyQuery as pq
import requests
import json
import os


class ParserArtRum():
    def __init__(self, **kwargs):
        self.config = {
            'path_parser_dir': 'parser_artrum',
            'path_out_dir': 'out',
            'categorys': ['kaminy',
                          'topki',
                          'pechi'],
            'base_link': 'http://art-rum.ru',
            'json_file': 'parser_json.txt',
            'json_file_indent': 0,
            'json_download_file': 'download_file_json.txt',
            'log': 0,
        }
        self.out = {}
        self.page = 0
        self.page_check = set()
        self.download_files = set()
        for key, val in kwargs.items():
            if key in self.config:
                self.config[key] = val

    def run(self):
        self.out_file_clear(self.config['json_file'])
        self.out_file_clear(self.config['json_download_file'])
        for category in self.config['categorys']:
            # Читаем из сформированого url
            self.out[category] = self.parser('/{}/'.format(category))
            # Разбираем скелет страницы
        self.out_file(self.config['json_file'], self.out_json(self.out, self.config['json_file_indent']))
        self.out_file(self.config['json_download_file'], self.out_json(list(self.download_files),
                                                                       self.config['json_file_indent']))

    def get_content(self, url, find=None):
        response = requests.get('{}{}'.format(self.config['base_link'], url))
        return pq(response.content).find(find) if find else pq(response.content)

    def parser(self, url):
        if url in self.page_check:
            if self.config['log']:
                print('pass - {}'.format(url))
        else:
            self.page_check.add(url)
            self.page += 1
            if self.config['log']:
                print(r'{}   {}    url( {} )'.format(self.page, len(self.download_files), url))
            p_types = [self.type_1,
                       self.type_2,
                       self.type_3
                       ]
            content = self.get_content(url, 'body div#main')
            out = {}
            for p_type in p_types:
                cur_type = p_type(content)
                if cur_type:
                    for key, value in cur_type.items():
                        if type(value) == dict and value.get('link'):
                            child = self.parser(value['link'])
                            if child:
                                cur_type[key]['children'] = child
                    out.update(cur_type)
                    break
            return out

    def type_1(self, content):
        out = {}
        name = ''
        img = ''
        for cur_li in content.find('ul.catalog.treepic li'):
            for link in pq(cur_li).children('a'):
                if pq(link).text():
                    name = pq(link).text()
                    href = pq(link).attr('href')
                    out[name] = {'link': href}
                else:
                    img = {}
                    for img_link in pq(link).children('div div'):
                        cur_img = pq(img_link).children('img').attr('src')
                        self.download_files.add(cur_img)
                        img.update({pq(img_link).attr('class'): cur_img})
            out[name]['img'] = img
        return out

    def type_2(self, content):
        out = self.type_2_page(content)
        for next_page in content.find('div.text-box font a'):
            if str(pq(next_page).text()).isdigit():
                out.update(self.type_2_page(self.get_content(pq(next_page).attr('href'))))
        return out

    def type_2_page(self, content):
        out = {}
        name = ''
        img = ''
        for cur_li in content.find('ul.catalog li'):
            for link in pq(cur_li).children('a'):
                text = pq(link).text()
                if text:
                    name = text
                    href = pq(link).attr('href')
                    out[name] = {'link': href}
                    out[name]['ext'] = self.parser(href)
                else:
                    img = pq(link).children('div span img').attr('src')
            out[name]['img'] = img
            self.download_files.add(img)
        return out

    def type_3(self, content):
        out = {}
        scheme = {}
        out['img'] = content.find('a.group-full-img.jqzoom').attr('href')
        self.download_files.add(out['img'])
        html = content.find('div.text-box.small')
        for html_img in pq(html).children('img'):
            self.download_files.add(pq(html_img).attr('src'))
        out['html'] = pq(html).html()
        for cur_scheme in content.find('div.file_catalog.schema'):
            link = pq(cur_scheme).find('div.file a.group-full-img')
            self.download_files.add(pq(link).attr('href'))
            scheme[pq(link).text()] = pq(link).attr('href')
        out['scheme'] = scheme
        return out

    def out_json(self, out, indent=None):
        return json.dumps(out, sort_keys=True, indent=indent)

    def out_file(self, file, out):
        with open(os.path.join(self.config['path_parser_dir'], self.config['path_out_dir'], file), 'w') as f:
            f.write(out)
            if self.config['log']:
                print('file write - {}'.format(file))

    def out_file_clear(self, file):
        with open(os.path.join(self.config['path_parser_dir'], self.config['path_out_dir'], file), 'w') as f:
            f.write('')
            if self.config['log']:
                print('file clear - {}'.format(file))

    def __str__(self):
        return self.out_json(self.out, indent=4)
