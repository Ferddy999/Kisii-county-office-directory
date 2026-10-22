from django.urls import path

from . import views

urlpatterns = [
    path("", views.DepartmentList.as_view(), name="department_list"),
    path("add/", views.DepartmentCreate.as_view(), name="department_add"),
    path("<int:pk>/edit/", views.DepartmentUpdate.as_view(), name="department_edit"),
    path("<int:pk>/delete/", views.DepartmentDelete.as_view(), name="department_delete"),
    path("directorates/", views.DirectorateList.as_view(), name="directorate_list"),
    path("directorates/add/", views.DirectorateCreate.as_view(), name="directorate_add"),
    path("directorates/<int:pk>/edit/", views.DirectorateUpdate.as_view(), name="directorate_edit"),
    path("directorates/<int:pk>/delete/", views.DirectorateDelete.as_view(), name="directorate_delete"),
]
