from django.utils import timezone

from core.auth.models import User
from core.profiles.models import MobileProfile


class AuthApiZafira:
    app_sources = ("zafira-app", "zafira-web")

    def __init__(self, request):
        self.request = request
        self.user = None

    def login(self, username):
        self.user = User.objects.filter(username=username).first()
        if self.user:
            MobileProfile.objects.get_or_create(user=self.user)
            self.user.last_login = timezone.now()
            self.user.save(update_fields=["last_login"])
        return self.user
