from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework.test import APIClient

from .models import ClinicalStudy, Role, StudyMember

User = get_user_model()


class ClinDocsAPITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.admin_role = Role.objects.get(name="System Administrator")
		self.admin = User.objects.create_user(
			email="admin@example.com",
			password="StrongAdminPassword123!",
			employee_id="EMP-001",
			first_name="Casey",
			last_name="Admin",
			role=self.admin_role,
		)

	def create_role(self, name, *codenames):
		role, _ = Role.objects.get_or_create(name=name)
		role.permissions.set(Permission.objects.filter(content_type__app_label="polls", codename__in=codenames))
		return role

	def create_user(self, email, employee_id, role, is_active=True):
		return User.objects.create_user(
			email=email,
			password="StrongUserPassword123!",
			employee_id=employee_id,
			first_name="Taylor",
			last_name="Researcher",
			role=role,
			is_active=is_active,
		)

	def create_study(self, created_by, manager=None):
		return ClinicalStudy.objects.create(
			protocol_number=f"PROTO-{ClinicalStudy.objects.count() + 1}",
			title="A clinical study",
			sponsor_name="Example Sponsor",
			created_by=created_by,
			study_manager=manager,
		)

	def test_email_login_and_inactive_account(self):
		response = self.client.post(
			"/api/auth/login/",
			{"email": "ADMIN@example.com", "password": "StrongAdminPassword123!"},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["user"]["email"], self.admin.email)

		inactive = self.create_user("inactive@example.com", "EMP-002", self.admin_role, is_active=False)
		response = self.client.post(
			"/api/auth/login/",
			{"email": inactive.email, "password": "StrongUserPassword123!"},
			format="json",
		)
		self.assertEqual(response.status_code, 400)
		self.assertIn("inactive", response.data["detail"].lower())

	def test_study_access_is_scoped_to_active_membership(self):
		viewer_role = self.create_role("Clinical Research Associate (CRA)", "view_clinicalstudy")
		viewer = self.create_user("viewer@example.com", "EMP-003", viewer_role)
		study = self.create_study(self.admin)

		self.client.force_authenticate(viewer)
		self.assertEqual(self.client.get(f"/api/studies/{study.pk}/").status_code, 404)
		self.assertEqual(self.client.get("/api/studies/").data, [])

		StudyMember.objects.create(study=study, user=viewer, assigned_by=self.admin)
		self.assertEqual(self.client.get(f"/api/studies/{study.pk}/").status_code, 200)
		StudyMember.objects.filter(study=study, user=viewer).update(is_active=False)
		self.assertEqual(self.client.get(f"/api/studies/{study.pk}/").status_code, 404)

	def test_only_roles_with_study_permission_can_create_studies(self):
		read_only_role = self.create_role("Read Only", "view_clinicalstudy")
		reader = self.create_user("reader@example.com", "EMP-004", read_only_role)
		self.client.force_authenticate(reader)
		response = self.client.post(
			"/api/studies/",
			{"protocol_number": "PROTO-READ", "title": "Not allowed", "sponsor_name": "Sponsor"},
			format="json",
		)
		self.assertEqual(response.status_code, 403)

	def test_study_member_assignment_rejects_duplicates(self):
		manager_role = self.create_role(
			"Study Manager",
			"view_clinicalstudy",
			"add_clinicalstudy",
			"change_clinicalstudy",
			"assign_study_members",
		)
		manager = self.create_user("manager@example.com", "EMP-005", manager_role)
		member = self.create_user("member@example.com", "EMP-006", manager_role)
		study = self.create_study(self.admin, manager)
		self.client.force_authenticate(manager)

		first = self.client.post(f"/api/studies/{study.pk}/members/", {"user_id": str(member.pk)}, format="json")
		duplicate = self.client.post(f"/api/studies/{study.pk}/members/", {"user_id": str(member.pk)}, format="json")
		self.assertEqual(first.status_code, 201)
		self.assertEqual(duplicate.status_code, 409)
		removed = self.client.delete(f"/api/studies/{study.pk}/members/{member.pk}/")
		self.assertEqual(removed.status_code, 204)
		self.assertFalse(StudyMember.objects.get(study=study, user=member).is_active)

	def test_member_assignment_is_limited_to_authorized_study_scope(self):
		manager_role = self.create_role("Scoped Study Manager", "view_clinicalstudy", "assign_study_members")
		manager = self.create_user("scoped-manager@example.com", "EMP-009", manager_role)
		study = self.create_study(self.admin)
		self.client.force_authenticate(manager)
		response = self.client.post(
			f"/api/studies/{study.pk}/members/",
			{"user_id": str(manager.pk)},
			format="json",
		)
		self.assertEqual(response.status_code, 404)

	def test_final_system_administrator_cannot_be_deactivated(self):
		self.client.force_authenticate(self.admin)
		response = self.client.post(f"/api/users/{self.admin.pk}/deactivate/")
		self.assertEqual(response.status_code, 400)
		self.admin.refresh_from_db()
		self.assertTrue(self.admin.is_active)

	def test_unauthenticated_api_requests_are_rejected(self):
		response = self.client.get("/api/studies/")
		self.assertIn(response.status_code, (401, 403))

	def test_management_endpoints_require_and_allow_administrator_access(self):
		self.client.force_authenticate(self.admin)
		self.assertEqual(self.client.get("/api/users/").status_code, 200)
		self.assertEqual(self.client.get("/api/roles/").status_code, 200)
		self.assertEqual(self.client.get("/api/permissions/").status_code, 200)
		self.assertEqual(self.client.get("/api/departments/").status_code, 200)
		self.assertEqual(self.client.get("/api/designations/").status_code, 200)
		self.assertEqual(self.client.get("/api/organizations/").status_code, 200)

	def test_authenticated_pages_render(self):
		study = self.create_study(self.admin)
		self.client.force_login(self.admin)
		urls = [
			"/",
			"/studies/",
			f"/studies/{study.pk}/",
			"/users/",
			"/roles/",
			"/profile/",
		]
		for url in urls:
			with self.subTest(url=url):
				self.assertEqual(self.client.get(url).status_code, 200)

	def test_password_reset_request_does_not_disclose_account_existence(self):
		existing = self.client.post("/api/auth/password-reset/", {"email": self.admin.email}, format="json")
		unknown = self.client.post("/api/auth/password-reset/", {"email": "unknown@example.com"}, format="json")
		self.assertEqual(existing.status_code, 200)
		self.assertEqual(existing.data, unknown.data)

	def test_user_manager_without_role_permission_cannot_assign_roles(self):
		user_admin_role = self.create_role("User Administrator", "manage_users")
		user_admin = self.create_user("user-admin@example.com", "EMP-007", user_admin_role)
		target_role = self.create_role("Restricted Reviewer", "view_clinicalstudy")
		self.client.force_authenticate(user_admin)
		response = self.client.post(
			"/api/users/",
			{
				"email": "new-user@example.com",
				"employee_id": "EMP-008",
				"first_name": "New",
				"last_name": "User",
				"role_id": str(target_role.pk),
			},
			format="json",
		)
		self.assertEqual(response.status_code, 400)
		self.assertIn("role_id", response.data)

	def test_system_administrator_role_permissions_are_immutable(self):
		self.client.force_authenticate(self.admin)
		response = self.client.patch(
			f"/api/roles/{self.admin_role.pk}/",
			{"permissions": []},
			format="json",
		)
		self.assertEqual(response.status_code, 400)

	def test_studies_cannot_be_permanently_deleted(self):
		study = self.create_study(self.admin)
		self.client.force_authenticate(self.admin)
		response = self.client.delete(f"/api/studies/{study.pk}/")
		self.assertEqual(response.status_code, 405)
		self.assertTrue(ClinicalStudy.objects.filter(pk=study.pk).exists())
