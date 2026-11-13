import secrets

from django.contrib.auth.models import Permission
from rest_framework import serializers

from .models import ClinicalStudy, CustomUser, Role, StudyMember


class RoleSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "is_active"]


class UserSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True, default="Unassigned")

    class Meta:
        model = CustomUser
        fields = ["id", "employee_id", "full_name", "email", "role_name", "is_active"]


class StudyMemberSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(is_active=True), source="user", write_only=True
    )
    assigned_role = RoleSummarySerializer(read_only=True)
    assigned_role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True), source="assigned_role", write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = StudyMember
        fields = ["id", "user", "user_id", "assigned_role", "assigned_role_id", "assigned_at", "is_active"]
        read_only_fields = ["id", "assigned_at", "is_active"]


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True, default="Unassigned")
    department_name = serializers.CharField(source="department.name", read_only=True, default="")
    designation_name = serializers.CharField(source="designation.name", read_only=True, default="")
    organization_name = serializers.CharField(source="organization.name", read_only=True, default="")
    password = serializers.CharField(write_only=True, required=False, min_length=10)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True), source="role", required=False, allow_null=True
    )
    assigned_studies = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id", "employee_id", "first_name", "last_name", "full_name", "email", "phone_number",
            "department", "department_name", "designation", "designation_name", "organization",
            "organization_name", "reporting_manager", "role_id", "role_name", "assigned_studies",
            "profile_image", "is_active", "is_staff", "date_joined", "last_login", "password",
        ]
        read_only_fields = ["id", "date_joined", "last_login", "is_staff"]

    def get_assigned_studies(self, obj):
        return list(
            obj.study_memberships.filter(is_active=True).values_list("study__study_id", flat=True)
        )

    def validate_email(self, value):
        return value.strip().lower()

    def validate_employee_id(self, value):
        return value.strip()

    def validate_profile_image(self, value):
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Profile images must be 5 MB or smaller.")
        return value

    def validate_role_id(self, value):
        request = self.context.get("request")
        if value and request and not request.user.has_perm("polls.manage_roles"):
            raise serializers.ValidationError("You do not have permission to assign roles.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_password(secrets.token_urlsafe(32))
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ClinicalStudySerializer(serializers.ModelSerializer):
    study_manager = UserSummarySerializer(read_only=True)
    study_manager_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(is_active=True), source="study_manager", required=False, allow_null=True
    )
    created_by = UserSummarySerializer(read_only=True)
    members = serializers.SerializerMethodField()
    assigned_user_count = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalStudy
        fields = [
            "id", "study_id", "protocol_number", "title", "description", "study_type", "therapeutic_area",
            "sponsor_name", "sponsor_contact", "sponsor_email", "cro_name", "clinical_phase", "study_design",
            "indication", "planned_enrollment", "number_of_sites", "start_date", "estimated_completion_date",
            "actual_completion_date", "status", "study_manager", "study_manager_id", "created_by", "members",
            "assigned_user_count", "created_at", "updated_at", "is_archived",
        ]
        read_only_fields = ["id", "study_id", "created_by", "created_at", "updated_at", "is_archived"]

    def get_members(self, obj):
        memberships = obj.memberships.filter(is_active=True).select_related("user", "assigned_role")
        return StudyMemberSerializer(memberships, many=True).data

    def get_assigned_user_count(self, obj):
        return obj.memberships.filter(is_active=True).count()

    def validate(self, attrs):
        request = self.context.get("request")
        if "study_manager" in attrs and request and attrs["study_manager"] != getattr(self.instance, "study_manager", None):
            if not request.user.has_perm("polls.assign_study_members"):
                raise serializers.ValidationError({"study_manager_id": "You do not have permission to assign a study manager."})
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        completion = attrs.get(
            "estimated_completion_date", getattr(self.instance, "estimated_completion_date", None)
        )
        actual_completion = attrs.get(
            "actual_completion_date", getattr(self.instance, "actual_completion_date", None)
        )
        if start and completion and completion < start:
            raise serializers.ValidationError({"estimated_completion_date": "Completion date cannot be before the start date."})
        if start and actual_completion and actual_completion < start:
            raise serializers.ValidationError({"actual_completion_date": "Actual completion cannot be before the start date."})
        return attrs


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.filter(content_type__app_label="polls").select_related("content_type"),
        required=False,
    )
    assigned_user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions", "assigned_user_count", "is_active", "is_system", "created_at"]
        read_only_fields = ["id", "is_system", "created_at"]

    def get_assigned_user_count(self, obj):
        return obj.users.count()


class PermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source="content_type.app_label", read_only=True)
    model = serializers.CharField(source="content_type.model", read_only=True)

    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "app_label", "model"]