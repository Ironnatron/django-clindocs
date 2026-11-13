from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import AuditLog, ClinicalStudy, CustomUser, Department, Designation, Organization, Role, StudyMember


class ClinDocsUserCreationForm(UserCreationForm):
	class Meta(UserCreationForm.Meta):
		model = CustomUser
		fields = ("email", "employee_id", "first_name", "last_name")


class ClinDocsUserChangeForm(UserChangeForm):
	class Meta:
		model = CustomUser
		fields = "__all__"


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
	form = ClinDocsUserChangeForm
	add_form = ClinDocsUserCreationForm
	ordering = ("email",)
	list_display = ("email", "employee_id", "first_name", "last_name", "role", "is_active")
	search_fields = ("email", "employee_id", "first_name", "last_name")
	fieldsets = (
		(None, {"fields": ("email", "password")}),
		("Personal information", {"fields": ("employee_id", "first_name", "last_name", "phone_number", "profile_image")}),
		("Professional information", {"fields": ("department", "designation", "organization", "reporting_manager")}),
		("Access", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
		("Dates", {"fields": ("last_login", "date_joined")}),
	)
	add_fieldsets = (
		(None, {"classes": ("wide",), "fields": ("email", "employee_id", "first_name", "last_name", "password1", "password2")}),
	)
	readonly_fields = ("last_login", "date_joined")


@admin.register(ClinicalStudy)
class ClinicalStudyAdmin(admin.ModelAdmin):
	list_display = ("study_id", "protocol_number", "title", "study_manager", "status", "is_archived")
	list_filter = ("status", "clinical_phase", "is_archived")
	search_fields = ("study_id", "protocol_number", "title", "sponsor_name")
	readonly_fields = ("study_id", "created_by", "created_at", "updated_at")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
	list_display = ("name", "is_system", "is_active", "created_at")
	list_filter = ("is_system", "is_active")
	search_fields = ("name",)
	filter_horizontal = ("permissions",)


@admin.register(StudyMember)
class StudyMemberAdmin(admin.ModelAdmin):
	list_display = ("study", "user", "assigned_role", "assigned_by", "assigned_at", "is_active")
	list_filter = ("is_active", "assigned_role")
	search_fields = ("study__study_id", "user__email", "user__employee_id")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ("timestamp", "user", "action", "module", "object_id")
	list_filter = ("module", "action")
	search_fields = ("description", "object_id", "user__email")
	readonly_fields = ("user", "action", "module", "object_id", "description", "timestamp", "ip_address")


admin.site.register((Department, Designation, Organization))
