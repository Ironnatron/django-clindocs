import binascii

from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import Permission
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter

from .api_permissions import CanManageRoles, CanManageUsers, StudyAccessPermission, is_system_administrator
from .models import AuditLog, ClinicalStudy, Department, Designation, Organization, Role, StudyMember
from .serializers import ClinicalStudySerializer, PermissionSerializer, RoleSerializer, StudyMemberSerializer, UserSerializer, UserSummarySerializer

User = get_user_model()


def record_audit(request, action_name, module, instance, description):
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action_name,
        module=module,
        object_id=str(instance.pk) if instance else "",
        description=description,
        ip_address=request.META.get("REMOTE_ADDR"),
    )


@method_decorator(csrf_protect, name="dispatch")
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data if hasattr(request.data, "get") else {}
        email = payload.get("email", "")
        password = payload.get("password", "")
        if not isinstance(email, str) or not isinstance(password, str):
            return Response({"detail": "Email or password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        email = email.strip().lower()
        user = authenticate(request, username=email, password=password)
        if not user:
            inactive = User.objects.filter(email__iexact=email, is_active=False).exists()
            message = "This account is inactive. Contact your administrator." if inactive else "Email or password is incorrect."
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response({"user": UserSerializer(user, context={"request": request}).data})


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        form = PasswordResetForm({"email": request.data.get("email", "")})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=None,
                subject_template_name="polls/password_reset_subject.txt",
                email_template_name="polls/password_reset_email.txt",
            )
        return Response({"detail": "If an active account uses that email, reset instructions have been sent."})


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            user_id = urlsafe_base64_decode(request.data.get("uid", "")).decode()
            user = User.objects.get(pk=user_id, is_active=True)
        except (ValueError, TypeError, UnicodeDecodeError, binascii.Error, ValidationError, User.DoesNotExist):
            return Response({"detail": "This password reset link is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        token = request.data.get("token", "")
        if not default_token_generator.check_token(user, token):
            return Response({"detail": "This password reset link is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        form = SetPasswordForm(user, {"new_password1": request.data.get("password1"), "new_password2": request.data.get("password2")})
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        form.save()
        return Response({"detail": "Your password has been updated."})


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [CanManageUsers]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["employee_id", "first_name", "last_name", "email", "department__name", "role__name"]
    ordering_fields = ["last_name", "email", "date_joined"]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        queryset = User.objects.select_related("role", "department", "designation", "organization", "reporting_manager")
        role_id = self.request.query_params.get("role")
        status_filter = self.request.query_params.get("status")
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        if status_filter in {"active", "inactive"}:
            queryset = queryset.filter(is_active=(status_filter == "active"))
        return queryset

    def perform_create(self, serializer):
        user = serializer.save()
        record_audit(self.request, "create", "users", user, f"Created account for {user.email}.")

    def _protect_last_administrator(self, target, updates):
        target_is_admin = is_system_administrator(target)
        new_role = updates.get("role", target.role)
        new_active = updates.get("is_active", target.is_active)
        remains_admin = bool(new_active and new_role and new_role.is_active and new_role.name.casefold() == "system administrator")
        if target.is_superuser:
            remains_admin = new_active and updates.get("is_superuser", target.is_superuser)
        if target_is_admin and not remains_admin:
            active_admins = User.objects.filter(is_active=True).filter(
                models_q_admin()
            ).exclude(pk=target.pk).exists()
            if not active_admins:
                return Response({"detail": "The final active System Administrator cannot be deactivated or reassigned."}, status=400)
        return None

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        blocked = self._protect_last_administrator(instance, serializer.validated_data)
        if blocked:
            return blocked
        self.perform_update(serializer)
        record_audit(request, "update", "users", instance, f"Updated account for {instance.email}.")
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        blocked = self._protect_last_administrator(user, {"is_active": False})
        if blocked:
            return blocked
        user.is_active = False
        user.save(update_fields=["is_active"])
        record_audit(request, "deactivate", "users", user, f"Deactivated account for {user.email}.")
        return Response({"detail": "User deactivated."})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=["is_active"])
        record_audit(request, "activate", "users", user, f"Activated account for {user.email}.")
        return Response({"detail": "User activated."})

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        user = self.get_object()
        form = PasswordResetForm({"email": user.email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                subject_template_name="polls/password_reset_subject.txt",
                email_template_name="polls/password_reset_email.txt",
            )
        record_audit(request, "reset_password", "users", user, f"Sent password reset instructions to {user.email}.")
        return Response({"detail": "Password reset instructions sent."})


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [CanManageRoles]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        return Role.objects.prefetch_related("permissions", "users")

    def perform_create(self, serializer):
        role = serializer.save()
        record_audit(self.request, "create", "roles", role, f"Created role {role.name}.")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop("partial", False))
        serializer.is_valid(raise_exception=True)
        if instance.is_system:
            if serializer.validated_data.get("name", instance.name) != instance.name:
                return Response({"detail": "The System Administrator role name cannot be changed."}, status=400)
            if "permissions" in serializer.validated_data:
                return Response({"detail": "Permissions for built-in system roles cannot be changed."}, status=400)
            if not serializer.validated_data.get("is_active", instance.is_active):
                return Response({"detail": "Built-in system roles cannot be deactivated."}, status=400)
        self.perform_update(serializer)
        record_audit(request, "update", "roles", instance, f"Updated role {instance.name}.")
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def users(self, request, pk=None):
        role = self.get_object()
        return Response(UserSerializer(role.users.select_related("role"), many=True, context={"request": request}).data)


class PermissionListAPIView(APIView):
    permission_classes = [CanManageRoles]

    def get(self, request):
        permissions = Permission.objects.filter(content_type__app_label="polls").select_related("content_type").order_by("content_type__model", "name")
        return Response(PermissionSerializer(permissions, many=True).data)


class DepartmentListAPIView(APIView):
    permission_classes = [CanManageUsers]

    def get(self, request):
        return Response(list(Department.objects.filter(is_active=True).values("id", "name")))


class DesignationListAPIView(APIView):
    permission_classes = [CanManageUsers]

    def get(self, request):
        return Response(list(Designation.objects.filter(is_active=True).values("id", "name")))


class OrganizationListAPIView(APIView):
    permission_classes = [CanManageUsers]

    def get(self, request):
        return Response(list(Organization.objects.filter(is_active=True).values("id", "name")))


class ClinicalStudyViewSet(viewsets.ModelViewSet):
    serializer_class = ClinicalStudySerializer
    permission_classes = [StudyAccessPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["study_id", "protocol_number", "title", "sponsor_name", "therapeutic_area"]
    ordering_fields = ["title", "start_date", "created_at", "status"]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = ClinicalStudy.objects.select_related("study_manager", "created_by").prefetch_related("memberships__user", "memberships__assigned_role")
        user = self.request.user
        if not user.has_perm("polls.view_all_clinicalstudies"):
            queryset = queryset.filter(
                Q(study_manager=user) | Q(created_by=user) | Q(memberships__user=user, memberships__is_active=True)
            )
        queryset = queryset.distinct()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if self.request.query_params.get("archived") != "true":
            queryset = queryset.filter(is_archived=False)
        return queryset

    @action(detail=False, methods=["get"])
    def candidates(self, request):
        candidates = User.objects.filter(is_active=True).select_related("role").order_by("last_name", "first_name")
        return Response(UserSummarySerializer(candidates, many=True).data)

    def perform_create(self, serializer):
        study = serializer.save(created_by=self.request.user)
        if study.study_manager:
            StudyMember.objects.get_or_create(
                study=study,
                user=study.study_manager,
                is_active=True,
                defaults={"assigned_by": self.request.user, "assigned_role": study.study_manager.role},
            )
        record_audit(self.request, "create", "studies", study, f"Created study {study.study_id}: {study.title}.")

    def perform_update(self, serializer):
        previous_manager_id = serializer.instance.study_manager_id
        study = serializer.save()
        if study.study_manager and study.study_manager_id != previous_manager_id:
            membership, created = StudyMember.objects.get_or_create(
                study=study,
                user=study.study_manager,
                is_active=True,
                defaults={"assigned_by": self.request.user, "assigned_role": study.study_manager.role},
            )
            if created:
                record_audit(self.request, "assign_member", "studies", study, f"Assigned study manager {membership.user.email} to {study.study_id}.")
        record_audit(self.request, "update", "studies", study, f"Updated study {study.study_id}.")

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Clinical studies cannot be permanently deleted. Archive the study instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    def members(self, request, pk=None):
        study = self.get_object()
        serializer = StudyMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                membership = StudyMember.objects.create(
                    study=study,
                    user=serializer.validated_data["user"],
                    assigned_role=serializer.validated_data.get("assigned_role") or (
                        serializer.validated_data["user"].role
                        if serializer.validated_data["user"].role and serializer.validated_data["user"].role.is_active
                        else None
                    ),
                    assigned_by=request.user,
                )
        except IntegrityError:
            return Response({"detail": "This user is already assigned to the study."}, status=status.HTTP_409_CONFLICT)
        record_audit(request, "assign_member", "studies", study, f"Assigned {membership.user.email} to {study.study_id}.")
        return Response(StudyMemberSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"members/(?P<user_id>[^/.]+)")
    def remove_member(self, request, pk=None, user_id=None):
        study = self.get_object()
        membership = StudyMember.objects.filter(study=study, user_id=user_id, is_active=True).first()
        if not membership:
            return Response({"detail": "Active study assignment not found."}, status=status.HTTP_404_NOT_FOUND)
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        record_audit(request, "remove_member", "studies", study, f"Removed {membership.user.email} from {study.study_id}.")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        study = self.get_object()
        study.is_archived = True
        study.status = ClinicalStudy.Status.ARCHIVED
        study.save(update_fields=["is_archived", "status", "updated_at"])
        record_audit(request, "archive", "studies", study, f"Archived study {study.study_id}.")
        return Response(ClinicalStudySerializer(study, context={"request": request}).data)


def models_q_admin():
    from django.db.models import Q

    return Q(is_superuser=True) | Q(role__name__iexact="System Administrator", role__is_active=True)