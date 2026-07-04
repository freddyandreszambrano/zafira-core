let tblMobileProfile;

const mobileProfile = {
    userCell(fullName, username, imageUrl) {
        const text = (fullName || username || '?').trim();
        const initials = Zafira.escape(text.split(/\s+/).map(p => p[0]).slice(0, 2).join('').toUpperCase());
        const safeText = Zafira.escape(text);
        const safeUser = Zafira.escape(username);
        const avatar = imageUrl
            ? `<img src="${Zafira.escape(imageUrl)}" class="w-9 h-9 rounded-full object-cover shadow-zafira" alt="${safeText}">`
            : `<span class="inline-flex items-center justify-center w-9 h-9 rounded-full gradient-primary text-white text-xs font-bold shadow-zafira">${initials}</span>`;
        return `<div class="flex items-center gap-3">
            ${avatar}
            <div class="flex flex-col leading-tight">
                <span class="font-medium text-zafira-obsidian">${safeText}</span>
                <span class="text-xs text-zafira-slate">@${safeUser}</span>
            </div>
        </div>`;
    },

    detailAction(id) {
        return `<div class="z-row-actions">
            <a href="${pathname}detail/${id}/" class="z-icon-btn" title="Ver detalle">
                <i class="fas fa-eye"></i>
            </a>
        </div>`;
    },

    list() {
        tblMobileProfile = Zafira.dataTable('#data', [
            {
                data: 'username',
                render: (username, type, row) => mobileProfile.userCell(row.full_name, username, row.image),
            },
            {
                data: 'email',
                render: data => Zafira.escape(data),
            },
            {
                data: 'user_type',
                render: data =>
                    `<span class="z-badge z-badge--off"><span class="z-badge__dot"></span>${Zafira.escape(data)}</span>`,
            },
            {
                data: 'gender',
                render: data => Zafira.escape(data || '-'),
            },
            {
                data: 'preferred_size',
                render: data => Zafira.escape(data || '-'),
            },
            {
                data: 'onboarding_completed',
                className: 'text-center',
                orderable: false,
                render: data => data
                    ? '<span class="z-badge z-badge--on"><span class="z-badge__dot"></span>Completado</span>'
                    : '<span class="z-badge z-badge--off"><span class="z-badge__dot"></span>Pendiente</span>',
            },
            {
                data: 'onboarding_force_show',
                className: 'text-center',
                orderable: false,
                render: data => Zafira.statusBadge(data, ['Forzado', 'Normal']),
            },
            {
                data: 'id',
                className: 'text-center',
                orderable: false,
                render: id => mobileProfile.detailAction(id),
            },
        ], {
            toggleField: 'onboarding_force_show',
            toggleConfirm: '¿Cambiar "Forzar onboarding" para este usuario?',
        });
    },
};

$(function () {
    mobileProfile.list();
});
