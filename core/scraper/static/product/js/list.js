let tblProduct;

const productList = {
    list() {
        tblProduct = Zafira.dataTable('#data', [
            {
                data: 'image_urls',
                orderable: false,
                render: data => {
                    const imageUrl = Array.isArray(data) && data.length ? data[0] : '';
                    if (!imageUrl) {
                        return '<span class="inline-flex w-12 h-12 items-center justify-center rounded-lg bg-zafira-slate-soft text-zafira-slate"><i class="fas fa-image"></i></span>';
                    }
                    return `<img src="${Zafira.escape(imageUrl)}" alt="Producto" class="w-12 h-12 object-cover rounded-lg border border-zafira-slate-soft">`;
                },
            },
            {
                data: 'name',
                render: (data, type, row) => `<div class="font-medium">${Zafira.escape(data)}</div>
                    <div class="text-xs text-zafira-slate">${Zafira.escape(row.base_name || row.id_external)}</div>`,
            },
            {
                data: 'category',
                render: data => Zafira.escape(data || '-'),
            },
            {
                data: 'store',
                render: data => Zafira.escape(data || '-'),
            },
            {
                data: 'price',
                render: (data, type, row) => `${Zafira.escape(row.currency || 'USD')} ${Zafira.escape(data || '0.00')}`,
            },
            {
                data: 'availability',
                render: data => Zafira.escape(data || 'unknown'),
            },
            {
                data: 'id',
                className: 'text-center',
                orderable: false,
                render: (id, type, row) => `<div class="z-row-actions">
                    <a href="${Zafira.escape(Zafira.safeUrl(row.url))}" class="z-icon-btn" target="_blank" rel="noopener noreferrer" title="Abrir URL">
                        <i class="fas fa-arrow-up-right-from-square"></i>
                    </a>
                    <a href="${pathname}delete/${id}/" class="z-icon-btn z-icon-btn--danger" title="Eliminar">
                        <i class="fas fa-trash"></i>
                    </a>
                </div>`,
            },
        ], { toggleField: null });
    },

    bindRunSources() {
        const button = document.querySelector('[data-run-sources]');
        const maxInput = document.getElementById('id_run_max_products');
        if (!button) return;

        button.addEventListener('click', async () => {
            const confirmed = await zafira_confirm(
                'Ejecutar fuentes',
                'Se ejecutara el scraper sobre todas las URLs guardadas.'
            );
            if (!confirmed) return;

            zafira_set_button_loading(button, true, 'Ejecutando...');
            const formData = new FormData();
            formData.append('action', 'scan_saved_sources');
            formData.append('max_products', maxInput ? maxInput.value : '50');

            try {
                const response = await fetch(pathname, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrftoken },
                    body: formData,
                });
                const data = await response.json();
                if (data.error) {
                    await zafira_alert(data.error);
                    return;
                }
                await zafira_alert(
                    `${data.metadata.total_products} productos procesados desde ${data.metadata.total_sources} fuentes.`,
                    'Scraper completado',
                    'success'
                );
                tblProduct.ajax.reload(null, false);
            } catch (error) {
                await zafira_alert('No se pudo ejecutar el scraper.');
            } finally {
                zafira_set_button_loading(button, false);
            }
        });
    },
};

$(function () {
    productList.list();
    productList.bindRunSources();
});
