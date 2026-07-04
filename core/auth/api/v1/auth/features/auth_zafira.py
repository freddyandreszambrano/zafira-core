from django.contrib.auth import get_user_model
from django.utils import timezone

from core.auth.models import User
from core.profiles.models import MobileProfile


class AuthApiZafira:
    app_sources = ("zafira-app", "zafira-web")

    def __init__(self, request):
        self.request = request
        self.user = None

    def is_valid_source(self):
        return self.request.headers.get("app-source") in self.app_sources

    def check_disabled_account(self, username, password):
        user = get_user_model().objects.filter(username=username).first()
        return user is not None and not user.is_active and user.check_password(password)

    def login(self, username):
        self.user = User.objects.filter(username=username).first()
        if self.user:
            MobileProfile.objects.get_or_create(user=self.user)
            self.user.last_login = timezone.now()
            self.user.save(update_fields=["last_login"])
        return self.user

    def build_response(self, response):
        if self.user is not None:
            user_data = self.user.to_json_api()
            token = user_data.pop("token", response.data.get("token", ""))
            response.data = {
                "token": token,
                "user": user_data,
            }
        return response
