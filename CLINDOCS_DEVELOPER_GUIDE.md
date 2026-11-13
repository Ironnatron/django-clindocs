# ClinDocs Developer Guide

## 1. What This Document Covers

This guide explains how the current codebase is organized, how requests move through it, what each source/configuration file does, and why the main code patterns are used. It is an implementation guide, not a regulated-system validation document.

## 2. High-Level Request Flow

### Page request

1. `manage.py` initializes Django with `mysite.settings` for commands and the development server.
2. `mysite.urls` sends `/admin/` to Django Admin, `/api/` to the REST API routes, and other page routes to `polls.urls`.
3. `polls.views` checks authentication/permissions and renders a template from `polls/templates/polls/`.
4. `base.html` supplies the common shell and loads Bootstrap, jQuery, DevExtreme, Font Awesome, ExcelJS, FileSaver, and local assets.

### API request

1. A page-level jQuery handler calls the matching path under `/api/`.
2. `polls.api_urls` maps auth/lookups directly and registers user, role, and study viewsets with DRF's router.
3. The API view invokes a permission class in `api_permissions.py`; object-level study rules are applied after queryset scoping.
4. A serializer parses/validates input and creates or updates the Django model.
5. Important mutations call `record_audit` in `api_views.py` to store an `AuditLog` row.
6. JSON responses are used to refresh grids/details and show toast feedback.

The API uses Django sessions, not JWT or API tokens. Django's session and authentication middleware are enabled; browser mutations include CSRF tokens in the `X-CSRFToken` header. Login and password-reset endpoints are explicitly CSRF-protected even though they allow anonymous requests.

## 3. Application Identity and Naming

The Python package and Django app label are still `polls`. That label is referenced by `AUTH_USER_MODEL`, permission names (`polls.manage_users`), migration dependencies, content types, imports, and template/static paths. Renaming it would require an intentional app-label/data migration, not merely a display-name change.

`polls.apps.ClinDocsConfig` sets `verbose_name = "ClinDocs"`, so Django Admin displays the product name while migration and permission identifiers remain stable. New files should follow the existing `polls` package layout unless a planned migration deliberately changes the app label.

## 4. Data Model and Relationships

The models live in `polls/models.py`.

- `Department`, `Designation`, and `Organization` are unique-name lookup tables. Users may reference them; deleting a lookup sets the corresponding nullable user field to null.
- `Role` has a UUID primary key, descriptive metadata, an active/system flag, and a many-to-many link to Django `Permission` rows. Users refer to one role. `is_system` supports safeguards for built-in roles.
- `CustomUser` extends Django's `AbstractBaseUser` and `PermissionsMixin`. Email is the unique authentication identifier; employee ID is also unique. It adds profile/contact, professional directory, reporting manager, role, active/staff, and join-date fields. The self-reference for reporting manager allows organizational reporting lines. UUID user IDs avoid relying on sequential identifiers in client-visible URLs.
- `ClinicalStudy` has a UUID database primary key and a generated human-facing `CD-...` study ID. Protocol number is unique. Sponsor, clinical, phase, enrollment, site, date, lifecycle, owner, creator, and audit timestamps are stored together. An index covers status/archive filtering.
- `StudyMember` links one user to one study, stores assignment role/actor/time, and soft-deactivates with `is_active`. A conditional unique constraint permits at most one active row per study/user pair while retaining inactive history.
- `AuditLog` records actor, action/module, object identifier, description, timestamp, and optional IP address. Its module/timestamp index supports audit filtering.

`CustomUserManager` implements `create_user` and `create_superuser`; Django's password hashing APIs are used rather than storing raw passwords. `CustomUser.has_perm` combines active-user checks, Django's built-in superuser/groups/direct permission behavior, and permissions on the user's active `Role`.

`ClinicalStudy.save` generates a study ID and makes an Archived status set `is_archived=True`. `ClinicalStudy.clean` contains model-level estimated-date validation. The REST serializer separately validates estimated and actual completion dates because serializer validation is the API request boundary.

