class UserOutput:
    def __init__(self, user, message=None):
        self.user = user
        self.message = message

    @property
    def data(self):
        payload = {"user": self.user.to_json_api()}
        if self.message:
            payload["message"] = self.message
        return payload


class MessageOutput:
    def __init__(self, message):
        self.message = message

    @property
    def data(self):
        return {"message": self.message}
