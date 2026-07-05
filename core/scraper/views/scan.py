import json
import logging

from django.http import HttpResponse
from django.views.generic import TemplateView

from core.scraper.models import ScraperSource
from core.scraper.services import save_products, scan_auto_url
from core.security.mixins import PermissionMixin

logger = logging.getLogger(__name__)


class ScraperScanView(PermissionMixin, TemplateView):
    template_name = "scraper/scan.html"
    permission_required = "add_product"

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        try:
            if action == "scan":
                data = self._scan(request)
            elif action == "save_products":
                data = self._save_products(request)
            else:
                data = {"success": False, "error": "No ha seleccionado ninguna opcion"}
        except json.JSONDecodeError:
            data = {"success": False, "error": "Formato de productos invalido."}
        except ValueError as e:
            data = {"success": False, "error": str(e)}
        except Exception:
            logger.exception("Error inesperado en el scraper scan")
            data = {
                "success": False,
                "error": "Ocurrio un error inesperado al procesar la solicitud.",
                "products": [],
                "errors": [],
            }
        return HttpResponse(json.dumps(data, ensure_ascii=False), content_type="application/json")

    def _scan(self, request):
        source_url = request.POST.get("url", "")
        source_id = request.POST.get("source_id")
        if source_id:
            source = ScraperSource.objects.get(pk=source_id)
            source_url = source.url
        return scan_auto_url(
            source_url,
            max_products=request.POST.get("max_products", 10),
            persist=False,
        )

    def _save_products(self, request):
        products = json.loads(request.POST.get("products") or "[]")
        saved = save_products(request.POST.get("store", ""), products)
        return {"success": True, "saved": saved}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Scraper"
        context["sources"] = ScraperSource.objects.all().order_by("name")
        context["default_max_products"] = 10
        return context