## 5. Authorization Design

The permission classes in `polls/api_permissions.py` are the security boundary. Template conditions only hide controls for usability; a caller must still pass the API permission check.

- `CanManageUsers` checks `polls.manage_users`.
- `CanManageRoles` checks `polls.manage_roles`.
- `StudyAccessPermission` requires authentication, checks operation permissions, and checks study scope for object mutations.
- `is_system_administrator` is used for the last-active-administrator protection in user updates/deactivation.
- A user has study scope when globally authorized by `view_all_clinicalstudies`, named as the manager, is the creator, or has an active membership.
- Querysets are scoped before detail lookup. A study outside scope therefore usually returns 404 rather than revealing its existence with a permission error.
- Creating a study requires `add_clinicalstudy`. Editing/archive requires `change_clinicalstudy`; member add/removal and manager assignment require `assign_study_members` plus study scope.
- Permanent study deletion returns 405. User deletion is omitted from the user viewset's allowed HTTP methods; user deactivation is the supported account lifecycle operation.
- Role serializers accept only permissions belonging to the ClinDocs app label. The System Administrator role cannot be renamed, deactivated, or have its permissions changed through the API.
- User serializers reject role assignment unless the request user also has `manage_roles`; user-management permission alone is insufficient.

`CustomUser.has_perm` evaluates role permissions on demand. This is straightforward and keeps role updates effective immediately, though it may issue additional database queries; if performance requires caching, invalidation on role/user-permission changes must be designed carefully.

## 6. API Serialization and Mutation Rules

`polls/serializers.py` defines API representations:

- `UserSummarySerializer` and `RoleSummarySerializer` provide compact nested data for grids and team lists.
- `StudyMemberSerializer` accepts an active user identifier and optional active assigned-role identifier; response fields include nested user/role summary and assignment time.
- `UserSerializer` handles personal/professional references, role, assigned-study IDs, write-only optional password, and optional image. Passwords are hashed through `set_password`. A no-password create receives an unpredictable random password before a password-reset invitation is sent. Uploaded images are capped at 5 MB.
- `ClinicalStudySerializer` makes generated/creator/timestamp fields read-only, includes manager/member details and member count, checks date order, and requires assignment permission when manager ownership changes.
- `RoleSerializer` limits permission IDs to `polls` permissions and computes assigned-user count.
- `PermissionSerializer` returns permission metadata for the role editor.

The API writes audit entries from mutation handlers, where the request actor and client IP are available. The model layer doesn't automatically audit all admin-shell changes; Django Admin mutations do not pass through `record_audit`.

## 7. Default Role Initialization

`polls/apps.py` loads `polls.signals` from `AppConfig.ready`. `polls/signals.py` listens for Django's `post_migrate` signal and creates seven default roles after the app's model permissions exist. The System Administrator role receives all permissions with the `polls` content type. The other roles receive study-view permission; the Clinical Project Manager also receives study add/change/member-assignment permissions. `get_or_create` makes role records idempotent, and permissions are reset to the declared defaults on each `polls` post-migrate run.

## 8. URL and View Layers

- `mysite/urls.py` mounts `/api/`, the page routes at `/`, and Django Admin at `/admin/`. It serves uploaded media only in debug mode.
- `polls/urls.py` maps login, logout, password-reset screens, dashboard, study list/detail, profile, users, and roles to page views.
- `polls/views.py` renders the pages. `login_required` protects application areas, explicit permission checks protect user/role pages, and `ensure_csrf_cookie` initializes the CSRF cookie used by AJAX forms. Dashboard study counts use the same scope as the study API.
- `polls/api_urls.py` defines auth and directory lookup routes, then uses `DefaultRouter` to expose `UserViewSet`, `RoleViewSet`, and `ClinicalStudyViewSet` resources/actions.
- `polls/api_views.py` implements login/logout/profile/password reset, user and role CRUD/actions, permission/directory lists, study CRUD, member add/remove, candidate lookup, archive behavior, and audit recording.

