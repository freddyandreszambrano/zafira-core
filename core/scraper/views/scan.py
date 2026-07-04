import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView

from core.scraper.models import ScraperSource
from core.scraper.services import scan_auto_url


class ScraperScanView(LoginRequiredMixin, TemplateView):
    template_name = "scraper/scan.html"
    login_url = "login"

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action != "scan":
            data = {"success": False, "error": "No ha seleccionado ninguna opcion"}
            return HttpResponse(json.dumps(data), content_type="application/json")

        try:
            source_url = request.POST.get("url", "")
            source_id = request.POST.get("source_id")
            if source_id:
                source = ScraperSource.objects.get(pk=source_id)
                source_url = source.url
            data = scan_auto_url(source_url, max_products=request.POST.get("max_products", 10))
        except Exception as e:
            data = {"success": False, "error": str(e), "products": [], "errors": [str(e)]}
        return HttpResponse(json.dumps(data, ensure_ascii=False), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Scraper"
        context["sources"] = ScraperSource.objects.all().order_by("name")
        context["default_max_products"] = 10
        return context
