let tblModuleType;

const module_type = {
    list() {
        tblModuleType = Zafira.dataTable('#data', [
            {
                data: 'name',
                render: data => Zafira.escape(data),
            },
            {
                data: 'icon',
                render: data => data
                    ? `<span class="inline-flex items-center justify-center w-8 h-8 rounded-lg gradient-soft"><i class="${Zafira.escape(data)} text-zafira-primary"></i></span>`
                    : '<span class="text-zafira-slate">—</span>',
            },
            {
                data: 'order',
                className: 'text-center',
                render: data => `<span class="font-semibold text-zafira-slate-deep">${data}</span>`,
            },
            {
                data: 'is_active',
                className: 'text-center',
                render: data => Zafira.statusBadge(data),
            },
            {
                data: 'id',
                className: 'text-center',
                orderable: false,
                render: id => Zafira.rowActions(id),
            },
        ], { toggleConfirm: '¿Cambiar el estado de este tipo de módulo?' });
    },
};

$(function () {
    module_type.list();
});
