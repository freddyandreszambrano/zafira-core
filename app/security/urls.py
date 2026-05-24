from django.urls import path

from .views import (
    GroupCreate,
    GroupDelete,
    GroupListView,
    GroupUpdate,
    ModuleCreate,
    ModuleDelete,
    ModuleListView,
    ModuleTypeCreate,
    ModuleTypeDelete,
    ModuleTypeListView,
    ModuleTypeUpdate,
    ModuleUpdate,
)


urlpatterns = [
    # Module type
    path('module_type/', ModuleTypeListView.as_view(), name='module_type_list'),
    path('module_type/create/', ModuleTypeCreate.as_view(), name='module_type_create'),
    path('module_type/update/<int:pk>/', ModuleTypeUpdate.as_view(), name='module_type_update'),
    path('module_type/delete/<int:pk>/', ModuleTypeDelete.as_view(), name='module_type_delete'),

    # Module
    path('module/', ModuleListView.as_view(), name='module_list'),
    path('module/create/', ModuleCreate.as_view(), name='module_create'),
    path('module/update/<int:pk>/', ModuleUpdate.as_view(), name='module_update'),
    path('module/delete/<int:pk>/', ModuleDelete.as_view(), name='module_delete'),

    # Group
    path('group/', GroupListView.as_view(), name='group_list'),
    path('group/create/', GroupCreate.as_view(), name='group_create'),
    path('group/update/<int:pk>/', GroupUpdate.as_view(), name='group_update'),
    path('group/delete/<int:pk>/', GroupDelete.as_view(), name='group_delete'),
]
