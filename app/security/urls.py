from django.urls import path

from .views import (
    GroupCreateView,
    GroupDeleteView,
    GroupListView,
    GroupUpdateView,
    ModuleCreateView,
    ModuleDeleteView,
    ModuleListView,
    ModuleTypeCreateView,
    ModuleTypeDeleteView,
    ModuleTypeListView,
    ModuleTypeUpdateView,
    ModuleUpdateView,
)


urlpatterns = [
    # Module type
    path('module_type/', ModuleTypeListView.as_view(), name='module_type_list'),
    path('module_type/create/', ModuleTypeCreateView.as_view(), name='module_type_create'),
    path('module_type/update/<int:pk>/', ModuleTypeUpdateView.as_view(), name='module_type_update'),
    path('module_type/delete/<int:pk>/', ModuleTypeDeleteView.as_view(), name='module_type_delete'),

    # Module
    path('module/', ModuleListView.as_view(), name='module_list'),
    path('module/create/', ModuleCreateView.as_view(), name='module_create'),
    path('module/update/<int:pk>/', ModuleUpdateView.as_view(), name='module_update'),
    path('module/delete/<int:pk>/', ModuleDeleteView.as_view(), name='module_delete'),

    # Group
    path('group/', GroupListView.as_view(), name='group_list'),
    path('group/create/', GroupCreateView.as_view(), name='group_create'),
    path('group/update/<int:pk>/', GroupUpdateView.as_view(), name='group_update'),
    path('group/delete/<int:pk>/', GroupDeleteView.as_view(), name='group_delete'),
]
