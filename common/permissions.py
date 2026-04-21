from rest_framework.permissions import SAFE_METHODS, BasePermission

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # GET, HEAD, OPTIONS -> cho phép tất cả user login
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # POST, PUT, DELETE -> chỉ admin
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )