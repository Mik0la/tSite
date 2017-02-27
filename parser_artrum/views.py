from django.shortcuts import render
from django.http import HttpResponse
from parser_artrum.parser import ParserArtRum
import threading
import os


def index(request):
    state = request.GET['state']
    config = {
        'path_parser_dir': 'parser_artrum',
        'path_out_dir': 'out',
        'log': 1,
        'json_file_indent': 4,
        'json_file': 'parser_json.txt',
        'json_download_file': 'download_file_json.txt',
    }
    if state == 'start':
        pars = ParserArtRum(**config)
        thread = threading.Thread(target=pars.run)
        thread.start()
        return HttpResponse('Start parsing')
    elif state == 'files':
        with open(os.path.join(config['path_parser_dir'],
                               config['path_out_dir'],
                               config['json_download_file']), 'rt') as f:
            return HttpResponse(f.read())
    elif state == 'struct':
        with open(os.path.join(config['path_parser_dir'],
                               config['path_out_dir'],
                               config['json_file']), 'rt') as f:
            return HttpResponse(f.read())
    return HttpResponse('Состояние неизвестно')
