import json

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, TemplateView

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
            elif action == "change_state":
                profile = MobileProfile.objects.get(pk=request.POST.get("id"))
                profile.onboarding_force_show = not profile.onboarding_force_show
                profile.save(update_fields=["onboarding_force_show"])
            else:
                data["error"] = "No ha seleccionado ninguna opcion"
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def _to_json(self, obj):
        try_on_photo_url = ""
        if obj.try_on_photo:
            try_on_photo_url = self.request.build_absolute_uri(obj.try_on_photo.url)

        image_url = try_on_photo_url
        if not image_url and obj.user.image:
            image_url = self.request.build_absolute_uri(obj.user.image.url)

        return {
            "id": obj.id,
            "user_id": obj.user_id,
            "username": obj.user.username,
            "email": obj.user.email,
            "dni": obj.user.dni,
            "full_name": obj.user.get_full_name(),
            "user_type": obj.user.user_type,
            "image": image_url,
            "try_on_photo": try_on_photo_url,
            "gender": obj.get_gender_display(),
            "preferred_size": obj.preferred_size,
            "onboarding_completed": obj.onboarding_completed,
            "onboarding_force_show": obj.onboarding_force_show,
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

    def post(self, request, *args, **kwargs):
        profile = self.get_object()
        user = profile.user

        if request.POST.get("action") == "toggle_active":
            user.is_active = not user.is_active
            user.save(update_fields=["is_active"])
            status = "activada" if user.is_active else "desactivada"
            messages.success(request, f"Cuenta {status} correctamente.")

        return redirect("mobile_profile_detail", pk=profile.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Detalle perfil mobile"
        context["list_url"] = reverse_lazy("mobile_profile_list")
        return context


class MobileProfileDeleteView(PermissionMixin, DeleteView):
    model = MobileProfile
    template_name = "mobile_profile/delete.html"
    success_url = reverse_lazy("mobile_profile_list")
    permission_required = "delete_mobileprofile"

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            profile = self.get_object()
            profile.user.delete()
            data["success"] = True
        except Exception as e:
            data["error"] = str(e)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context
