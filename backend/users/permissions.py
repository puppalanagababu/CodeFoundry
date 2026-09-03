from rest_framework.permissions import BasePermission
from .models import User


class IsRecruiterUser(BasePermission):
    """
    Allows access only to authenticated users with RECRUITER or ADMIN role.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        user_role = getattr(user, "role", None)
        is_recruiter = (user_role == User.Role.RECRUITER)
        is_admin = (user_role == User.Role.ADMIN) or user.is_staff or user.is_superuser

        return is_recruiter or is_admin
