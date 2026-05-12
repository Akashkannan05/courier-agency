from rest_framework import serializers
from django.contrib.auth.models import User
from staff.models import StaffAccount, Location

class StaffUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    assigned_location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all(), required=False, allow_null=True)
    status = serializers.ChoiceField(choices=StaffAccount.STATUS_CHOICES, default='active')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'assigned_location', 'status']

    def create(self, validated_data):
        assigned_location = validated_data.pop('assigned_location', None)
        status = validated_data.pop('status', 'active')
        password = validated_data.pop('password')
        
        # Create the user
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create the associated StaffAccount
        StaffAccount.objects.create(
            user=user,
            assigned_location=assigned_location,
            status=status
        )
        return user
