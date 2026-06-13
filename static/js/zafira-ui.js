        function zafira_alert(message, title = 'Aviso', icon = 'error') {
            if (!window.Swal) {
                alert(message);
                return Promise.resolve();
            }
            return Swal.fire({
                title,
                text: message,
                icon,
                customClass: { popup: 'z-swal' },
                confirmButtonText: 'Entendido',
            });
        }

        function zafira_set_button_loading(button, loading, label = 'Guardando...') {
            if (!button) return;
            if (loading) {
                button.dataset.originalHtml = button.innerHTML;
                button.disabled = true;
                button.innerHTML = `<i class="fas fa-spinner fa-spin"></i><span>${label}</span>`;
                return;
            }
            button.disabled = false;
            if (button.dataset.originalHtml) button.innerHTML = button.dataset.originalHtml;
        }

        function zafira_confirm(title, message) {
            if (!window.Swal) {
                return Promise.resolve(confirm(`${title}\n\n${message}`));
            }
            return Swal.fire({
                title,
                text: message,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Confirmar',
                cancelButtonText: 'Cancelar',
                reverseButtons: true,
                customClass: { popup: 'z-swal' },
            }).then(result => result.isConfirmed);
        }

        async function submit_with_ajax(title, message, url, params, onSuccess) {
            const confirmed = await zafira_confirm(title, message);
            if (!confirmed) return;
            const formData = new FormData();
            Object.entries(params).forEach(([k, v]) => formData.append(k, v));
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrftoken },
                    body: formData,
                });
                const data = await response.json();
                if (data.error) zafira_alert(data.error);
                else if (onSuccess) onSuccess(data);
            } catch (error) {
                zafira_alert('No se pudo completar la acción. Inténtalo nuevamente.');
            }
        }

        async function submit_formdata_with_ajax_form(target) {
            const form = target.tagName === 'FORM' ? target : target.form;
            const submitButton = form.querySelector('[type="submit"]');
            zafira_set_button_loading(submitButton, true);
            const formData = new FormData(form);
            formData.append('action', form.dataset.action || 'add');
            try {
                const response = await fetch(form.action || pathname, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrftoken },
                    body: formData,
                });
                const data = await response.json();
                if (data.error) {
                    await zafira_alert(data.error);
                    zafira_set_button_loading(submitButton, false);
                    return;
                }
                window.location.href = form.dataset.success || pathname.replace(/(create|update\/\d+)\/?$/, '');
            } catch (error) {
                await zafira_alert('No se pudo completar la acción. Inténtalo nuevamente.');
                zafira_set_button_loading(submitButton, false);
            }
        }

        // ──────────────────────────────────────────────────────────────
        // Zafira UI Kit
        // ──────────────────────────────────────────────────────────────
        window.Zafira = {
            escape(value) {
                const map = {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#039;',
                };
                return String(value ?? '').replace(/[&<>"']/g, m => map[m]);
            },

            statusBadge(active, labels = ['Activo', 'Inactivo']) {
                const cls = active ? 'z-badge--on' : 'z-badge--off';
                const label = active ? labels[0] : labels[1];
                return `<button rel="toggle_btn" class="z-badge ${cls}">
                    <span class="z-badge__dot"></span>${label}
                </button>`;
            },

            rowActions(id, basePath = pathname, extras = []) {
                const buttons = extras.map(a => {
                    const cls = a.danger ? 'z-icon-btn z-icon-btn--danger' : 'z-icon-btn';
                    return `<a href="${a.href}" class="${cls}" title="${a.title}"><i class="${a.icon}"></i></a>`;
                }).join('');
                return `<div class="z-row-actions">${buttons}
                    <a href="${basePath}update/${id}/" class="z-icon-btn" title="Editar"><i class="fas fa-pen"></i></a>
                    <a href="${basePath}delete/${id}/" class="z-icon-btn z-icon-btn--danger" title="Eliminar"><i class="fas fa-trash"></i></a>
                </div>`;
            },

            dataTable(selector, columns, options = {}) {
                const opts = Object.assign({
                    url: pathname,
                    toggleField: 'is_active',
                    toggleConfirm: '¿Cambiar el estado de este registro?',
                    pageSize: 10,
                    defaultOrder: [],
                }, options);

                const skelRow = `<div class="z-skel__row">${'<span class="z-skel__bar"></span>'.repeat(columns.length)}</div>`;
                const skeletonHTML = `<div class="z-skel" style="--z-cols:${columns.length}" aria-hidden="true">${skelRow.repeat(Math.min(opts.pageSize, 6))}</div>`;

                const $tbl = $(selector);
                $.fn.dataTable.ext.errMode = 'none';
                const tbl = $tbl.DataTable({
                    dom: 'rt<"z-table-footer"<"z-table-info"i><"z-table-pager"p>>',
                    destroy: true, processing: true, serverSide: true,
                    pageLength: opts.pageSize,
                    order: opts.defaultOrder,
                    language: {
                        processing: skeletonHTML,
                        zeroRecords: 'Sin resultados',
                        emptyTable: '<i class="fas fa-inbox text-3xl mb-2 block opacity-40"></i><div>No hay registros para mostrar</div>',
                        info: 'Mostrando _START_ a _END_ de _TOTAL_',
                        infoEmpty: '0 registros',
                        infoFiltered: '(filtrado de _MAX_ total)',
                        paginate: {
                            first: '<i class="fas fa-angle-double-left"></i>',
                            previous: '<i class="fas fa-angle-left"></i>',
                            next: '<i class="fas fa-angle-right"></i>',
                            last: '<i class="fas fa-angle-double-right"></i>',
                        },
                    },
                    ajax: {
                        url: opts.url, type: 'POST', headers: { 'X-CSRFToken': csrftoken },
                        data: function (d) {
                            d.action = 'search';
                            d.page = d.start / d.length + 1;
                            d.page_size = d.length;
                            d.search.value = $tbl.data('searchValue') || '';
                        },
                        dataSrc: function (json) {
                            if (json.error) {
                                zafira_alert(json.error);
                                return [];
                            }
                            return json.data || [];
                        },
                        error: function () {
                            zafira_alert('No se pudo cargar la información de la tabla.');
                        },
                    },
                    columns: columns,
                });

                const $scroll = $tbl.closest('.overflow-x-auto');
                tbl.on('processing.dt', function (e, settings, processing) {
                    if (processing && $scroll.length) {
                        $scroll[0].style.setProperty('--z-skel-top', ($tbl.find('thead').outerHeight() || 0) + 'px');
                    }
                    $scroll.toggleClass('z-loading', processing).attr('aria-busy', processing ? 'true' : 'false');
                });

                const $searchInput = $(`[data-table-search="${selector}"]`);
                if ($searchInput.length) {
                    let debounce;
                    $searchInput.on('input', function () {
                        clearTimeout(debounce);
                        const val = this.value;
                        debounce = setTimeout(() => {
                            $tbl.data('searchValue', val);
                            tbl.ajax.reload();
                        }, 280);
                    });
                }

                $(`[data-table-refresh="${selector}"]`).on('click', () => tbl.ajax.reload(null, false));

                if (opts.toggleField) {
                    $tbl.find('tbody').off('click.zafira').on('click.zafira', 'button[rel="toggle_btn"]', function () {
                        const row = tbl.row($(this).closest('tr')).data();
                        if (!row) return;
                        submit_with_ajax('Confirmar', opts.toggleConfirm, opts.url,
                            { id: row.id, action: 'change_state' },
                            () => tbl.ajax.reload(null, false));
                    });
                }

                return tbl;
            },

            /**
             * Auto-bind para dropdowns reutilizables.
             * Marca el contenedor con `data-dropdown` y dentro:
             *   - [data-dropdown-trigger] → click para abrir/cerrar
             *   - [data-dropdown-menu]     → contenido (con clases .z-dropdown__*)
             */
            initDropdowns(root = document) {
                root.querySelectorAll('[data-dropdown]:not([data-z-ready])').forEach(dd => {
                    dd.setAttribute('data-z-ready', '1');
                    const trigger = dd.querySelector('[data-dropdown-trigger]');
                    if (!trigger) return;
                    trigger.addEventListener('click', e => {
                        e.stopPropagation();
                        document.querySelectorAll('[data-dropdown].is-open').forEach(o => {
                            if (o !== dd) o.classList.remove('is-open');
                        });
                        dd.classList.toggle('is-open');
                    });
                });
            },
        };

        Zafira.toggleTheme = function () {
            const root = document.documentElement;
            const meta = document.querySelector('meta[name="color-scheme"]');
            const isDark = root.classList.toggle('dark');
            localStorage.setItem('zafira-theme', isDark ? 'dark' : 'light');
            if (meta) meta.content = isDark ? 'dark' : 'light';
        };

        document.addEventListener('click', e => {
            if (e.target.closest('[data-toggle-theme]')) Zafira.toggleTheme();
        });

        document.addEventListener('DOMContentLoaded', () => Zafira.initDropdowns());
        document.addEventListener('click', e => {
            if (!e.target.closest('[data-dropdown]')) {
                document.querySelectorAll('[data-dropdown].is-open').forEach(o => o.classList.remove('is-open'));
            }
        });

        // Sidebar group collapse
        document.addEventListener('click', e => {
            const header = e.target.closest('[data-group-toggle]');
            if (header) {
                const group = header.closest('.z-group');
                group.dataset.open = group.dataset.open === 'true' ? 'false' : 'true';
            }
        });

        // Mobile sidebar toggle
        document.addEventListener('click', e => {
            if (e.target.closest('[data-toggle-sidebar]')) {
                document.getElementById('z-sidebar').classList.toggle('is-open');
                document.getElementById('z-shell').classList.toggle('is-overlay');
            } else if (e.target.closest('.z-shell.is-overlay') && !e.target.closest('.z-sidebar')) {
                document.getElementById('z-sidebar').classList.remove('is-open');
                document.getElementById('z-shell').classList.remove('is-overlay');
            }
        });

        // Colapsar / expandir el menú lateral (escritorio) — persistente
        document.addEventListener('click', e => {
            const btn = e.target.closest('[data-toggle-collapse]');
            if (!btn) return;
            const collapsed = document.documentElement.classList.toggle('sidebar-collapsed');
            btn.title = collapsed ? 'Expandir menú' : 'Contraer menú';
            try { localStorage.setItem('zafira-sidebar-collapsed', collapsed ? '1' : '0'); } catch (e) {}
        });
        document.addEventListener('DOMContentLoaded', () => {
            const btn = document.querySelector('[data-toggle-collapse]');
            if (btn && document.documentElement.classList.contains('sidebar-collapsed'))
                btn.title = 'Expandir menú';
        });
