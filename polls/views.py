from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .api_permissions import is_system_administrator
from .models import ClinicalStudy, CustomUser, Role


@ensure_csrf_cookie
def login_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "polls/login.html")


@ensure_csrf_cookie
def password_reset_page(request):
    return render(request, "polls/password_reset.html")


@ensure_csrf_cookie
def password_reset_confirm_page(request):
    return render(request, "polls/password_reset_confirm.html")


@require_POST
def logout_page(request):
    logout(request)
    return redirect("login")


@login_required
@ensure_csrf_cookie
def dashboard(request):
    studies = ClinicalStudy.objects.all()
    if not request.user.has_perm("polls.view_all_clinicalstudies"):
        studies = studies.filter(
            Q(study_manager=request.user) | Q(created_by=request.user) | Q(memberships__user=request.user, memberships__is_active=True)
        ).distinct()
    context = {
        "total_studies": studies.filter(is_archived=False).count(),
        "active_studies": studies.filter(status=ClinicalStudy.Status.ACTIVE, is_archived=False).count(),
        "completed_studies": studies.filter(status=ClinicalStudy.Status.COMPLETED).count(),
        "can_manage_users": request.user.has_perm("polls.manage_users"),
        "can_manage_roles": request.user.has_perm("polls.manage_roles"),
        "is_system_admin": is_system_administrator(request.user),
    }
    if context["can_manage_users"]:
        context["total_users"] = CustomUser.objects.count()
    return render(request, "polls/dashboard.html", context)


@login_required
@ensure_csrf_cookie
def studies_page(request):
    return render(request, "polls/studies.html")


@login_required
@ensure_csrf_cookie
def profile_page(request):
    return render(request, "polls/profile.html")


@login_required
@ensure_csrf_cookie
def study_detail_page(request, study_id):
    return render(request, "polls/study_detail.html", {"study_id": study_id})


@login_required
@ensure_csrf_cookie
def users_page(request):
    if not request.user.has_perm("polls.manage_users"):
        return HttpResponseForbidden("You do not have permission to manage users.")
    return render(request, "polls/users.html")


@login_required
@ensure_csrf_cookie
def roles_page(request):
    if not request.user.has_perm("polls.manage_roles"):
        return HttpResponseForbidden("You do not have permission to manage roles.")
    return render(request, "polls/roles.html")