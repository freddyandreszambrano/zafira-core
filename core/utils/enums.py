from django.db import models


class BaseTextChoices(models.TextChoices):
    @classmethod
    def get_value(cls, label):
        for value, choice_label in cls.choices:
            if choice_label == label:
                return value
        return ""

    @classmethod
    def get_label(cls, value):
        for choice_value, label in cls.choices:
            if choice_value == value:
                return label
        return ""

    @classmethod
    def get_value_by_label(cls, label):
        return cls.get_value((label or "").strip())


class UserTypeChoices(BaseTextChoices):
    ADMIN = "admin", "ADMIN"
    MOBILE = "mobile", "MOBILE"


class DepartmentChoices(BaseTextChoices):
    HR = "rrhh", "RECURSOS HUMANOS"
    IT = "tecnologia", "INFORMACION Y TECNOLOGIA"
    FINANCE = "finanzas", "FINANZAS"
    SALES = "ventas", "VENTAS"
    MARKETING = "marketing", "MARKETING"
    OPERATIONS = "operaciones", "OPERACIONES"
    OTHER = "otro", "OTRO"


class GenderChoices(BaseTextChoices):
    FEMALE = "femenino", "FEMENINO"
    MALE = "masculino", "MASCULINO"
    OTHER = "otro", "OTRO"
    UNDISCLOSED = "no_indica", "NO INDICA"
