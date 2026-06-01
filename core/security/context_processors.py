from collections import OrderedDict

from .models import Module


def modules(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'available_modules': OrderedDict()}

    if user.is_superuser:
        qs = Module.objects.filter(is_active=True, is_visible=True)
    else:
        group_id = user.get_group_id_session() if hasattr(user, 'get_group_id_session') else None
        if not group_id and hasattr(user, 'set_group_session'):
            user.set_group_session()
            group_id = user.get_group_id_session()
        if not group_id:
            return {'available_modules': OrderedDict()}
        qs = Module.objects.filter(
            is_active=True,
            is_visible=True,
            module_groups__group_id=group_id,
        ).distinct()

    grouped = OrderedDict()
    for module in qs.select_related('module_type').order_by(
        'module_type__order', 'order', 'name',
    ):
        type_name = module.module_type.name if module.module_type else 'General'
        grouped.setdefault(type_name, []).append(module)
    return {'available_modules': grouped}
