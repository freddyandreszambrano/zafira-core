let tblUser;

function userCell(fullName, username) {
    const text = (fullName || username || '?').trim();
    const initials = Zafira.escape(text.split(/\s+/).map(p => p[0]).slice(0, 2).join('').toUpperCase());
    const safeText = Zafira.escape(text);
    const safeUsername = Zafira.escape(username);
    return `<div class="flex items-center gap-3">
        <span class="inline-flex items-center justify-center w-9 h-9 rounded-full gradient-primary text-white text-xs font-bold shadow-zafira">${initials}</span>
        <div class="flex flex-col leading-tight">
            <span class="font-medium text-zafira-obsidian">${safeText}</span>
            <span class="text-xs text-zafira-slate">@${safeUsername}</span>
        </div>
    </div>`;
}

const user = {
    list: function () {
        tblUser = Zafira.dataTable('#data', [
            {
                data: 'username',
                render: (username, type, row) => userCell(row.full_name, username),
            },
            { data: 'email', render: data => Zafira.escape(data) },
            {
                data: 'dni',
                render: data => `<code class="px-2 py-0.5 rounded bg-zafira-slate-soft/40 text-xs text-zafira-slate-deep">${Zafira.escape(data)}</code>`,
            },
            {
                data: 'is_staff',
                className: 'text-center',
                render: data => data
                    ? '<span class="z-badge z-badge--on"><span class="z-badge__dot"></span>Equipo</span>'
                    : '<span class="z-badge z-badge--off"><span class="z-badge__dot"></span>Usuario</span>',
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
        ], { toggleConfirm: '¿Cambiar el estado de este usuario?' });
    }
};

$(function () {
    user.list();
});
