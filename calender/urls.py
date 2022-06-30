from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('', index.as_view(), name="index"),
    path('rest/v1/calendar/init/',GoogleCalendarInitView.as_view(),name='google-login'),
    path('rest/v1/calendar/redirect/',GoogleCalendarRedirectView.as_view(),name='calender_view'),
    path('revoke',revoke.as_view(),name='revoke'),
]
