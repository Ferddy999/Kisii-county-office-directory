from django.urls import path

from . import views

urlpatterns = [
    path("", views.OfficeList.as_view(), name="office_list"),
    path("add/", views.OfficeCreate.as_view(), name="office_add"),
    path("<int:pk>/edit/", views.OfficeUpdate.as_view(), name="office_edit"),
    path("<int:pk>/delete/", views.OfficeDelete.as_view(), name="office_delete"),
]
