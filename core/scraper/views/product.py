import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import DeleteView, TemplateView

from core.scraper.models import Product, ScraperSource
from core.scraper.services import normalize_max_products, scan_saved_sources
from core.security.mixins import PermissionMixin


class ProductListView(PermissionMixin, TemplateView):
    template_name = "product/list.html"
    permission_required = "view_product"

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
                        (
                            Q(name__icontains=search_value)
                            | Q(base_name__icontains=search_value)
                            | Q(category__icontains=search_value)
                            | Q(store__icontains=search_value)
                            | Q(url__icontains=search_value)
                        ),
                        Q.OR,
                    )
                queryset = Product.objects.filter(query).order_by("-extracted_at")
                paginator = Paginator(queryset, page_size)
                paginated_data = paginator.get_page(page)
                data = {
                    "data": [item.to_json() for item in paginated_data],
                    "recordsTotal": paginator.count,
                    "recordsFiltered": paginator.count,
                }
            elif action == "scan_saved_sources":
                max_products = normalize_max_products(request.POST.get("max_products"), default=50)
                data = scan_saved_sources(max_products=max_products)
            else:
                data["error"] = "No ha seleccionado ninguna opcion"
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Productos scrapeados"
        context["subtitle"] = "Consulta y administra los productos extraidos por el scraper."
        context["source_count"] = ScraperSource.objects.count()
        context["source_list_url"] = reverse_lazy("scraper_source_list")
        return context


class ProductDeleteView(PermissionMixin, DeleteView):
    model = Product
    template_name = "product/delete.html"
    success_url = reverse_lazy("scraper_product_list")
    permission_required = "delete_product"

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
