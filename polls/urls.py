from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('password-reset/', views.password_reset_page, name='password-reset'),
    path('password-reset/confirm/', views.password_reset_confirm_page, name='password-reset-confirm'),
    path('studies/', views.studies_page, name='studies'),
    path('studies/<uuid:study_id>/', views.study_detail_page, name='study-detail'),
    path('profile/', views.profile_page, name='profile'),
    path('users/', views.users_page, name='users'),
    path('roles/', views.roles_page, name='roles'),
]