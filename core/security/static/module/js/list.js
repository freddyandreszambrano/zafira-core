let tblModule;

const module_crud = {
    list: function () {
        tblModule = Zafira.dataTable('#data', [
            { data: 'name', render: data => Zafira.escape(data) },
            {
                data: 'url',
                render: data => `<code class="px-2 py-0.5 rounded bg-zafira-slate-soft/40 text-xs text-zafira-slate-deep">${Zafira.escape(data)}</code>`,
            },
            {
                data: 'module_type',
                defaultContent: '<span class="text-zafira-slate">—</span>',
                render: data => data ? Zafira.escape(data) : '<span class="text-zafira-slate">—</span>',
            },
            {
                data: 'icon',
                render: data => data
                    ? `<span class="inline-flex items-center justify-center w-8 h-8 rounded-lg gradient-soft"><i class="${Zafira.escape(data)} text-zafira-primary"></i></span>`
                    : '<span class="text-zafira-slate">—</span>',
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
        ], { toggleConfirm: '¿Cambiar el estado de este módulo?' });
    }
};

$(function () {
    module_crud.list();
});