Password reset uses Django's `PasswordResetForm`, `SetPasswordForm`, and `default_token_generator`. `polls/templates/polls/password_reset_subject.txt` and `password_reset_email.txt` define the outgoing message; the email link points to the ClinDocs confirmation page with uid/token query values.

## 9. Frontend Design and Browser Code

Templates use Django template inheritance. `base.html` defines the authenticated shell (sidebar, topbar, profile dropdown, footer), global library includes, and shared toast container. Public auth pages use the same base but render without the signed-in shell.

`polls/static/polls/app.css` contains CSS variables for product colors, layout primitives, sidebar/header/table/modal/auth/detail styling, status badges, and responsive breakpoints. It keeps grids and management layouts compact, hides/collapses navigation at smaller widths, and provides page-specific visual states.

`polls/static/polls/app.js` defines `window.ClinDocs` helpers:

- `api` sends JSON or multipart FormData through jQuery AJAX and attaches the CSRF header.
- `toast` displays transient success/error messages.
- `errorMessage` extracts a useful message from DRF responses.
- `escape` HTML-escapes dynamic text used in generated table markup.
- `statusBadge` returns the lifecycle status badge.
- The document-ready handler persists and toggles collapsed sidebar state.

Page-specific JavaScript is currently embedded in its template. Login/reset/profile pages use direct AJAX calls. Studies/users/roles use DevExtreme DataGrid for search, column filters, paging, column controls, and export. ExcelJS creates a workbook and FileSaver downloads it. Role permission checks and study/user actions remain server-enforced.

External CDN assets include Google Fonts, Bootstrap 4.6.2 CSS/JS, Font Awesome 5, DevExtreme 22.2.4, jQuery, ExcelJS, and FileSaver. The browser therefore needs access to those CDN hosts. No frontend package manager/build pipeline is configured.

## 10. Configuration and Database Notes

`mysite/settings.py` installs Django core apps, DRF, and `polls.apps.ClinDocsConfig`; defines middleware and templates; selects `polls.CustomUser`; and configures auth redirects, timezone, static/media paths, DRF session authentication, email, and database settings.

