from core.auth.models import User
from core.profiles.models import MobileProfile


class AuthApiZafira:
    app_sources = ("zafira-app", "zafira-web")

    def __init__(self, request):
        self.request = request
        self.user = None

    def is_valid_source(self):
        return self.request.headers.get("app-source") in self.app_sources

    def login(self, username):
        self.user = User.objects.filter(username=username).first()
        if self.user:
            MobileProfile.objects.get_or_create(user=self.user)
        return self.user

    def build_response(self, response):
        if self.user is not None:
            response.data = self.user.to_json_api()
        return response
