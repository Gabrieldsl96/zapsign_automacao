from django.urls import path

from . import views

app_name = "webhooks"

urlpatterns = [
    path("receive/", views.receive_webhook, name="receive"),
]
