const scraperScan = {
    result: null,

    init() {
        this.form = document.getElementById('frmScraperScan');
        this.submitButton = document.querySelector('[data-scan-submit]');
        this.status = document.querySelector('[data-scan-status]');
        this.summary = document.querySelector('[data-scan-summary]');
        this.tableBody = document.querySelector('[data-products-body]');
        this.jsonOutput = document.querySelector('[data-json-output]');
        this.jsonSize = document.querySelector('[data-json-size]');
        this.copyButton = document.querySelector('[data-copy-json]');
        this.sourceSelect = document.querySelector('[data-source-select]');
        this.urlInput = document.getElementById('id_url');

        if (!this.form) return;
        this.form.addEventListener('submit', event => this.submit(event));
        this.copyButton.addEventListener('click', () => this.copyJson());
        if (this.sourceSelect) {
            this.sourceSelect.addEventListener('change', () => this.syncSourceUrl());
            this.syncSourceUrl();
        }
    },

    syncSourceUrl() {
        const selected = this.sourceSelect.options[this.sourceSelect.selectedIndex];
        const savedUrl = selected ? selected.dataset.url : '';
        if (!this.urlInput) return;

        if (savedUrl) {
            this.urlInput.value = savedUrl;
            this.urlInput.required = false;
            this.urlInput.disabled = true;
            this.urlInput.readOnly = true;
            this.urlInput.setCustomValidity('');
            return;
        }
        this.urlInput.disabled = false;
        this.urlInput.required = true;
        this.urlInput.readOnly = false;
        this.urlInput.setCustomValidity('');
    },

    submit(event) {
        event.preventDefault();
        this.syncSourceUrl();
        if (!this.sourceSelect.value && !this.urlInput.value.trim()) {
            this.urlInput.setCustomValidity('Ingresa una URL o elige una fuente guardada.');
        } else {
            this.urlInput.setCustomValidity('');
        }
        if (!this.form.reportValidity()) return;

        this.setLoading(true);
        fetch(pathname, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            body: new FormData(this.form),
        })
            .then(response => response.json())
            .then(data => this.render(data))
            .catch(error => this.render({
                success: false,
                error: error.message,
                products: [],
                errors: [error.message],
            }))
            .finally(() => this.setLoading(false));
    },

    render(data) {
        this.result = data;
        const products = data.products || [];
        const errors = data.errors || [];

        this.status.className = `z-badge ${data.success ? 'z-badge--on' : 'z-badge--off'}`;
        this.status.innerHTML = `<span class="z-badge__dot"></span>${data.success ? 'Completado' : 'Error'}`;
        this.summary.textContent = data.success
            ? `${products.length} productos extraidos`
            : (data.error || 'No se pudo completar el escaneo');
        this.jsonSize.textContent = `${products.length} productos`;
        this.jsonOutput.textContent = JSON.stringify(data, null, 2);
        this.copyButton.disabled = false;

        if (!data.success) {
            this.tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-red-500 py-10">${this.escape(data.error || errors.join(', '))}</td></tr>`;
            return;
        }

        if (!products.length) {
            this.tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-zafira-slate py-10">No hay productos para mostrar</td></tr>';
            return;
        }

        this.tableBody.innerHTML = products.map(product => this.productRow(product)).join('');
    },

    productRow(product) {
        const imageUrl = (product.image_urls || [])[0];
        const price = product.price === null || product.price === undefined
            ? '-'
            : `${product.currency || 'USD'} ${product.price}`;
        const image = imageUrl
            ? `<img src="${this.escapeAttr(imageUrl)}" alt="${this.escapeAttr(product.name || 'Producto')}" class="w-14 h-14 object-cover rounded-lg border border-zafira-slate-soft">`
            : '<span class="inline-flex w-14 h-14 items-center justify-center rounded-lg bg-zafira-slate-soft text-zafira-slate"><i class="fas fa-image"></i></span>';

        return `<tr>
            <td>${image}</td>
            <td class="font-medium text-zafira-obsidian dark:text-zafira-slate-soft">${this.escape(product.name || '-')}</td>
            <td>${this.escape(product.category || '-')}</td>
            <td>${this.escape(price)}</td>
            <td>${this.escape(product.availability || '-')}</td>
            <td><a href="${this.escapeAttr(product.url || '#')}" target="_blank" rel="noopener noreferrer" class="z-icon-btn" title="Abrir"><i class="fas fa-arrow-up-right-from-square"></i></a></td>
        </tr>`;
    },

    setLoading(isLoading) {
        this.submitButton.disabled = isLoading;
        this.submitButton.innerHTML = isLoading
            ? '<i class="fas fa-spinner fa-spin"></i><span>Escaneando</span>'
            : '<i class="fas fa-magnifying-glass"></i><span>Escanear</span>';
        if (isLoading) {
            this.status.className = 'z-badge z-badge--off';
            this.status.innerHTML = '<span class="z-badge__dot"></span>Escaneando';
            this.summary.textContent = 'Procesando URL';
        }
    },

    copyJson() {
        if (!this.result) return;
        navigator.clipboard.writeText(JSON.stringify(this.result, null, 2));
    },

    escape(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    },

    escapeAttr(value) {
        return this.escape(value).replace(/`/g, '&#096;');
    },
};

document.addEventListener('DOMContentLoaded', () => scraperScan.init());
