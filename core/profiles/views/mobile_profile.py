import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import DetailView, TemplateView

from core.profiles.models import MobileProfile
from core.security.mixins import PermissionMixin


class MobileProfileListView(PermissionMixin, TemplateView):
    template_name = "mobile_profile/list.html"
    permission_required = "view_mobileprofile"

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
                            Q(user__username__icontains=search_value)
                            | Q(user__email__icontains=search_value)
                            | Q(user__dni__icontains=search_value)
                            | Q(user__first_name__icontains=search_value)
                            | Q(user__last_name__icontains=search_value)
                            | Q(preferred_size__icontains=search_value)
                            | Q(country__icontains=search_value)
                            | Q(language__icontains=search_value)
                        ),
                        Q.OR,
                    )
                queryset = (
                    MobileProfile.objects.select_related("user").filter(query).order_by("-id")
                )
                paginator = Paginator(queryset, page_size)
                paginated = paginator.get_page(page)
                data = {
                    "data": [self._to_json(item) for item in paginated],
                    "recordsTotal": paginator.count,
                    "recordsFiltered": paginator.count,
                }
            else:
                data["error"] = "No ha seleccionado ninguna opcion"
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def _to_json(self, obj):
        return {
            "id": obj.id,
            "user_id": obj.user_id,
            "username": obj.user.username,
            "email": obj.user.email,
            "dni": obj.user.dni,
            "full_name": obj.user.get_full_name(),
            "user_type": obj.user.user_type,
            "gender": obj.get_gender_display(),
            "preferred_size": obj.preferred_size,
            "language": obj.language,
            "country": obj.country,
            "push_token": obj.push_token,
            "created_at": obj.created_at.strftime("%Y-%m-%d %H:%M"),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Perfiles mobile"
        context["subtitle"] = "Consulta informacion de usuarios registrados desde la app."
        return context


class MobileProfileDetailView(PermissionMixin, DetailView):
    model = MobileProfile
    template_name = "mobile_profile/detail.html"
    context_object_name = "profile"
    permission_required = "view_mobileprofile"

    def get_queryset(self):
        return MobileProfile.objects.select_related("user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Detalle perfil mobile"
        context["list_url"] = reverse_lazy("mobile_profile_list")
        context["style_preferences"] = json.dumps(
            self.object.style_preferences,
            indent=2,
            ensure_ascii=False,
        )
        return context
