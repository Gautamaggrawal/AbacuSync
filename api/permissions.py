from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.user_type == "ADMIN"


class IsCentre(permissions.BasePermission):
    """
    Custom permission to only allow centre users to access the view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.user_type == "CENTRE"


class IsAdminOrCentre(permissions.BasePermission):
    """
    Custom permission to only allow admin or centre users to access the view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.user_type in ["ADMIN", "CENTRE"]


class IsAdminUser(permissions.BasePermission):
    """
    Permission to allow only admin users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsCentreAdmin(permissions.BasePermission):
    """
    Permission to allow only centre admins.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and hasattr(request.user, "profile")
            and request.user.profile.is_centre_admin
        )


class IsTeacher(permissions.BasePermission):
    """
    Permission to allow only teachers.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and hasattr(request.user, "profile")
            and request.user.profile.is_teacher
        )


class IsStudent(permissions.BasePermission):
    """
    Permission to allow only students.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and hasattr(request.user, "profile")
            and request.user.profile.is_student
        )


class IsCentreAdminOrTeacher(permissions.BasePermission):
    """
    Permission to allow centre admins or teachers.
    """

    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, "profile"):
            return False
        return (
            request.user.profile.is_centre_admin
            or request.user.profile.is_teacher
        )


class IsCentreAdminForCentre(permissions.BasePermission):
    """
    Permission to allow only centre admins for specific centre.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not hasattr(request.user, "profile"):
            return False

        # Check if user is admin for this centre
        if hasattr(obj, "centre"):
            return (
                request.user.profile.is_centre_admin
                and request.user.profile.centre == obj.centre
            )

        # If object is centre itself
        if hasattr(obj, "id"):
            return (
                request.user.profile.is_centre_admin
                and request.user.profile.centre.id == obj.id
            )

        return False
