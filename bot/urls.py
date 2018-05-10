from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.bot_out, name='bot_out'),
]