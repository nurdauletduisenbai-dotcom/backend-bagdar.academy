from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.courses.models import Course, Group

from .models import Invite, Organization, OrgMembership


class MyOrganizationSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'logo_url', 'timezone', 'roles')

    def get_roles(self, obj) -> list[str]:
        return self.context['request'].user.get_roles_for_org(obj.id)


class InviteCreateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=OrgMembership.Role.choices)
    course_id = serializers.IntegerField(required=False, allow_null=True)
    group_id = serializers.IntegerField(required=False, allow_null=True)
    max_uses = serializers.IntegerField(min_value=1, max_value=500, default=1)
    expires_in_days = serializers.IntegerField(min_value=1, max_value=90, default=7)

    def validate(self, attrs):
        org_id = self.context['org_id']
        course = group = None
        if attrs.get('course_id'):
            course = Course.objects.filter(id=attrs['course_id'], org_id=org_id).first()
            if not course:
                raise serializers.ValidationError({'course_id': 'Курс не найден в этой организации.'})
        if attrs.get('group_id'):
            if not course:
                raise serializers.ValidationError({'group_id': 'Группа указывается вместе с курсом.'})
            group = Group.objects.filter(id=attrs['group_id'], course=course).first()
            if not group:
                raise serializers.ValidationError({'group_id': 'Группа не найдена в этом курсе.'})
        attrs['course'] = course
        attrs['group'] = group
        attrs['expires_at'] = timezone.now() + timedelta(days=attrs.pop('expires_in_days'))
        return attrs


class InviteCreatedSerializer(serializers.ModelSerializer):
    invite_token = serializers.CharField(help_text='Показывается один раз — в базе хранится только хеш')

    class Meta:
        model = Invite
        fields = ('id', 'role', 'course', 'group', 'max_uses', 'used_count', 'expires_at', 'invite_token')
