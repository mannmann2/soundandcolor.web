from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [

	# path('', views.IndexView.as_view(), name='index'),
 #    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
 #    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
 #    path('<int:question_id>/vote/', views.vote, name='vote'),

 	path('login', views.home, name='home'),
    path('', views.users, name='users'),
    path('refresh', views.refresh_all, name='refresh'),
    path('<str:username>/', views.details, name='details'),
    path('<str:username>/recent/', views.recent, name='recent'),
    path('<str:username>/top/', views.top, name='top'),
    path('<str:username>/following/', views.following, name='following'),
    path('<str:username>/saved/', views.saved, name='saved'),
    path('new', views.new, name='new'),
    path('<str:username>/genres/', views.genres, name='genres'),
    path('artist/<str:artist>/', views.artist, name='artist'),
    path('album/<str:album>/', views.album, name='album'),
    # path('album/<str:album>/<str:track>', views.album, name='album')

]