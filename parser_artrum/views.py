from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from parser_artrum.parser import ParserArtRum
import threading
import os


@csrf_protect
def index(request):
    if 'state' in request.GET:
        state = request.GET['state']
        config = {
            'path_parser_dir': 'parser_artrum',
            'path_out_dir': 'out',
            'log': 1,
            'json_file_indent': None,
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
    return render(
        request,
        "parcer_artrum.html",
        {}
    )
