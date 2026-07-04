import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from core.scraper.forms import ScraperSourceForm
from core.scraper.models import ScraperSource
from core.security.mixins import PermissionMixin


class ScraperSourceListView(PermissionMixin, TemplateView):
    template_name = "scraper_source/list.html"
    permission_required = "view_scrapersource"

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get("action", None)
        try:
            if action == "search":
                page = request.POST.get("page")
                page_size = request.POST.get("page_size")
                search_value = request.POST.get("search[value]", "")
                query = Q()
                if search_value:
                    query.add(Q(name__icontains=search_value) | Q(url__icontains=search_value), Q.OR)
                queryset = ScraperSource.objects.filter(query).order_by("name")
                paginator = Paginator(queryset, page_size)
                paginated_data = paginator.get_page(page)
                data = {
                    "data": [item.to_json() for item in paginated_data],
                    "recordsTotal": paginator.count,
                    "recordsFiltered": paginator.count,
                }
            else:
                data["error"] = "No ha seleccionado ninguna opcion"
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Fuentes del scraper"
        context["subtitle"] = "URLs guardadas para ejecutar extracciones recurrentes."
        context["create_url"] = reverse_lazy("scraper_source_create")
        return context


class ScraperSourceCreateView(PermissionMixin, CreateView):
    model = ScraperSource
    template_name = "scraper_source/form.html"
    form_class = ScraperSourceForm
    success_url = reverse_lazy("scraper_source_list")
    permission_required = "add_scrapersource"

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
                data["valid"] = self._validate_unique(request)
            else:
                data["error"] = "No ha seleccionado ninguna opcion"
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def _validate_unique(self, request):
        pattern = request.POST.get("pattern", "")
        value = request.POST.get(pattern, "")
        if pattern == "name":
            return not ScraperSource.objects.filter(name__iexact=value).exists()
        if pattern == "url":
            return not ScraperSource.objects.filter(url__iexact=value).exists()
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Crear fuente del scraper"
        context["list_url"] = self.success_url
        context["action"] = "add"
        return context


class ScraperSourceUpdateView(PermissionMixin, UpdateView):
    model = ScraperSource
    template_name = "scraper_source/form.html"
    form_class = ScraperSourceForm
    success_url = reverse_lazy("scraper_source_list")
    permission_required = "change_scrapersource"

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
                data["valid"] = self._validate_unique(request)
            else:
                data["error"] = "No ha seleccionado ninguna opcion"
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def _validate_unique(self, request):
        pattern = request.POST.get("pattern", "")
        value = request.POST.get(pattern, "")
        queryset = ScraperSource.objects.exclude(pk=self.object.pk)
        if pattern == "name":
            return not queryset.filter(name__iexact=value).exists()
        if pattern == "url":
            return not queryset.filter(url__iexact=value).exists()
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Editar fuente del scraper"
        context["list_url"] = self.success_url
        context["action"] = "edit"
        return context


class ScraperSourceDeleteView(PermissionMixin, DeleteView):
    model = ScraperSource
    template_name = "scraper_source/delete.html"
    success_url = reverse_lazy("scraper_source_list")
    permission_required = "delete_scrapersource"

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
