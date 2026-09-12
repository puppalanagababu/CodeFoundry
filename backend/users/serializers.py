from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]
        read_only_fields = ["id", "username", "email", "role"]


class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, min_length=1, max_length=150)
    password = serializers.CharField(
        write_only=True, required=True, min_length=6
    )
    password2 = serializers.CharField(
        write_only=True, required=True, min_length=6
    )
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]
        extra_kwargs = {"username": {"validators": []}}


    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        username = validated_data["username"]
        email = validated_data.get("email", "")
        password = validated_data["password"]

        # Role is ALWAYS STUDENT upon public registration
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=User.Role.STUDENT,
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    new_password2 = serializers.CharField(required=True, write_only=True, min_length=6)

    def validate(self, attrs):
        from django.contrib.auth.password_validation import validate_password
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode

        if attrs.get("new_password") != attrs.get("new_password2"):
            raise serializers.ValidationError({"new_password": "Passwords do not match."})

        uid = attrs.get("uid")
        token = attrs.get("token")

        try:
            uid_int = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_int)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"detail": "Invalid or expired password reset token."})

        if not user.is_active or not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"detail": "Invalid or expired password reset token."})

        # Run Django's configured password validators
        validate_password(attrs.get("new_password"), user)

        attrs["user"] = user
        return attrs
