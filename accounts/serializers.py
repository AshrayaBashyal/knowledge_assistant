from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

 
class RegisterSerializer(serializers.ModelSerializer):
    """
    Validates registration input and creates a new user with a hashed password. 
    """
 
    password = serializers.CharField(write_only=True, min_length=8)
 
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "password"]
        read_only_fields = ["id"]
 
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)