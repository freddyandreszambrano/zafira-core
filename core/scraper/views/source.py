import json
import re
from urllib.parse import unquote, urlparse

from django.core.paginator import Paginator
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from core.scraper.forms import ScraperSourceForm
from core.scraper.models import ScraperSource
from core.security.mixins import PermissionMixin

SOURCE_URL_PATTERN = re.compile(r"https?://[^\s,;]+", re.IGNORECASE)


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
                    query.add(
                        Q(name__icontains=search_value) | Q(url__icontains=search_value), Q.OR
                    )
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
                data = self._save_sources(request)
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
            urls = self._extract_urls(value)
            if not urls:
                return True
            return not any(ScraperSource.objects.filter(url__iexact=url).exists() for url in urls)
        return True

    def _save_sources(self, request):
        urls = self._extract_urls(request.POST.get("url", ""))
        if len(urls) <= 1:
            post = request.POST.copy()
            if urls:
                post["url"] = urls[0]
            form = self.form_class(post)
            if form.is_valid():
                form.save()
                return {"success": True}
            return {"error": form.errors.as_json()}

        name = request.POST.get("name", "").strip()
        if not name:
            return {"error": "Ingrese un nombre"}

        duplicated_urls = [
            url for url in urls if ScraperSource.objects.filter(url__iexact=url).exists()
        ]
        if duplicated_urls:
            return {"error": f"La URL ya se encuentra registrada: {duplicated_urls[0]}"}

        forms = []
        used_names = set()
        for index, url in enumerate(urls, start=1):
            source_name = self._unique_source_name(
                self._source_name(name, url, index, len(urls)),
                used_names,
            )
            form = self.form_class({"name": source_name, "url": url})
            if not form.is_valid():
                return {"error": form.errors.as_json()}
            forms.append(form)
            used_names.add(source_name.lower())

        with transaction.atomic():
            for form in forms:
                form.save()
        return {"success": True, "created": len(forms)}

    def _extract_urls(self, raw_value):
        raw_value = (raw_value or "").strip()
        if not raw_value:
            return []

        urls = [
            url.rstrip("/") + "/" if url.endswith("//") else url
            for url in SOURCE_URL_PATTERN.findall(raw_value)
        ]
        remainder = (
            SOURCE_URL_PATTERN.sub("", raw_value).replace(",", " ").replace(";", " ").strip()
        )
        if remainder:
            return [raw_value]

        validator = URLValidator()
        valid_urls = []
        for url in urls:
            validator(url)
            if url not in valid_urls:
                valid_urls.append(url)
        return valid_urls

    def _source_name(self, base_name, url, index, total):
        if total == 1:
            return base_name
        label = self._category_label(url)
        if label and label.lower() not in base_name.lower():
            return f"{base_name} - {label}"
        return f"{base_name} {index}"

    def _category_label(self, url):
        parsed = urlparse(url)
        parts = []
        for part in parsed.path.split("/"):
            cleaned = unquote(part).strip()
            if not cleaned or cleaned.lower() == "c" or cleaned.isdigit():
                continue
            parts.append(cleaned.replace("-", " ").title())
        return " ".join(parts)

    def _unique_source_name(self, source_name, used_names):
        candidate = source_name.strip()
        unique_name = candidate
        counter = 2
        while (
            unique_name.lower() in used_names
            or ScraperSource.objects.filter(name__iexact=unique_name).exists()
        ):
            unique_name = f"{candidate} {counter}"
            counter += 1
        return unique_name

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
