let tblGroup;

const group = {
    list() {
        tblGroup = Zafira.dataTable('#data', [
            {
                data: 'name',
                render: data => `<div class="flex items-center gap-3">
                    <span class="inline-flex items-center justify-center w-8 h-8 rounded-lg gradient-soft">
                        <i class="fas fa-user-tag text-zafira-primary text-xs"></i>
                    </span>
                    <span class="font-medium">${Zafira.escape(data)}</span>
                </div>`,
            },
            {
                data: 'description',
                render: data => data
                    ? `<span class="text-zafira-slate-deep">${Zafira.escape(data)}</span>`
                    : '<span class="text-zafira-slate">Sin descripción</span>',
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
        ], { toggleConfirm: '¿Cambiar el estado de este grupo?' });
    },
};

$(function () {
    group.list();
});
