from django.conf.urls import include, url
from django.contrib import admin
from parser_artrum.views import index

urlpatterns = [
    url(r'^parser_artrum/', index),
    url(r'^admin/', admin.site.urls),
]
