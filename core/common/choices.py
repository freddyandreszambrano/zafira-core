from django.db import models


class TextChoicesCustom(models.TextChoices):
    @classmethod
    def get_value(cls, label):
        for value, lbl in cls.choices:
            if lbl == label:
                return value
        return ''

    @classmethod
    def get_label(cls, value):
        for val, label in cls.choices:
            if val == value:
                return label
        return ''

    @classmethod
    def get_value_by_label(cls, label):
        return cls.get_value((label or '').strip())


class Department(TextChoicesCustom):
    HR = 'HR', 'Recursos Humanos'
    IT = 'IT', 'Información y Tecnología'
    FINANCE = 'FINANCE', 'Finanzas'
    SALES = 'SALES', 'Ventas'
    MARKETING = 'MARKETING', 'Marketing'
    OPERATIONS = 'OPERATIONS', 'Operaciones'
    OTHER = 'OTHER', 'Otro'
