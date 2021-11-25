from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:#if user is_staff, is_admin,is_active yoki is_active , is_seller
            return True
        return False 