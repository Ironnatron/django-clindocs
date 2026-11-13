from django.apps import apps
from django.contrib.auth.models import Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


DEFAULT_ROLES = {
    "System Administrator": ("Full application access, including user, role, and study administration.", None),
    "Clinical Project Manager": (
        "Create and manage studies and assign members within authorized scope.",
        {"view_clinicalstudy", "add_clinicalstudy", "change_clinicalstudy", "assign_study_members"},
    ),
    "Document Manager": ("View assigned studies and study information.", {"view_clinicalstudy"}),
    "Clinical Research Associate (CRA)": ("View assigned clinical studies and study details.", {"view_clinicalstudy"}),
    "Reviewer": ("View assigned studies and relevant study information.", {"view_clinicalstudy"}),
    "Approver": ("View assigned studies and study information.", {"view_clinicalstudy"}),
    "Read Only User": ("View authorized clinical studies without administrative access.", {"view_clinicalstudy"}),
}


@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    if sender.label != "polls":
        return
    Role = apps.get_model("polls", "Role")
    permissions = Permission.objects.filter(content_type__app_label="polls")
    for name, (description, codenames) in DEFAULT_ROLES.items():
        role, _ = Role.objects.get_or_create(
            name=name,
            defaults={"description": description, "is_system": name == "System Administrator"},
        )
        if name == "System Administrator":
            role.permissions.set(permissions)
        elif codenames:
            role.permissions.set(permissions.filter(codename__in=codenames))