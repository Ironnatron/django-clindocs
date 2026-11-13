# ClinDocs Application Guide

## 1. Purpose and Scope

ClinDocs is the Phase 1 foundation for a clinical study and user-management application. It provides authenticated access, role-based permissions, clinical study records, study teams, account administration, and audit entries. The application is intended to establish the identity and study-access foundation for later document, TMF, review, approval, reporting, and notification phases.

This guide describes what the current code does. A visual label or placeholder is not evidence that a future module is implemented. In particular, Settings, global search, notifications, document storage, TMF, review/approval, and study reports are not functional features in this phase.

## 2. Technology and Architecture

- Backend: Python, Django, Django REST Framework, Django ORM, and Django session authentication.
- Database: SQLite locally by default. PostgreSQL can be selected using environment variables.
- Frontend: server-rendered Django templates, HTML, CSS, jQuery, and AJAX.
- UI libraries: Bootstrap 4.6.2, DevExtreme 22.2.4, Font Awesome 5, ExcelJS, and FileSaver are loaded from CDNs.
- Authentication: Django session cookies with CSRF protection. This project does not issue API tokens.

The browser loads a Django page, then jQuery calls the protected REST API. DRF validates request data with serializers, permission classes authorize the operation, and Django models persist the resulting records.

## 3. Starting and Signing In

Run the following commands from the project directory:

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. The superuser command is interactive: enter an email address, employee ID, first name, last name, and password. Run it in a terminal that accepts prompts; do not use `--noinput` unless supplying all required values through an automated setup process.

The login screen accepts email and password, validates the email format in the browser, toggles password visibility, displays server-side credential/inactive-account errors, and shows a loading state during authentication. "Remember my email" stores only the email address in browser local storage; it does not store a password or extend the session. Successful login opens the dashboard.

The Forgot Password flow accepts an email and always returns the same confirmation message to avoid disclosing whether an account exists. If an active account matches, Django sends a single-use token link. The local email backend prints the message in the server console. The reset page requires matching passwords and applies Django's configured password validators.

Logout is a CSRF-protected POST from the profile menu. The browser session is cleared and the user is returned to the login page. Inactive users are rejected by Django authentication.

## 4. Application Navigation and Pages

### Dashboard (`/`)

The dashboard shows counts for visible, active, and completed studies. Users with user-management permission also see a total account count; other users see their role instead. Study counts are scoped to studies the current user may see. A recent-studies grid displays up to six records and links to study details.

The sidebar links to Dashboard and Clinical Studies. User Management and Role Management are shown only to users with the corresponding permissions. The sidebar can collapse and remembers its state in local storage. The top bar contains a search field and notification bell for future use, plus the current user's name/role, profile link, and logout action.

### Clinical Studies (`/studies/`)

The study register is a DevExtreme DataGrid backed by `GET /api/studies/`. The table supports text search, column sorting and filtering, pagination/page-size choice, column resizing, column hiding/chooser, status badges, and Excel export. The API limits records to the current user's authorized study scope before returning them.

Users with `add_clinicalstudy` can create studies. Users with `change_clinicalstudy` can edit them and archive them. The form covers:

- Protocol number, title, description, study type, and therapeutic area.
- Sponsor name/contact/email and CRO name.
- Trial phase, design, indication, planned enrollment, and site count.
- Start, estimated completion, and actual completion dates.
- Status and study manager.

The system generates a `CD-` study identifier. Protocol numbers are unique. Study managers can be selected only by users with study-assignment permission; a selected manager is automatically added to the study team. Date validation rejects completion dates earlier than the start date.

Archiving requires confirmation, sets status to Archived, and removes a record from the normal active listing. Archived studies can be selected with the Archived filter. Permanent study deletion is intentionally disabled; the API returns HTTP 405 and instructs the caller to archive instead.

### Study Details (`/studies/<uuid>/`)

The details page loads a study through its protected detail API. It displays the study ID, protocol, title, sponsor, therapeutic area, description, phase, ownership, timeline, team, and audit timestamps. KPI tiles show active assigned-user count, planned duration when both dates exist, status, and planned enrollment.

