# from django.urls import path

from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from . import views

from django.conf import settings
from django.views.static import serve
from django.conf.urls.static import static

app_name = 'stats'
urlpatterns = [

    path('', views.home, name='home'),
    path('auth', views.auth, name='auth'),
    path('refresh', views.refresh_all, name='refresh'),
    path('friends', views.users, name='users'),
    path('add', views.add_friend, name='add_friend'),
    path('add2', views.add2, name='add2'),

    path('new', views.new, name='new'),
    path('graphs', views.graphs, name='graphs'),
    path('search', views.search, name='search'),

    path('media', views.download, name='download'),
    path('logout', views.logout_view, name='logout'),

    path('artist/<str:artist>/', views.artist, name='artist'),
    path('album/<str:album>/', views.album, name='album'),
    path('<str:username>$', views.details, name='details'),
    path('<str:username>/recent/', views.recent, name='recent'),
    path('<str:username>/top/', views.top, name='top'),
    path('<str:username>/saved/', views.saved, name='saved'),
    path('<str:username>/following/', views.following, name='following'),
    path('<str:username>/<str:genre>/', views.genres, name='genres'),
    # url('static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_URL}),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)