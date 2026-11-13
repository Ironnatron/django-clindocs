from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import (
    ClinicalStudyViewSet,
    DepartmentListAPIView,
    DesignationListAPIView,
    LoginAPIView,
    LogoutAPIView,
    PasswordResetAPIView,
    PasswordResetConfirmAPIView,
    PermissionListAPIView,
    OrganizationListAPIView,
    ProfileAPIView,
    RoleViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")
router.register("studies", ClinicalStudyViewSet, basename="study")

urlpatterns = [
    path("auth/login/", LoginAPIView.as_view(), name="api-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="api-logout"),
    path("auth/profile/", ProfileAPIView.as_view(), name="api-profile"),
    path("auth/password-reset/", PasswordResetAPIView.as_view(), name="api-password-reset"),
    path("auth/password-reset-confirm/", PasswordResetConfirmAPIView.as_view(), name="api-password-reset-confirm"),
    path("permissions/", PermissionListAPIView.as_view(), name="api-permissions"),
    path("departments/", DepartmentListAPIView.as_view(), name="api-departments"),
    path("designations/", DesignationListAPIView.as_view(), name="api-designations"),
    path("organizations/", OrganizationListAPIView.as_view(), name="api-organizations"),
    path("", include(router.urls)),
]