from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_system_administrator(user):
    return bool(
        user.is_authenticated
        and user.is_active
        and (user.is_superuser or (user.role_id and user.role.is_active and user.role.name.casefold() == "system administrator"))
    )


class CanManageUsers(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("polls.manage_users")


class CanManageRoles(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("polls.manage_roles")


class StudyAccessPermission(BasePermission):
    def has_study_scope(self, user, study):
        return bool(
            user.has_perm("polls.view_all_clinicalstudies")
            or study.study_manager_id == user.pk
            or study.created_by_id == user.pk
            or study.memberships.filter(user=user, is_active=True).exists()
        )

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if getattr(view, "action", "") == "candidates":
            return request.user.has_perm("polls.assign_study_members")
        if request.method in SAFE_METHODS:
            return True
        if getattr(view, "action", "") in {"members", "remove_member"}:
            return request.user.has_perm("polls.assign_study_members")
        if getattr(view, "action", "") == "create":
            return request.user.has_perm("polls.add_clinicalstudy")
        if getattr(view, "action", "") == "destroy":
            return request.user.has_perm("polls.delete_clinicalstudy")
        return request.user.has_perm("polls.change_clinicalstudy")

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            if getattr(view, "action", "") in {"members", "remove_member"}:
                return request.user.has_perm("polls.assign_study_members") and self.has_study_scope(request.user, obj)
            if getattr(view, "action", "") == "destroy":
                return request.user.has_perm("polls.delete_clinicalstudy") and self.has_study_scope(request.user, obj)
            return request.user.has_perm("polls.change_clinicalstudy") and self.has_study_scope(request.user, obj)
        if request.user.has_perm("polls.view_all_clinicalstudies"):
            return True
        return self.has_study_scope(request.user, obj)