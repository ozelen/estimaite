from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    # Project URLs
    path("", views.project_list, name="project_list"),
    path("create/", views.project_create, name="project_create"),
    path("<int:pk>/", views.project_detail, name="project_detail"),
    path("<int:pk>/edit/", views.project_update, name="project_update"),
    path("<int:pk>/delete/", views.project_delete, name="project_delete"),
    # Feature URLs
    path("features/", views.feature_list, name="feature_list"),
    path("features/create/", views.feature_create, name="feature_create"),
    path(
        "<int:project_pk>/features/create/",
        views.feature_create,
        name="feature_create_for_project",
    ),
    path("features/<int:pk>/", views.feature_detail, name="feature_detail"),
    path("features/<int:pk>/edit/", views.feature_update, name="feature_update"),
    path("features/<int:pk>/delete/", views.feature_delete, name="feature_delete"),
]
