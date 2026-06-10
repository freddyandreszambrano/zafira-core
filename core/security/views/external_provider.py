import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from core.security.forms import ExternalProviderForm
from core.security.mixins import PermissionMixin
from core.security.models import ExternalProvider


class ExternalProviderListView(PermissionMixin, TemplateView):
    template_name = "external_provider/list.html"
    permission_required = "view_externalprovider"

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get("action", None)
        try:
            if action == "search":
                data = []
                page = request.POST.get("page")
                page_size = request.POST.get("page_size")
                search_value = request.POST.get("search[value]", "")
                query = Q()
                if search_value:
                    query.add(
                        (Q(name__icontains=search_value) | Q(client_id__icontains=search_value)),
                        Q.OR,
                    )
                queryset = ExternalProvider.objects.filter(query).order_by("-id")
                paginator = Paginator(queryset, page_size)
                paginated_data = paginator.get_page(page)
                response = [item.to_json() for item in paginated_data]
                data = {
                    "data": response,
                    "recordsTotal": paginator.count,
                    "recordsFiltered": paginator.count,
                }
            elif action == "change_state":
                provider = ExternalProvider.objects.get(pk=request.POST.get("id"))
                provider.is_active = not provider.is_active
                provider.save()
            else:
                data["error"] = "No ha seleccionado ninguna opción"
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Proveedores externos"
        context["create_url"] = reverse_lazy("external_provider_create")
        return context


class ExternalProviderCreateView(PermissionMixin, CreateView):
    model = ExternalProvider
    template_name = "external_provider/form.html"
    form_class = ExternalProviderForm
    success_url = reverse_lazy("external_provider_list")
    permission_required = "add_externalprovider"

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get("action", None)
        try:
            if action == "add":
                form = self.get_form()
                if form.is_valid():
                    form.save()
                    data["success"] = True
                else:
                    data["error"] = form.errors.as_json()
            elif action == "validate_data":
                pattern = request.POST.get("pattern", "")
                if pattern == "name":
                    value = request.POST.get("name", "")
                    data["valid"] = not ExternalProvider.objects.filter(name__iexact=value).exists()
                else:
                    data["valid"] = True
            else:
                data["error"] = "No ha seleccionado ninguna opción"
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Crear proveedor externo"
        context["list_url"] = self.success_url
        context["action"] = "add"
        return context


class ExternalProviderUpdateView(PermissionMixin, UpdateView):
    model = ExternalProvider
    template_name = "external_provider/form.html"
    form_class = ExternalProviderForm
    success_url = reverse_lazy("external_provider_list")
    permission_required = "change_externalprovider"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get("action", None)
        try:
            if action == "edit":
                form = self.get_form()
                if form.is_valid():
                    form.save()
                    data["success"] = True
                else:
                    data["error"] = form.errors.as_json()
            elif action == "validate_data":
                pattern = request.POST.get("pattern", "")
                if pattern == "name":
                    value = request.POST.get("name", "")
                    data["valid"] = (
                        not ExternalProvider.objects.exclude(pk=self.object.pk)
                        .filter(name__iexact=value)
                        .exists()
                    )
                else:
                    data["valid"] = True
            else:
                data["error"] = "No ha seleccionado ninguna opción"
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Editar proveedor externo"
        context["list_url"] = self.success_url
        context["action"] = "edit"
        return context


class ExternalProviderDeleteView(PermissionMixin, DeleteView):
    model = ExternalProvider
    template_name = "external_provider/delete.html"
    success_url = reverse_lazy("external_provider_list")
    permission_required = "delete_externalprovider"

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            self.get_object().delete()
            data["success"] = True
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


__all__ = [
    "ExternalProviderListView",
    "ExternalProviderCreateView",
    "ExternalProviderUpdateView",
    "ExternalProviderDeleteView",
]
