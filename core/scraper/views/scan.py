import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView

from core.scraper.adapters import ADAPTER_MAP
from core.scraper.services import scan_url


class ScraperScanView(LoginRequiredMixin, TemplateView):
    template_name = 'scraper/scan.html'
    login_url = 'login'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        if action != 'scan':
            data = {'success': False, 'error': 'No ha seleccionado ninguna opcion'}
            return HttpResponse(json.dumps(data), content_type='application/json')

        try:
            data = scan_url(
                store=request.POST.get('store', 'modarm'),
                source_url=request.POST.get('url', ''),
                max_products=request.POST.get('max_products', 10),
            )
        except Exception as e:
            data = {'success': False, 'error': str(e), 'products': [], 'errors': [str(e)]}
        return HttpResponse(json.dumps(data, ensure_ascii=False), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Scraper'
        context['stores'] = ADAPTER_MAP.keys()
        context['default_store'] = 'modarm'
        context['default_max_products'] = 10
        return context
