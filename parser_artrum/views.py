from django.shortcuts import render
from django.http import HttpResponse
from pyquery import PyQuery as pq
import requests
import json


def art_rum():
    base_link = 'http://art-rum.ru'
    categorys = ['kaminy',
                 'topki',
                 'pechi']
    out_json = {}

    def get_content(url, find=None):
        response = requests.get('{}{}'.format(base_link, url))
        return pq(response.content).find(find) if find else pq(response.content)

    def parser(url):
        p_types = [type_1,
                   type_2,
                   type_3,
                   ]
        content = get_content(url, 'body div#main')
        out = {}
        for p_type in p_types:
            cur_type = p_type(content)
            if cur_type:
                for key, value in cur_type.items():
                    if type(value) == dict and value.get('link'):
                        child = parser(value['link'])
                        if child:
                            cur_type[key]['children'] = child
                out.update(cur_type)
                break
        return out

    def type_1(content):
        out = {}
        name = ''
        for cur_li in content.find('ul.catalog.treepic li'):
            for link in pq(cur_li).children('a'):
                if pq(link).text():
                    name = pq(link).text()
                    href = pq(link).attr('href')
                    out[name] = {'link': href}
                else:
                    img = {}
                    for img_link in pq(link).children('div div'):
                        img.update({pq(img_link).attr('class'): pq(img_link).children('img').attr('src')})
            out[name]['img'] = img
        return out

    def type_2(content):
        out = type_2_page(content)
        for next_page in content.find('div.text-box font a'):
            if str(pq(next_page).text()).isdigit():
                out.update(type_2_page(get_content(pq(next_page).attr('href'))))
        return out

    def type_2_page(content):
        out = {}
        name = ''
        for cur_li in content.find('ul.catalog li'):
            for link in pq(cur_li).children('a'):
                text = pq(link).text()
                if text:
                    name = text
                    href = pq(link).attr('href')
                    out[name] = {'link': href}
                    out[name]['ext'] = parser(href)
                else:
                    img = pq(link).children('div span img').attr('src')
            out[name]['img'] = img
        return out

    def type_3(content):
        out = {}
        scheme = {}
        out['img'] = content.find('a.group-full-img.jqzoom').attr('href')
        out['html'] = content.find('div.text-box.small').html()
        for cur_scheme in content.find('div.file_catalog.schema'):
            link = pq(cur_scheme).find('div.file a.group-full-img')
            scheme[pq(link).text()] = pq(link).attr('href')
        out['scheme'] = scheme
        return out

    for category in categorys:
        # Читаем из сформированого url
        out_json[category] = parser('/{}/'.format(category))
        # Разбираем скелет страницы

    return json.dumps(out_json, sort_keys=True, indent=4)


def index(request):
    return HttpResponse(art_rum())
