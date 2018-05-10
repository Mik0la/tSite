from django.conf.urls import include, url
from django.contrib import admin
# from parser_artrum.views import artrum
# from bot.views import bot

urlpatterns = [
    #  url(r'^parser_artrum/', include('parser_artrum.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^bot/', include('bot.urls')),
]