- Default SQLite path: project-root `clindocs.sqlite3`, overridable by `SQLITE_DB_NAME`.
- PostgreSQL activates when `POSTGRES_DB` is set; other connection values use `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT`.
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_EMAIL_BACKEND`, and `DJANGO_DEFAULT_FROM_EMAIL` are environment-configurable.
- Default mail backend is Django's console backend.
- `MEDIA_ROOT` is project-root `media/`; `MEDIA_URL` is `/media/`.

`db.sqlite3` is the original starter database and is intentionally not the active database. It has the old built-in-user migration history, so it was preserved rather than repurposed after `AUTH_USER_MODEL` changed. The generated `clindocs.sqlite3` file is the current local database and is ignored by Git. Back it up separately if its contents matter.

## 11. Migrations

- `polls/migrations/0001_initial.py` creates the directory, custom user, role, study, membership, and audit tables and their relations/constraints/indexes. It depends on Django auth permissions and uses `settings.AUTH_USER_MODEL` for custom-user references.
- `polls/migrations/0002_alter_clinicalstudy_options.py` adds the explicit `view_all_clinicalstudies` permission to the study model. That distinction prevents ordinary membership-view permission from granting portfolio-wide visibility.
- `polls/migrations/__init__.py` marks the migration directory as a Python package.

Do not edit applied migration files to change deployed schemas. Change models, generate a new migration with `python manage.py makemigrations`, inspect it, and apply with `python manage.py migrate`.

## 12. File-by-File Inventory

### Project root

| File | Purpose and why it exists |
| --- | --- |
| `.gitignore` | Excludes Python bytecode, local virtual environments, the active local SQLite database, uploaded media, and collected static output. This avoids committing machine-specific or user-generated files. |
| `README.md` | Short install/run/configuration/API overview for onboarding. This developer guide expands on the code architecture. |
| `requirements.txt` | Declares Django, DRF, Pillow for image fields/uploads, and psycopg's binary PostgreSQL driver so environments can install runtime dependencies reproducibly. |
| `manage.py` | Standard Django command entry point. Sets `DJANGO_SETTINGS_MODULE` and dispatches commands such as `migrate`, `createsuperuser`, `check`, `test`, and `runserver`. |
| `db.sqlite3` | Legacy starter database, not used by default. It is retained to avoid deleting prior local data and has pre-custom-user migration history. |
| `clindocs.sqlite3` | Current local application database, generated by migrations and ignored by Git. It contains user/study/role data for this checkout. |

### `mysite/` project package

| File | Purpose and why it exists |
| --- | --- |
| `mysite/__init__.py` | Empty marker that makes `mysite` an importable Python package. |
| `mysite/settings.py` | Central Django configuration: installed apps, middleware, URLs/templates, SQLite/PostgreSQL selection, custom user, auth redirects, password validators, timezone, static/media, email, and DRF defaults. Environment variables separate deployment values from source. |
| `mysite/urls.py` | Root URL router: `/api/` to REST endpoints, `/` to ClinDocs pages, `/admin/` to Django Admin, and debug-only media serving for uploaded profile images. |
| `mysite/asgi.py` | ASGI callable for asynchronous-capable deployment servers. It loads the same settings module as the rest of the project. |
| `mysite/wsgi.py` | WSGI callable for conventional synchronous deployment servers. It also loads `mysite.settings`. |

### `polls/` Django app package

| File | Purpose and why it exists |
| --- | --- |
| `polls/__init__.py` | Empty Python package marker. The app label remains `polls` for import, permission, and migration compatibility. |
| `polls/apps.py` | Declares `ClinDocsConfig`, the AppConfig used by Django. `name = 'polls'` retains the internal app identity; `verbose_name = 'ClinDocs'` changes the name displayed in Admin. `ready()` imports signals so post-migrate role seeding is registered. |
| `polls/models.py` | Defines the custom email user and manager, directory lookup tables, roles/permissions, clinical study lifecycle, unique active membership constraint, and audit log. It is the ORM schema and contains stable model-level behavior. |
| `polls/serializers.py` | DRF JSON boundary: shapes user/study/role payloads, hides passwords, resolves related IDs, validates dates/image size/role and manager assignments, and produces compact nested representations. |
| `polls/api_permissions.py` | Reusable REST authorization rules for user administration, role administration, global/assigned study visibility, study-level write scope, and System Administrator checks. Keeps authorization independent from template visibility. |
| `polls/api_views.py` | REST API handlers and viewsets. Owns session login/logout, reset-token handling, CRUD/actions, filtering/search, object scoping, member lifecycle, archival, and audit calls. `record_audit` centralizes request metadata capture. |
| `polls/api_urls.py` | Defines explicit auth, permission, and directory lookup API paths and registers user/role/study viewsets with DRF's router for standard list/detail/action routes. |
| `polls/views.py` | Server-rendered page handlers. Protects pages with login/permission checks, calculates scoped dashboard KPIs, renders templates, sets CSRF cookies, and handles browser logout. |
| `polls/urls.py` | Maps browser paths to `polls.views`: dashboard, login/logout, reset screens, study list/detail, profile, users, and roles. |
| `polls/signals.py` | Idempotently seeds the seven named default roles after model permissions are created. The signal runs after migrations and sets each role's declared default permissions. |
| `polls/admin.py` | Registers the custom email-based user with customized creation/change forms and configures study, role, member, audit, and directory records in Django Admin. Audit fields are read-only in Admin. |
| `polls/tests.py` | Django/DRF regression tests for email/inactive login, scoped study access, create permissions, duplicate/removal behavior, cross-study assignment denial, final admin protection, role assignment restriction, immutable system-role permissions, password-reset response privacy, page rendering, and archive-only study deletion. |

### `polls/migrations/`

| File | Purpose and why it exists |
| --- | --- |
| `polls/migrations/__init__.py` | Python package marker required for Django migration discovery. |
| `polls/migrations/0001_initial.py` | Initial schema migration for directories, custom user, role, study, memberships, and audit. Generated from models so new installations can reproduce the schema. |
| `polls/migrations/0002_alter_clinicalstudy_options.py` | Adds the explicit global study visibility permission while preserving narrower assigned-study viewing. |

### `polls/templates/polls/`

| File | Purpose and why it exists |
| --- | --- |
| `base.html` | Shared HTML document and authenticated layout: sidebar, topbar, notification placeholder, profile/logout dropdown, page content block, footer, toast host, and CDN/local assets. Template inheritance prevents repeating shell markup. |
| `login.html` | Email/password form, browser validation, show/hide password, optional remembered email, loading/error states, and AJAX login request. |
| `password_reset.html` | Email-based reset request form. Displays an enumeration-resistant generic success response from the API. |
| `password_reset_confirm.html` | Reads uid/token from the reset link, validates matching passwords in the browser, and submits the confirmation to the API. Server token/password validation remains authoritative. |
| `password_reset_subject.txt` | Plain-text subject for Django password-reset messages. |
| `password_reset_email.txt` | Plain-text reset message using Django's generated `protocol`, `domain`, `uid`, and one-time `token`. |
| `dashboard.html` | Scoped KPI summary and AJAX-loaded recent study grid. Counts are server-rendered; rows are fetched from the study API. |
| `studies.html` | Study DataGrid, status/search controls, create/edit modal, Excel export, and archive confirmation/action. JavaScript builds API payloads; DRF performs validation and authorization. |
| `study_detail.html` | Loads and displays one authorized study, team, KPI details, timeline, assignment/removal modal, and explicit future-module placeholders. |
| `users.html` | User directory grid, search/status controls, user create/edit/details modals, directory lookups, optional image upload, activation/deactivation, and password reset calls. |
| `roles.html` | Role grid, permission editor, activation controls, export, and assigned-user modal. The API protects built-in system role settings. |
| `profile.html` | Read-only account summary loaded from the authenticated profile API. |

### `polls/static/polls/`

| File | Purpose and why it exists |
| --- | --- |
| `app.css` | Shared theme tokens and layout styling, component visuals, status colors, modals/forms, empty/loading states, and responsive breakpoints for desktop/tablet/mobile. |
| `app.js` | Shared jQuery utilities for JSON/FormData API calls with CSRF, response error extraction, HTML escaping, toasts, status badge markup, and persistent sidebar collapse. |

## 13. Testing and Local Maintenance

Run checks from the project root:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test polls
```

`check` catches Django configuration/model/admin issues. `makemigrations --check --dry-run` catches model changes without migrations. `test polls` creates an isolated test database and exercises the REST/page behaviors in `polls/tests.py`.

For new behavior, prefer a focused test in the existing test module unless the test suite becomes large enough to justify separation. Test authorization at the API boundary, not just whether a template hides a button. Use Django migrations for schema changes and preserve the local database unless a deliberate reset is requested.

## 14. Current Boundaries and Deployment Cautions

- There is no separate frontend build system, bundled asset pipeline, or `package.json`; browser libraries load from CDNs.
- DevExtreme search and paging are client-side over the returned list; DRF pagination is not configured.
- Directory models have Admin-backed CRUD, while dedicated directory management screens are not present.
- The profile page is read-only. Notification, global-search, settings, document/TMF/workflow/report features are placeholders.
- Django Admin data changes do not currently create `AuditLog` rows; API mutation paths do.
- `clindocs.sqlite3` is local operational data, not a migration or source file. Configure backups before using real data.
- The development server, console email, debug media serving, fallback secret key, and CDN-only assets are not production deployment settings.
- "GxP-ready foundation" is UI copy, not a claim of validation, compliance certification, validated audit controls, or production suitability.