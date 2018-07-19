# from django.urls import path

from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from . import views

# from django.conf import settings
# from django.conf.urls.static import static

app_name = 'stats'
urlpatterns = [

    path('', views.home, name='home'),
    path('auth', views.auth, name='auth'),
    path('refresh', views.refresh_all, name='refresh'),
    path('friends', views.users, name='users'),
    path('add', views.add_friend, name='add'),
    path('viz', views.viz, name='viz'),
    path('new', views.new, name='new'),
    path('graphs', views.graphs, name='graphs'),
    path('search', views.search, name='search'),
    path(r'<str:username>$', views.details, name='details'),
    path('<str:username>/recent/', views.recent, name='recent'),
    path('<str:username>/top/', views.top, name='top'),
    path('<str:username>/saved/', views.saved, name='saved'),
    path('<str:username>/following/', views.following, name='following'),
    path('<str:username>/genres/', views.genres, name='genres'),
    path('artist/<str:artist>/', views.artist, name='artist'),
    path('album/<str:album>/', views.album, name='album'),
    path('logout', views.logout_view, name='logout'),
    # path('ref', views.ref, name='ref'),
    # path('config.json', views.ff, name='config'),
    # path('login', views.login_page, name='login'),
    # path('login2', views.login_view, name='login2'),
    # path('register', views.signup, name='register'),
]
# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)