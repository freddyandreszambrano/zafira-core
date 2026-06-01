from django.contrib.auth.models import Permission
from django.db import models

from .module import Module


class Group(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    modules = models.ManyToManyField(
        Module, through='GroupModule', blank=True, related_name='groups',
    )
    permissions = models.ManyToManyField(
        Permission, through='GroupPermission', blank=True, related_name='security_groups',
    )

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'
        ordering = ['name']

    def __str__(self):
        return self.name

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
        }


class GroupModule(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_modules')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='module_groups')

    class Meta:
        verbose_name = 'Grupo - Módulo'
        verbose_name_plural = 'Grupos - Módulos'
        unique_together = ('group', 'module')

    def __str__(self):
        return f'{self.group.name} → {self.module.name}'


class GroupPermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Grupo - Permiso'
        verbose_name_plural = 'Grupos - Permisos'
        unique_together = ('group', 'module', 'permission')

    def __str__(self):
        return f'{self.group.name} → {self.permission.codename}'

    def to_json_session(self):
        return {
            'id': self.module.id,
            'name': self.module.name,
            'icon': self.module.icon,
            'url': self.module.url,
            'permission': self.permission.codename,
        }
