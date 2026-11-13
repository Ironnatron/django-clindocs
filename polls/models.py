import secrets
import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Permission
from django.db import models
from django.utils import timezone


class Department(models.Model):
	name = models.CharField(max_length=120, unique=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name


class Designation(models.Model):
	name = models.CharField(max_length=120, unique=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name


class Organization(models.Model):
	name = models.CharField(max_length=180, unique=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name


class Role(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True)
	permissions = models.ManyToManyField(Permission, blank=True, related_name="clindocs_roles")
	is_active = models.BooleanField(default=True)
	is_system = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]
		permissions = [("manage_roles", "Can manage roles")]

	def __str__(self):
		return self.name


class CustomUserManager(BaseUserManager):
	use_in_migrations = True

	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError("An email address is required")
		user = self.model(email=self.normalize_email(email), **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", True)
		extra_fields.setdefault("is_superuser", True)
		extra_fields.setdefault("is_active", True)
		if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
			raise ValueError("A superuser must have staff and superuser status")
		return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	employee_id = models.CharField(max_length=40, unique=True)
	email = models.EmailField(unique=True)
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	phone_number = models.CharField(max_length=30, blank=True)
	department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
	designation = models.ForeignKey(Designation, null=True, blank=True, on_delete=models.SET_NULL)
	organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
	reporting_manager = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="direct_reports")
	profile_image = models.ImageField(upload_to="profiles/", blank=True)
	role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	date_joined = models.DateTimeField(default=timezone.now)

	objects = CustomUserManager()

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = ["employee_id", "first_name", "last_name"]

	class Meta:
		ordering = ["last_name", "first_name"]
		permissions = [("manage_users", "Can manage users")]

	def __str__(self):
		return self.get_full_name() or self.email

	def get_full_name(self):
		return f"{self.first_name} {self.last_name}".strip()

	def get_short_name(self):
		return self.first_name

	def has_perm(self, perm, obj=None):
		if not self.is_active:
			return False
		if super().has_perm(perm, obj):
			return True
		if not self.role_id or not self.role.is_active:
			return False
		app_label, codename = perm.split(".", 1)
		return self.role.permissions.filter(
			content_type__app_label=app_label,
			codename=codename,
		).exists()

	def has_module_perms(self, app_label):
		if not self.is_active:
			return False
		if super().has_module_perms(app_label):
			return True
		return bool(self.role_id and self.role.is_active and self.role.permissions.filter(content_type__app_label=app_label).exists())


class ClinicalStudy(models.Model):
	class Status(models.TextChoices):
		DRAFT = "draft", "Draft"
		PLANNING = "planning", "Planning"
		ACTIVE = "active", "Active"
		ON_HOLD = "on_hold", "On Hold"
		COMPLETED = "completed", "Completed"
		ARCHIVED = "archived", "Archived"

	class Phase(models.TextChoices):
		PHASE_I = "I", "Phase I"
		PHASE_II = "II", "Phase II"
		PHASE_III = "III", "Phase III"
		PHASE_IV = "IV", "Phase IV"

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	study_id = models.CharField(max_length=32, unique=True, editable=False)
	protocol_number = models.CharField(max_length=100, unique=True)
	title = models.CharField(max_length=240)
	description = models.TextField(blank=True)
	study_type = models.CharField(max_length=100, blank=True)
	therapeutic_area = models.CharField(max_length=120, blank=True)
	sponsor_name = models.CharField(max_length=180)
	sponsor_contact = models.CharField(max_length=160, blank=True)
	sponsor_email = models.EmailField(blank=True)
	cro_name = models.CharField(max_length=180, blank=True)
	clinical_phase = models.CharField(max_length=3, choices=Phase.choices, blank=True)
	study_design = models.CharField(max_length=180, blank=True)
	indication = models.CharField(max_length=180, blank=True)
	planned_enrollment = models.PositiveIntegerField(default=0)
	number_of_sites = models.PositiveIntegerField(default=0)
	start_date = models.DateField(null=True, blank=True)
	estimated_completion_date = models.DateField(null=True, blank=True)
	actual_completion_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
	study_manager = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_studies")
	created_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="created_studies")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_archived = models.BooleanField(default=False)

	class Meta:
		ordering = ["-updated_at"]
		permissions = [
			("assign_study_members", "Can assign study members"),
			("export_clinicalstudy", "Can export clinical studies"),
			("view_all_clinicalstudies", "Can view all clinical studies"),
		]
		indexes = [models.Index(fields=["status", "is_archived"])]

	def save(self, *args, **kwargs):
		if not self.study_id:
			self.study_id = f"CD-{uuid.uuid4().hex[:8].upper()}"
		if self.status == self.Status.ARCHIVED:
			self.is_archived = True
		super().save(*args, **kwargs)

	def clean(self):
		from django.core.exceptions import ValidationError

		if self.start_date and self.estimated_completion_date and self.estimated_completion_date < self.start_date:
			raise ValidationError({"estimated_completion_date": "Completion date cannot be before the start date."})

	def __str__(self):
		return f"{self.study_id} - {self.title}"


class StudyMember(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	study = models.ForeignKey(ClinicalStudy, on_delete=models.CASCADE, related_name="memberships")
	user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="study_memberships")
	assigned_role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
	assigned_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="study_assignments_made")
	assigned_at = models.DateTimeField(auto_now_add=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ["user__last_name", "user__first_name"]
		constraints = [
			models.UniqueConstraint(fields=["study", "user"], condition=models.Q(is_active=True), name="unique_active_study_member"),
		]


class AuditLog(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
	action = models.CharField(max_length=40)
	module = models.CharField(max_length=60)
	object_id = models.CharField(max_length=64, blank=True)
	description = models.TextField()
	timestamp = models.DateTimeField(auto_now_add=True)
	ip_address = models.GenericIPAddressField(null=True, blank=True)

	class Meta:
		ordering = ["-timestamp"]
		indexes = [models.Index(fields=["module", "timestamp"])]
