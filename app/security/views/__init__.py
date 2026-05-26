from .group import GroupCreateView, GroupDeleteView, GroupListView, GroupUpdateView
from .module import (
    ModuleCreateView,
    ModuleDeleteView,
    ModuleListView,
    ModuleTypeCreateView,
    ModuleTypeDeleteView,
    ModuleTypeListView,
    ModuleTypeUpdateView,
    ModuleUpdateView,
)

__all__ = [
    'ModuleListView', 'ModuleCreateView', 'ModuleUpdateView', 'ModuleDeleteView',
    'ModuleTypeListView', 'ModuleTypeCreateView', 'ModuleTypeUpdateView', 'ModuleTypeDeleteView',
    'GroupListView', 'GroupCreateView', 'GroupUpdateView', 'GroupDeleteView',
]
