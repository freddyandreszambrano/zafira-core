from core.auth.models import User


class AuthApiZafira:
    def __init__(self, request):
        self.request = request

    def login(self, username):
        user = User.objects.filter(username=username).first()
        if user:
            print('user exists')
