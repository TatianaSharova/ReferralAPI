from rest_framework import permissions


class IsAuthor(permissions.BasePermission):
    '''Позволяет доступ только авторам.'''
    def has_object_permission(self, request, view, obj):
        return (obj.user == request.user
                or request.user.is_superuser)