Users with `assign_study_members` can assign active users to a study and remove members. Removal sets `StudyMember.is_active` to false; it does not delete the assignment history. Duplicate active assignments are rejected. Only users with both the assignment permission and access to that particular study can manage its members.

Documents, TMF, Review & Approval, and Study Reports appear only as clearly marked "Available in upcoming phase" placeholders. They do not store or process documents, approval tasks, or reports.

### User Management (`/users/`)

This page is available only to users with `manage_users`. Its DataGrid supports search, sorting, column filtering, paging, column hiding, export, and active/inactive status filtering. It lists identity, contact, department, designation, organization, role, assigned studies, account status, date joined, and row actions.

The add/edit form includes first/last name, unique employee ID, unique email, phone, department, designation, organization, reporting manager, role, account status, optional password, and optional profile image (up to 5 MB). Directory choices come from protected department/designation/organization APIs. If an administrator creates a user without a password, the application assigns an unknown random password and requests a password-reset email for the new account.

Row actions include view details, edit, activate/deactivate, and reset-password support through the API. Deactivation is soft: the account and its study history remain stored, but the account cannot log in. There is no user delete action. The final active System Administrator cannot be deactivated or reassigned through the user API.

Role assignment is separately protected: a user manager must also have `manage_roles` to assign a role. Profile images are validated as image files by Django and capped at 5 MB by the serializer.

### Role Management (`/roles/`)

This page is available only to users with `manage_roles`. The grid lists role ID, name, description, assigned-user count, creation date, and status. Administrators can create/edit roles, assign application permissions, activate/deactivate non-system roles, export the grid, and inspect assigned users.

The API only permits permissions belonging to the ClinDocs app (`polls` is the internal Django app label). Role permissions are enforced by Django's backend permission checks; hiding a button is not the security control. The built-in System Administrator role cannot be renamed, deactivated, or have its permissions changed through the API. Deactivating another role removes that role's permission grants from its users; the UI asks for confirmation if users are assigned.

### My Profile (`/profile/`)

The profile page displays the signed-in user's name, email, phone, employee ID, department, designation, organization, role, account status, creation date, last login, and study IDs. It is read-only in this phase; there is no profile-edit workflow.

### Django Admin (`/admin/`)

Staff/superusers can use Django Admin to manage custom users, studies, roles, study membership, audit records, and department/designation/organization directories. The app is displayed as ClinDocs in Django Admin. The Python package and migration label remain `polls` for compatibility.

## 5. Roles and Authorization

The default roles are created after migrations:

| Role | Default capability |
| --- | --- |
| System Administrator | All permissions generated for the ClinDocs app, including user/role administration, study management, assignment, and global study visibility. |
| Clinical Project Manager | View, create, and edit studies; assign study members. Access remains scoped to created, managed, or assigned studies. |
| Document Manager | View studies in their authorized scope. Document-management functionality is not implemented yet. |
| Clinical Research Associate (CRA) | View studies in their authorized scope. |
| Reviewer | View studies in their authorized scope. |
| Approver | View studies in their authorized scope. |
| Read Only User | View studies in their authorized scope. |

The user must be active and have an active role for role permissions to apply. Django superusers also receive Django's superuser permissions while active. `view_clinicalstudy` permits study reads but does not grant portfolio-wide visibility. `view_all_clinicalstudies` is the explicit global-view permission.

A study is in a user's scope when the user has global study visibility, is the study manager, created the study, or has an active `StudyMember` assignment. For writes, the role also needs the operation permission (for example `change_clinicalstudy` or `assign_study_members`) and the user's scope must include that study. User/role APIs are guarded separately by `manage_users` and `manage_roles`.

## 6. Study Lifecycle and Data Rules

Supported statuses are Draft, Planning, Active, On Hold, Completed, and Archived. Trial phase values are I, II, III, and IV. Study and user primary keys are UUIDs; each study also has a generated human-facing study ID. Protocol number, email, employee ID, and role name are unique.

An active study/user assignment is unique per pair. Removing a member deactivates the assignment, permitting a later new active assignment while retaining history. Users referenced by study/audit activity are protected from accidental hard deletion by foreign-key behavior. Studies should be archived rather than deleted.

Audit entries are written for user creation/update/activation/deactivation/password reset, role creation/update, study create/update/archive, and study-member assignment/removal. Each record stores actor (if present), action, module, object ID, description, timestamp, and IP address where available.

## 7. REST API Reference

All API paths are under `/api/`. Session-authenticated requests use CSRF protection for state-changing browser requests.

### Authentication

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/auth/login/` | Authenticate by email/password and establish a session. |
| POST | `/api/auth/logout/` | End the authenticated session. |
| GET | `/api/auth/profile/` | Return the signed-in user's profile. |
| POST | `/api/auth/password-reset/` | Request a reset email without disclosing account existence. |
| POST | `/api/auth/password-reset-confirm/` | Validate uid/token and set the new password. |

### Users, roles, and lookups

| Method | Path | Purpose |
| --- | --- | --- |
| GET, POST | `/api/users/` | List/search/filter users or create one. Requires `manage_users`. |
| GET, PUT, PATCH | `/api/users/<id>/` | Read/update a user. Requires `manage_users`. |
| POST | `/api/users/<id>/activate/` | Activate a user. |
| POST | `/api/users/<id>/deactivate/` | Soft-deactivate a user; protects the final active administrator. |
| POST | `/api/users/<id>/reset-password/` | Send a reset link. |
| GET, POST | `/api/roles/` | List or create roles. Requires `manage_roles`. |
| GET, PUT, PATCH | `/api/roles/<id>/` | Read/update a role; built-in administrator safeguards apply. |
| GET | `/api/roles/<id>/users/` | List users with that role. |
| GET | `/api/permissions/` | List available ClinDocs permissions. |
| GET | `/api/departments/`, `/api/designations/`, `/api/organizations/` | Return active directory values for user forms. Requires `manage_users`. |

### Studies

| Method | Path | Purpose |
| --- | --- | --- |
| GET, POST | `/api/studies/` | List visible studies or create a study. |
| GET, PUT, PATCH | `/api/studies/<uuid>/` | Read or update a study. |
| GET | `/api/studies/candidates/` | List active user candidates for team assignment. Requires `assign_study_members`. |
| POST | `/api/studies/<uuid>/members/` | Assign an active user to an in-scope study. |
| DELETE | `/api/studies/<uuid>/members/<user_uuid>/` | Soft-remove an active member. |
| POST | `/api/studies/<uuid>/archive/` | Mark the study archived. |
| DELETE | `/api/studies/<uuid>/` | Not supported; returns HTTP 405. |

Study list filters include `status` and `archived=true`. Search and ordering fields are configured on the DRF viewsets. List endpoints are not configured with DRF server-side pagination; the DevExtreme grids paginate the returned data in the browser.

## 8. Configuration and Storage

The default database is `clindocs.sqlite3`. The original starter `db.sqlite3` is preserved and is not the active database. Set `SQLITE_DB_NAME` to select another SQLite path. Set `POSTGRES_DB` to enable PostgreSQL and optionally set `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT`.

Other environment settings are `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_EMAIL_BACKEND`, and `DJANGO_DEFAULT_FROM_EMAIL`. Local defaults are for development only. Before deployment, use a unique secret key, turn debug off, configure hosts and HTTPS, use a production email service, and provide production-grade database, media, backup, monitoring, and access controls.

Profile uploads go to `media/profiles/`. Django serves media files through the development URL configuration only when `DEBUG` is enabled. Static project CSS/JS are in the app static directory. Framework assets are CDN-loaded, so the browser needs network access to those CDNs.

## 9. Future/Non-Functional UI Areas

- Global search is a top-bar visual placeholder; individual data grids have their own working search.
- Notification bell is a placeholder and does not send notifications.
- Settings navigation is disabled/placeholder.
- My Profile is read-only.
- Documents, TMF, review/approval, and reports are labeled as future-phase content and do not provide fake functionality.
- The "GxP-ready foundation" sidebar text is branding copy only. The application is not validated or certified for regulated production use.

## 10. Verification Commands

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test polls
```