from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect

from .constants import MSG_PERMISSION_DENIED


class PublicMixin(UserPassesTestMixin):
    redirect_authenticated_to = "dashboard"

    def test_func(self):
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect(self.redirect_authenticated_to)


class StaffRequiredMixin(UserPassesTestMixin):
    permission_denied_message = MSG_PERMISSION_DENIED

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        return JsonResponse({"error": self.permission_denied_message}, status=403)


class GroupRequiredMixin(UserPassesTestMixin):
    required_groups: list[str] = []

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.groups.filter(name__in=self.required_groups).exists()


class JsonResponseMixin:
    @staticmethod
    def success(message="", **extra):
        return JsonResponse({"success": True, "message": message, **extra})

    @staticmethod
    def error(message="", status=400, **extra):
        return JsonResponse({"success": False, "error": message, **extra}, status=status)

    @staticmethod
    def validation_errors(form, status=400):
        errors = {field: str(error[0]) for field, error in form.errors.items()}
        return JsonResponse({"success": False, "errors": errors}, status=status)
