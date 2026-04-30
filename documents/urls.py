from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.index, name="index"),
    path("fluxo/novo/", views.create_flow, name="create_flow"),
    path("fluxo/<int:pk>/", views.flow_detail, name="flow_detail"),
]
