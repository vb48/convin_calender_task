from django.urls import path, re_path
from . import views


urlpatterns = [
    path('v1/calendar/init/',views.init, name='init'),
    path('v1/calendar/redirect/',views.redirect, name='redirect'),
] 