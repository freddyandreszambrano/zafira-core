let tblExternalProvider;

const external_provider = {
    list() {
        tblExternalProvider = Zafira.dataTable('#data', [
            {
                data: 'name',
                render: data => Zafira.escape(data),
            },
            {
                data: 'client_id',
                render: data =>
                    `<code class="px-2 py-0.5 rounded bg-zafira-slate-soft/40 text-xs text-zafira-slate-deep">${Zafira.escape(data)}</code>`,
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
        ], { toggleConfirm: '¿Cambiar el estado de este proveedor externo?' });
    },
};

$(function () {
    external_provider.list();
});
