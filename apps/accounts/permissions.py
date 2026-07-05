"""
Role-based DRF permission classes, reused across every app's API views.
Each checks request.user.role against the User.Role choices — nothing more.
Object-level ownership checks (e.g. "citizen can only see their own tokens")
live in the owning app (queue_management), not here.
"""
from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class _HasRole(BasePermission):
    """Base class: subclasses set `allowed_roles`."""
    allowed_roles: set[str] = set()
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


class IsCitizen(_HasRole):
    allowed_roles = {User.Role.CITIZEN}


class IsReception(_HasRole):
    allowed_roles = {User.Role.RECEPTION}


class IsOperator(_HasRole):
    allowed_roles = {User.Role.OPERATOR}


class IsManager(_HasRole):
    allowed_roles = {User.Role.MANAGER}


class IsDistrictAdmin(_HasRole):
    allowed_roles = {User.Role.DISTRICT_ADMIN}


class IsSupervisor(_HasRole):
    allowed_roles = {User.Role.SUPERVISOR}


class IsAdminRole(_HasRole):
    allowed_roles = {User.Role.ADMIN}


class IsAnyStaff(_HasRole):
    """Reception, Operator, Manager, District Admin, Supervisor, or Admin — anyone who isn't a plain Citizen."""
    allowed_roles = {
        User.Role.RECEPTION, User.Role.OPERATOR, User.Role.MANAGER,
        User.Role.DISTRICT_ADMIN, User.Role.SUPERVISOR, User.Role.ADMIN,
    }


class IsManagerOrAbove(_HasRole):
    allowed_roles = {User.Role.MANAGER, User.Role.DISTRICT_ADMIN, User.Role.SUPERVISOR, User.Role.ADMIN}


class IsOwnerOrStaff(BasePermission):
    """Object-level: the object's `citizen`/`user` field matches request.user, or requester is staff."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff_role:
            return True
        owner = getattr(obj, "citizen", None) or getattr(obj, "user", None)
        return owner_id_matches(owner, request.user)


def owner_id_matches(owner, user):
    return owner is not None and owner.pk == user.pk
