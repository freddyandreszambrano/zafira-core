class MessageOutput:
    def __init__(self, message):
        self.message = message

    @property
    def data(self):
        return {"message": self.message}


class FieldValidationOutput:
    def __init__(self, exists=False, message=""):
        self.exists = exists
        self.message = message

    @property
    def data(self):
        return {
            "exists": self.exists,
            "message": self.message,
        }
