from django.urls import path

from . import views

urlpatterns = [
    path("", views.StaffList.as_view(), name="staff_list"),
    path("add/", views.StaffCreate.as_view(), name="staff_add"),
    path("<int:pk>/edit/", views.StaffUpdate.as_view(), name="staff_edit"),
    path("<int:pk>/delete/", views.StaffDelete.as_view(), name="staff_delete"),
]
