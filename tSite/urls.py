from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^parser_artrum/', include('parser_artrum.urls')),
    url(r'^admin/', admin.site.urls),
]
