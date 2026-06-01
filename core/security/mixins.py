from typing import Iterable, List, Optional, Union

from crum import get_current_request
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator

from .models import Group, Module


def _login_redirect():
    return getattr(settings, 'LOGIN_REDIRECT_URL', '/')


class PermissionMixin:
    permission_required: Optional[Union[str, Iterable[str]]] = None

    def get_permits(self) -> List[str]:
        if not self.permission_required:
            return []
        if isinstance(self.permission_required, str):
            return [self.permission_required]
        return list(self.permission_required)

    def get_last_url(self):
        request = get_current_request()
        if request and 'url_last' in request.session:
            return request.session['url_last']
        return _login_redirect()

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            request.session['url_last'] = request.path
            request.session['module'] = {
                'name': 'Superuser',
                'icon': 'fas fa-user-shield',
                'permissions': '*',
            }
            return super().get(request, *args, **kwargs)

        request.session['module'] = None
        try:
            if 'group' not in request.session:
                messages.error(request, 'No tiene un grupo seleccionado.')
                return HttpResponseRedirect(self.get_last_url())

            group_id = request.session['group'].get('id')
            group = Group.objects.filter(id=group_id).first()
            if not group:
                messages.error(request, 'El grupo seleccionado no existe.')
                return HttpResponseRedirect(self.get_last_url())

            for codename in self.get_permits():
                if not group.grouppermission_set.filter(permission__codename=codename).exists():
                    messages.error(request, 'No tiene permiso para ingresar a este módulo')
                    return HttpResponseRedirect(self.get_last_url())

            permits = self.get_permits()
            if permits:
                gp = group.grouppermission_set.filter(permission__codename=permits[0]).first()
                if gp:
                    request.session['module'] = gp.to_json_session()
            request.session['url_last'] = request.path

            return super().get(request, *args, **kwargs)
        except Exception:
            return HttpResponseRedirect(_login_redirect())


class ModuleMixin:
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        request.session['module'] = None

        if request.user.is_superuser:
            request.session['module'] = {
                'name': 'Superuser',
                'icon': 'fas fa-user-shield',
                'permissions': '*',
            }
            return super().get(request, *args, **kwargs)

        try:
            request.user.set_group_session()
            group_id = request.user.get_group_id_session()
            modules = Module.objects.filter(
                Q(module_type__is_active=True) | Q(module_type__isnull=True)
            ).filter(
                group_modules__group_id=group_id,
                is_active=True,
                url=request.path,
                is_visible=True,
            )
            if modules.exists():
                request.session['module'] = modules.first().to_json()
                return super().get(request, *args, **kwargs)
            messages.error(request, 'No tiene permiso para ingresar a este módulo')
            return HttpResponseRedirect(_login_redirect())
        except Exception:
            return HttpResponseRedirect(_login_redirect())
