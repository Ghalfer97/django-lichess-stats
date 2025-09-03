from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/',views.about,name='about'),
    path('lichess/',views.lichess_view,name='lichess'),
    path('lichess_results/',views.lichess_games,name='lichess_games'),
]